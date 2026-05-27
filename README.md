# GUI Threshold Estimation

This is a GUI version of Threshold Estimation originally written by Gudrun Schappacher-Tilp.
For more information see original repository: <https://github.com/schappag/threshold_estimation>
The goal is to make a user-friendly version, that requires no installation of Python and other packages is needed.

## How to Use

The program is a single portable exe-file located in the `dist/` folder.
After running the program you see this window:

<img src="/screenshot/screenshot_1.png" width="500">

- **Select File**: Select your data, which should be stored as csv-file.

To convert data from xlsx to csv (NIRS, Spiro), see <https://github.com/felix-feistritzer/xlsx-to-csv>

- Optional you can add labels for the plot.

- **Plot**: Runs the calculation and plots the result. This can, depending on the amount of data, take some time. Please be patient :)

- **Save Plot**: Save the generated plot as png-file.

## Requirements

- Python
- Python packages
    - numpy
    - pandas
    - scipy
    - matplotlib
    - tkinter
 
## Building the file

If you want to rebuild the program (e.g. for another system, making modifications, etc.), here are the instructions, how to build it yourself.

For building the exe-file, pyinstaller was used.
See the PyInstaller documentation: <https://pyinstaller.org/en/stable/>

To build the program into a single file, the following command was used:

```
pyinstaller -F --clean --noconsole gui.py
```

`pyinstaller` The main command-line tool for PyInstaller, which packages Python applications into standalone executables.

`-F` Bundles everything into a single executable file.

`--clean` Cleans (removes) any temporary files or caches from previous builds before starting.

`--noconsole` Prevents a console window from appearing when the executable runs. Useful for GUI applications.

`gui.py` The python script.

### Output

The executable will be placed in the `dist/` folder within your project directory.

## Possible Problems

A possible problem under Windows 11 is, that the Smart App Control will block the app.

This is because under Windows 11 files need to be signed. I haven’t done this yet.

When starting the program, you may see the following message: _Smart App Control blocked an app that may be unsafe_

Windows Smart App Control must be disabled to run this app.

To disable Smart App Control, go to:

Settings -> Privacy & security -> App & browser control -> Smart App Control settings

and select _Off_

After that the program should start.
