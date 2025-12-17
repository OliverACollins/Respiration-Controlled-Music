import argparse
import logging
import threading
import sys
import time
import queue
from collections import deque

import numpy as np
import mido
from scipy.signal import butter, lfilter, lfilter_zi

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg


# -----------------------------------------------------
# MIDI output handler
# -----------------------------------------------------
class MidiOut:
    def __init__(self, port_name):
        try:
            self.outport = mido.open_output(port_name)
        except IOError as e:
            raise RuntimeError(
                f"Could not open MIDI port '{port_name}'. "
                f"Available ports: {mido.get_output_names()}"
            ) from e

    def note_on(self, note, velocity):
        self.outport.send(
            mido.Message("note_on", note=int(note), velocity=int(velocity))
        )

    def note_off(self, note):
        self.outport.send(
            mido.Message("note_off", note=int(note))
        )


# -----------------------------------------------------
# Respiration low-pass filter
# -----------------------------------------------------
class RespFilter:
    def __init__(self, fs, cutoff=1.0):
        nyq = 0.5 * fs
        norm = cutoff / nyq
        self.b, self.a = butter(2, norm, btype="low")
        zi = lfilter_zi(self.b, self.a)
        self.z = zi * 0.0

    def add(self, x):
        y, self.z = lfilter(self.b, self.a, [x], zi=self.z)
        return float(y[0])


# -----------------------------------------------------
# Respiration visualiser
# -----------------------------------------------------
class RespVisualiser:
    def __init__(self, queue, buffer_len=20000, ymin=-1, ymax=1): # smaller y-axis than live as prerecorded signal has smaller amp range
        self.queue = queue
        self.buffer = deque(maxlen=buffer_len)

        self.app = QtWidgets.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(title="RESP Visualiser")
        self.win.resize(900, 300)
        self.win.show()

        self.plot = self.win.addPlot(title="Prerecorded Respiration -> MIDI Notes")
        self.curve = self.plot.plot(pen='c')

        self.plot.setYRange(ymin, ymax)
        self.plot.disableAutoRange(axis='y')
        self.plot.setLabel('left', 'Amplitude (V)')
        self.plot.setLabel('bottom', 'Samples')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20)

    def update(self):
        while not self.queue.empty():
            self.buffer.append(self.queue.get_nowait())
        if self.buffer:
            self.curve.setData(np.array(self.buffer))

    def start(self):
        self.app.exec_()


# -----------------------------------------------------
# Map respiration amplitude → MIDI note
# -----------------------------------------------------
def map_amp_to_note(x, xmin, xmax, note_min=40, note_max=80):
    if xmax <= xmin:
        return note_min
    frac = (x - xmin) / (xmax - xmin)
    frac = np.clip(frac, 0.0, 1.0)
    return int(round(note_min + frac * (note_max - note_min)))


# -----------------------------------------------------
# Worker thread (global calibration)
# -----------------------------------------------------
def bridge_worker(args, vis_queue):
    logging.info(f"Loading prerecorded respiration from '{args.input_file}'...")
    data = np.loadtxt(args.input_file, delimiter=',', skiprows=1)

    fs = args.sampling_rate
    dt = 1.0 / fs

    filt = RespFilter(fs, cutoff=args.cutoff)
    midi = MidiOut(args.midi_port)

    # ---- GLOBAL CALIBRATION ----
    logging.info("PLEASE WAIT: Calibrating amplitude range of RESP signal...")
    filtered_data = np.array([filt.add(float(x)) for x in data])
    amp_min = float(np.min(filtered_data))
    amp_max = float(np.max(filtered_data))

    logging.info(
        f"Calibration complete: amp_min={amp_min:.3f}, amp_max={amp_max:.3f}"
    )

    prev_note = None

    # ---- PLAYBACK ----
    try:
        for filtered in filtered_data:
            vis_queue.put_nowait(filtered)

            note = map_amp_to_note(
                filtered,
                amp_min,
                amp_max,
                note_min=args.note_low,
                note_max=args.note_high
            )

            if prev_note is None:
                midi.note_on(note, args.velocity)
                prev_note = note
            elif note != prev_note:
                midi.note_off(prev_note)
                midi.note_on(note, args.velocity)
                prev_note = note

            time.sleep(dt)

    except KeyboardInterrupt:
        logging.info("Stopping MIDI playback...")


# -----------------------------------------------------
# Main
# -----------------------------------------------------
def main(args):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s")
    vis_queue = queue.Queue(maxsize=2000)
    vis = RespVisualiser(vis_queue)
    threading.Thread(target=bridge_worker, args=(args, vis_queue), daemon=True,).start()
    vis.start()

if __name__ == "__main__":
    main()