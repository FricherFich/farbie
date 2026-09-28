# FARBIE

This project converts lighting/chase descriptions stored as plain text into Ableton Live clip data and imports them into a template `.als` project.

## What it does

The workflow is:

- Reads a fixture script file such as `Spot1:0#000000;1#FFFFFF;...`
- Parses the beat-based RGB, velocity and direction values
- Maps fixture names to DMX channels and Ableton automation targets
- Builds XML envelope data for each channel
- Appends the generated clip and scene to a base Ableton Live project
- Saves a new timestamped `.als` file and moves the processed text file into an imported folder

This is mainly useful for building lighting cues from text definition files and turning them into Ableton clips automatically.

## Main files

- `main_import_all_anids_as_clip.py` – batch importer entry point
- `append_as_clip_to_file.py` – entry point for inserting one fixture definition into an Ableton project
- `parse_fixture_idea.py` – converts text scripts into structured channel data
- `append_to_clip_slots.py` – appends a new clip into the Ableton XML structure
- `dmx_channel_mapping.py` – DMX fixture/channel lookup
- `prepare_envelope_xml.py` – creates envelope XML for automation
- `als_xml_conversion.py` – unzips/rezips `.als` files to/from XML
- `constants.py` – path to the base `.als` template used for DMX channel lookup
- `frontend/preview.py` – local visual preview of the script before importing

## Prerequisites

This project was verified with Python 3.12. Python 3.14 caused compatibility issues with the preview dependency stack, so use Python 3.12 for best results.

### Install Python 3.12

Windows:

- Download the Python 3.12 installer from python.org or install via winget:

```powershell
winget install --id Python.Python.3.12 -e
```

- In VS Code, select the Python 3.12 interpreter via the Command Palette: `Python: Select Interpreter`

### Install required packages

From a terminal with the selected Python 3.12 interpreter:

```powershell
python -m pip install --upgrade pip
python -m pip install pygame
```

If the `py` launcher is available, this is equivalent:

```powershell
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install pygame
```

### Verify the setup

```powershell
python --version
python -c "import pygame; print(pygame.__version__)"
```

You should see Python 3.12.x and the installed `pygame` version.

## How to use it

### 1) Prepare source files

Place your text fixture files in a folder named `effects` in the project root.

Example format:

```text
Spot1:0#000000;2#FF00AA;4#000000
Tube01:0#FFFFFF;4#000000
Laser1:0#000000;2#R;4#L
```

- RGB fixture entries use `beat#RRGGBB`
- Direction entries use values like `R`, `0`, or `L`
- Velocity is mapped through the laser channels

### 2) Run the batch importer

From the project folder:

```bash
python main_import_all_anids_as_clip.py
```

What happens:

- Finds the newest `.als` file in the `output` folder
- Copies it to a temporary working file
- Imports every text script from `effects`
- Moves each processed file to `imported`
- Saves a new timestamped `.als` file in the current directory

### 3) Preview a script visually

You can also preview a fixture script before importing it:

```bash
python frontend/preview.py path/to/your_fixture_file.txt
```

If no file is passed, the script falls back to a built-in demo sequence.

## Requirements

- Python 3
- `pygame` for the preview UI

Install it with:

```bash
pip install pygame
```

## Notes

- The project expects a base Ableton Live template and an up-to-date DMX fixture mapping.
- The generated output uses the template project as a starting point, so the `.als` file should be kept valid and editable in Ableton.
- The importer is designed for a project-specific setup, so you may need to adjust folder names and fixture mapping if you reuse it in a different environment.
