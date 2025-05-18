# Marvel Heroes Toolkit

A custom GUI tool for converting, importing, and managing account data from Marvel Heroes into an SQLite database format.

## Features

- Import JSON account exports into a `.db` file
- Merge two SQLite account files
- View detailed log output per tab
- Clean, icon-based interface with tab separation
- Support for `CLEAN_Account.db` as a base schema

## Getting Started

### Requirements

- Python 3.9+
- Tkinter (included with most Python installations)
- No external packages required by default

### Running the App

```bash
python marvel_heroes_gui.py
```

The GUI will open with two main tabs:
- **Convert JSON to DB**: Choose a `.json` file and a base `.db` file (like `CLEAN_Account.db`)
- **Merge DB Files**: Combine records from one DB into another

### Building to .EXE (Optional)

If you'd like to generate a standalone `.exe`:

```bash
pyinstaller --noconsole --onefile --icon=marvel_toolkit.ico marvel_heroes_gui.spec
```

Or run the included `build.bat` on Windows if you have PyInstaller installed.

### Sample Files

- `CLEAN_Account.db`: base SQLite structure for import
- `marvel_toolkit.ico`: icon used in the compiled `.exe`

## Notes

- The app includes per-tab log windows.
- Data is not auto-saved — always ensure your target DB is backed up before import/merge.

