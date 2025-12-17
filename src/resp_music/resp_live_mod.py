import argparse
import logging
import threading
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

    def send_cc(self, cc, value, channel=0):
        """Send a MIDI CC message (0-127)."""
        self.outport.send(mido.Message("control_change",
                                       control=int(cc),
                                       value=int(value),
                                       channel=channel))


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

        self.plot = self.win.addPlot(title="Live Respiration -> MIDI CC")
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
# Map respiration amplitude → MIDI CC value
# -----------------------------------------------------
def map_amp_to_cc(x, xmin, xmax):
    # Linearly map RESP amplitude (V) to MIDI CC (0-127)
    # MIDI 0 CC = min
    # MIDI 127 CC = max
    if xmax <= xmin:
        return 0
    frac = (x - xmin) / (xmax - xmin)
    frac = np.clip(frac, 0.0, 1.0)
    value = frac * 127
    return int(round(value))


# -----------------------------------------------------
# Worker thread
# -----------------------------------------------------
def bridge_worker(args, vis_queue):

    # Calibration window to calculate min and max respiration amplitude
    # Tell PP to inhale and exhale fully over the 30-second period - MIDI output will NOT play during this time
    calibration_duration = 30.0  # seconds
    start_time = time.time()
    calibrating = True

    amp_min = None
    amp_max = None
    calibration_msg_shown = False

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

    try:
        while True:
            sample, _ = inlet.pull_sample(timeout=0.0)
            if sample is None:
                continue

            raw = float(sample[args.channel])
            filtered = filt.add(raw)

            vis_queue.put_nowait(filtered)

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
                    logging.info(f"Calibration complete: amp_min={amp_min:.3f}, amp_max={amp_max:.3f}")
            else:
                cc_value = map_amp_to_cc(filtered, amp_min, amp_max)
                midi.send_cc(args.cc, cc_value, channel=args.channel_midi)

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