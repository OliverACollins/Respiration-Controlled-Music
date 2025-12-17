# src/resp_midi/cli.py
import argparse

from resp_music import (
    resp_live_play,
    resp_live_mod,
    resp_prerec_play,
    resp_prerec_mod,
)


def main():
    parser = argparse.ArgumentParser(
        prog="resp-music",
        description="Respiration-controlled MIDI system",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help = False
    )

    parser.add_argument(
    "--help",
    action="help",
    help="Help for CLI"
)
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- live-play ----
    live_play = subparsers.add_parser(
        "live-play",
        help="Play MIDI from live respiration data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help = False
    )

    live_play.add_argument("--help", action="help", help="")
    live_play.add_argument("--midi-port", default="HCI 1", metavar="", help="loopMIDI port name")
    live_play.add_argument("--note-low", type=int, default=40, metavar="", help="Lowest MIDI note")
    live_play.add_argument("--note-high", type=int, default=80, metavar="", help="Highest MIDI note")
    live_play.add_argument("--velocity", type=int, default=100, metavar="", help="MIDI note velocity")
    live_play.add_argument("--cutoff", type=float, default=1.0, metavar="", help="Low-pass filter Hz cutoff")
    live_play.add_argument("--channel", type=int, default=1, metavar="", help="OpenSignals channel")
    live_play.add_argument("--stream-index", type=int, default=0, metavar="", help="OpenSignals stream index")
    live_play.set_defaults(func=resp_live_play.main)


    # ---- live-mod ----
    live_mod = subparsers.add_parser(
        "live-mod",
        help="Modulate MIDI from live respiration data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help = False
    )

    live_mod.add_argument("--help", action="help", help="")
    live_mod.add_argument("--midi-port", default="HCI 1", metavar="", help="loopMIDI port name")
    live_mod.add_argument("--cc", type=int, default=115, metavar="", help="MIDI CC mapping")
    live_mod.add_argument("--channel-midi", type=int, default=0, metavar="", help="MIDI channel (0-15)")
    live_mod.add_argument("--cutoff", type=float, default=1.0, metavar="", help="Low-pass filter Hz cutoff")
    live_mod.add_argument("--channel", type=int, default=1, metavar="", help="OpenSignals channel")
    live_mod.add_argument("--stream-index", type=int, default=0, metavar="", help="OpenSignals stream index")
    live_mod.set_defaults(func=resp_live_mod.main)


    # ---- prerec-play ----
    prerec_play = subparsers.add_parser(
        "prerec-play",
        help="Play MIDI from prerecorded respiration data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help = False
    )

    prerec_play.add_argument("--help", action="help", help="")
    prerec_play.add_argument("--input-file", default=r"src\resp_music\simulate\resp_simulate_15.csv", metavar="", help="Prerecorded CSV respiration data (15 breaths/minute)")
    prerec_play.add_argument("--sampling-rate", type=float, default=1000.0, metavar="", help="Sampling rate of simulated RESP signal")
    prerec_play.add_argument("--midi-port", default="HCI 1", metavar="", help="loopMIDI port name")
    prerec_play.add_argument("--note-low", type=int, default=40, metavar="", help="Lowest MIDI note")
    prerec_play.add_argument("--note-high", type=int, default=80, metavar="", help="Highest MIDI note")
    prerec_play.add_argument("--velocity", type=int, default=100, metavar="", help="MIDI note velocity")
    prerec_play.add_argument("--cutoff", type=float, default=1.0, metavar="", help="Low-pass filter Hz cutoff")
    prerec_play.set_defaults(func=resp_prerec_play.main)


    # ---- prerec-mod ----
    prerec_mod = subparsers.add_parser(
        "prerec-mod",
        help="Modulate MIDI from prerecorded respiration data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help = False
    )

    prerec_mod.add_argument("--help", action="help", help="")
    prerec_mod.add_argument("--input-file", default=r"src\resp_music\simulate\resp_simulate_15.csv", metavar="", help="Prerecorded CSV respiration data (15 breaths/minute)")
    prerec_mod.add_argument("--sampling-rate", type=float, default=1000.0, metavar="", help="Sampling rate of simulated RESP signal")
    prerec_mod.add_argument("--midi-port", default="HCI 1", metavar="", help="loopMIDI port name")
    prerec_mod.add_argument("--cc", type=int, default=115, metavar="", help="MIDI CC mapping")
    prerec_mod.add_argument("--channel-midi", type=int, default=0, metavar="", help="MIDI channel (0-15)")
    prerec_mod.add_argument("--cutoff", type=float, default=1.0, metavar="", help="Low-pass filter Hz cutoff")
    prerec_mod.set_defaults(func=resp_prerec_mod.main)


    args = parser.parse_args()
    args.func(args)