import argparse
import logging
import threading
import signal
import sys
import time
import queue
from collections import deque

import numpy as np
import mido
from pylsl import resolve_streams, StreamInlet
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
        self.outport.send(mido.Message("note_on", note=int(note), velocity=int(velocity)))

    def note_off(self, note):
        self.outport.send(mido.Message("note_off", note=int(note)))


# -----------------------------------------------------
# Respiration low-pass filter
# -----------------------------------------------------
class RespFilter:
    """Simple real-time low-pass filter for smoothing respiration amplitude."""

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
    def __init__(self, queue, buffer_len=20000, ymin=-2, ymax=2):
        self.queue = queue
        self.buffer = deque(maxlen=buffer_len)

        self.app = QtWidgets.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(title="RESP Visualiser")
        self.win.resize(900, 300)
        self.win.show()

        self.plot = self.win.addPlot(title="Live Respiration -> MIDI Notes")
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
            value = self.queue.get_nowait()
            self.buffer.append(value)
        if self.buffer:
            self.curve.setData(np.array(self.buffer))

    def start(self):
        self.app.exec_()


# -----------------------------------------------------
# Map respiration amplitude → MIDI note number
# -----------------------------------------------------
def map_amp_to_note(x, xmin, xmax, note_min=40, note_max=80):
    # Linearly map RESP amplitude (V) to note range
    # MIDI 40 (min) = E2
    # MIDI 80 (max) = G#5
    if xmax <= xmin:
        return note_min
    frac = (x - xmin) / (xmax - xmin)
    frac = np.clip(frac, 0.0, 1.0)
    note = note_min + frac * (note_max - note_min)
    return int(round(note))


# ---------------- Ctrl+C safe stop ----------------
stop_flag = threading.Event()

def signal_handler(sig, frame):
    logging.info("Ctrl+C detected. Stopping...")
    stop_flag.set()                  # Inform threads to stop
    QtWidgets.QApplication.quit()    # Close PyQt GUI
    sys.exit(0)                      # Exit script

signal.signal(signal.SIGINT, signal_handler)


# -----------------------------------------------------
# Worker thread
# -----------------------------------------------------
def bridge_worker(args, vis_queue):

    # Calibration window to calculate min and max respiration amplitude
    # Tell PP to inhale and exhale fully over the 30-second period - MIDI output will NOT play during this time
    calibration_duration = 30.0  # seconds
    start_time = time.time()
    calibrating = True

    logging.info("Resolving OpenSignals LSL streams...")
    streams = [s for s in resolve_streams() if "OpenSignals" in (s.name() or "")]
    if not streams:
        logging.error("No OpenSignals streams found.")
        return

    info = streams[min(args.stream_index, len(streams)-1)]
    inlet = StreamInlet(info, max_chunklen=32)

    fs = info.nominal_srate() or 100.0
    logging.info(f"Using stream '{info.name()}', fs={fs:.1f} Hz, channel={args.channel}")

    filt = RespFilter(fs, cutoff=args.cutoff)
    midi = MidiOut(args.midi_port)

    amp_min = None
    amp_max = None
    prev_note = None
    calibration_msg_shown = False

    try:
        while True:
            sample, _ = inlet.pull_sample(timeout=0.0)
            if sample is None:
                time.sleep(0.001)
                continue

            raw = float(sample[args.channel])
            filtered = filt.add(raw)

            now = time.time()

            if calibrating:
                if not calibration_msg_shown:
                    logging.info(
                        f"PLEASE WAIT: Calibrating amplitude range of RESP signal ({calibration_duration:.0f}s)..."
                    )
                    calibration_msg_shown = True

                if amp_min is None:
                    amp_min = filtered
                    amp_max = filtered
                else:
                    amp_min = min(amp_min, filtered)
                    amp_max = max(amp_max, filtered)

                if now - start_time >= calibration_duration:
                    calibrating = False
                    prev_note = None
                    logging.info(
                        f"Calibration complete: amp_min={amp_min:.3f}, amp_max={amp_max:.3f}"
                    )

            vis_queue.put_nowait(filtered)

            if not calibrating:
                note = map_amp_to_note(
                    filtered, amp_min, amp_max,
                    note_min=args.note_low,
                    note_max=args.note_high
                )
                if prev_note is None:
                    prev_note = note
                    midi.note_on(note, args.velocity)
                elif note != prev_note:
                    midi.note_off(prev_note)
                    midi.note_on(note, args.velocity)
                    prev_note = note

    except KeyboardInterrupt:
        logging.info("Stopping respiration bridge...")


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