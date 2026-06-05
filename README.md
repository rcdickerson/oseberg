# The Oseberg Graphics Library
A basic Python graphics library backed by SDL3. Designed for introductory computer science use.

> [!WARNING]
> This library is still in very early stages, use at your own risk!

Named for an early style of Viking art.

## Using the Library

The library is intended to be used by placing the `graphics.py` file in
a project directory and importing it. (The library is targeted for use
in introductory computer science assignments with simple project directory
structures.)

## Requirements

Oseberg uses the [PySDL3 bindings](https://github.com/Aermoss/PySDL3) for the
[SDL3 library](https://wiki.libsdl.org/SDL3/FrontPage). PySDL3 can be installed
within IDEs like Thonny.

You can also create a virtual environment and install PySDL3 that way.

Windows:
``` bash
python3 -m venv .venv
.venv\Scripts\activate
pip install PySDL3
```

Linux / MacOS:
``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install PySDL3
```
