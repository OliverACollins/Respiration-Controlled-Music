# Respiration-Controlled-Music ("resp-music")
**A human-computer interface (HCI) allowing one to create/modulate music using respiration signals, accessible as a Python package.**

## Rationale
The purpose of creating a respiration-music interface was to bring greater bodily awareness towards one's respiratory sensations in a simple manner. It can be suggested that this package *could* provide beneficial applications within psychophysiology research (e.g., relating to mindfulness, interoception)

## About
This Python package enables users to (1) create/modulate music according to their live respiration signals and (2) create/modulate music using a prerecorded respiration simulation (courtesy of the [NeuroKit2](https://neuropsychology.github.io/NeuroKit/functions/rsp.html) package).

This package consists of two scripts for each live and prerecorded respiration-controlled music:
- "live-play": live respiration -> MIDI notes produced by Ableton (pitch of notes determined by RESP signal)
- "live-mod": live respiration -> MIDI CC mapping (the modulation of a musical quality, determined by the user, e.g., chorus, overdrive, reverb)
- "prerec-play": prerecorded respiration -> MIDI notes produced by Ableton
- "prerec-mod": prerecorded respiration -> MIDI CC mapping

Each script has an initial calibration period to calculate one's respiration amplitude (V) range, to determine the scaling of MIDI notes to one's "respiratory capacity". The "live-" scripts have an active 30-second calibration period, where, prototypically, one would aim to perform maximal exhalation and inhalation during this window. The "prerec-" scripts have an indefinite calibration period, where Python examines the amplitude range over the prerecorded CSV data. After the calibration period, the scripts are hard-coded so that the scaling of MIDI notes is determined by the minimum and maximum respiration amplitude calculated during this initial window.

## Pipelines
### For **live** respiration-controlled music
Live respiration signal (streaming through OpenSignals and then to LabRecorder LSL) -> Python bridge for play ("live-play") or modulation ("live-mod") -> loopMIDI -> Ableton Live MIDI output (either playing notes or modulating a musical quality)

### For **prerecorded** respiration-controlled music
Prerecorded respiration signal (simulated using NeuroKit2, encoded into .csv file) -> Python bridge for play ("prerec-play") or modulation ("prerec-mod") -> loopMIDI -> Ableton Live MIDI output (either playing notes or modulating a musical quality)

**This interface has ONLY been tested using Ableton Live 12 for MIDI output within this signal-to-MIDI conversion, so it is unknown whether other MIDI-compatible DAWs would produce the same result as the current pipelines. Ableton was the chosen DAW for this interface due to its flexibility and tractability.**

## Requirements
### Hardware
- WINDOWS PC/Laptop - package incompatible on non-Windows operating systems
- PLUX Biosignals device (e.g., BITalino)
- Respiration belt
- MIDI controller (only necessary for modulation scripts due to MIDI CC mapping, which requires a MIDI controller)

### Software
- VScode (with Python and Jupyter extensions)
- Python >=3.12
- [OpenSignals](https://support.pluxbiosignals.com/knowledge-base/introducing-opensignals-revolution/#download-opensignals) (built for PLUX devices)
- [LabRecorder LSL](https://github.com/labstreaminglayer/App-LabRecorder)
- [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
- Ableton Live

## Roadmap
[x] Live respiration -> MIDI conversion (for both "play" and "modulation")
[x] Prerecorded respiration -> MIDI conversion (for both "play" and "modulation")
[ ] For modulation scripts, add in Key mapping in addition to MIDI CC mapping (so that owning a MIDI controller is not required to run live-mod and prerec-mod)
[ ] Code a cleaner end to MIDI output and data visualiser
[ ] Add a wider variety of prerecorded respiration signals (e.g., different respiration rates, more complex signals)

## Dependencies
Install the following dependencies:
```python
pip install numpy scipy mido python-rtmidi pylsl pyqt5 pyqtgraph
```

## Installation
Install directly from this GitHub repository in Python terminal:

```python
pip install https://github.com/OliverACollins/Respiration-Controlled-Music/zipball/main
```

## Usage
### Setting up loopMIDI port
To facilitate signal-to-MIDI transmission between Python and Ableton, you must install loopMIDI to create a MIDI port. By default, the resp-music scripts are set to run from a port named "HCI 1", but this can be easy adapted through the `--midi-port "PORT_NAME"` CLI argument within the Python terminal.[*] Due to "HCI 1" being the default MIDI port, if you are using a port of a different name, this other port must be specified each time you run the script.

To view the available MIDI ports on your machine, run the following Python code in a new file:

```python
import mido

print("MIDI Input Ports:")
for name in mido.get_input_names():
    print("  ", name)

print("\nMIDI Output Ports:")
for name in mido.get_output_names():
    print("  ", name)
```

### Setting up Ableton Live
Within Ableton, to ensure that the loopMIDI port is correctly set-up, you must do the following:
- Navigate to the "Options" tab and find "Settings"
- In the "Settings" window, go to "Link, Tempo & MIDI". Here, you will find your named loopMIDI port under "Input Ports" and "Output Ports"
- Under "Input Ports", tick "Track" and "Remote" to enable signal-to-MIDI conversion
- After, insert a MIDI track with an Ableton Instrument, ensuring that the track monitor is set to either "Auto" or "In"

If running a modulation script (live-mod or prerec-mod), you must specify your MIDI CC mapping. This can be achieved through clicking the "MIDI" button in the top-right corner of Ableton Live and then using your MIDI controller to select a quality to modulate (which is a very flexible decision)! By default, the MIDI CC mapping is set to "115". To change this default setting according to a different CC mapping in Ableton, use the `--cc "xxx"` CLI argument with your relevant CC number.

### Live respiration-controlled music
To enable live respiration -> MIDI note conversion (playing), run the following command in the Python terminal:

```python
resp-music live-play
```

To enable live respiration -> MIDI CC mapping (modulation), run the following command in the Python terminal:

```python
resp-music live-mod
```

### Prerecorded respiration-controlled music
To enable prerecorded respiration -> MIDI note conversion (playing), run the following command in the Python terminal:

```python
resp-music prerec-play
```

To enable prerecorded respiration -> MIDI CC mapping (modulation), run the following command in the Python terminal:

```python
resp-music prerec-mod
```

### CLI
In the Python terminal, to view all arguments and their defaults for each script, simply add `--help` to the end of each command above. For example...

``` python
resp-music live-play --help
```

Examples of arguments include, but are not limited to:
- `--midi-port`: as discussed above, this argument sets the loopMIDI port name (applies to all four scripts)
- `--cc`: as discussed above, this argument determines the MIDI CC mapping for the live-mod and prerec-mod scripts
- `--note-low`: lowest MIDI note played. This can be changed to allow for a more sensitive respiration-to-music scaling (applies to both live-play and prerec-play)
- `--note-high`: highest MIDI note played. This can be changed to allow for a more sensitive respiration-to-music scaling (applies to both live-play and prerec-play)
- `--input-file`: the prerecorded respiration data (15 breaths/minute) used for both "prerec-" scripts
- `--cutoff`: low-pass filter frequency cutoff applied to respiration signal (applies to all four scripts)

## Troubleshooting
- [*]When specifying your loopMIDI port, it is essential (if applicable) to include the port number after the port name within the CLI argument (e.g., `--midi-port "new_port 2"`)
- If MIDI output is not being produced in Ableton, and steps earlier on in the pipeline have been set up ostensibly correctly, try removing and re-adding your MIDI port within the loopMIDI software

*If any issues occur that are not referenced within this README, please open an [Issue](https://github.com/OliverACollins/Respiration-Controlled-Music/issues) so that any problems highlighted can be addressed*