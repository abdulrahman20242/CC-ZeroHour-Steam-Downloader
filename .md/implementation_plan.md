# Implementation Plan: Refactoring Launchers and Scripts

## Goal Description
The user requested two main improvements to the standalone downloader setup:
1. Rename [Sortify.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/download%20Command%20&%20Conquer%20Generals%20Zero%20Hour/Sortify.bat) to a more appropriate and descriptive name for the project.
2. Fix the broken [2732960.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/2732960.bat) file by converting its logic to run via Python (similar to [depot_gui.py](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/depot_gui.py)), rather than hardcoding complex bash commands that fail.

## Proposed Changes

### 1. Renaming [Sortify.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/download%20Command%20&%20Conquer%20Generals%20Zero%20Hour/Sortify.bat)
I will rename [Sortify.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/download%20Command%20&%20Conquer%20Generals%20Zero%20Hour/Sortify.bat) to **`Launch_GUI.bat`** (or `Launch_ZeroHour_GUI.bat`). This makes its purpose immediately obvious to any user.

### 2. Converting [2732960.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/2732960.bat) logic to Python (`depot_cli.py`)
Currently, [2732960.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/2732960.bat) uses hardcoded terminal commands that are failing or unwieldy.
I will create a new Python script:
#### [NEW] `depot_cli.py`
This script will be a streamlined, terminal-only version of [depot_gui.py](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/depot_gui.py). 
- It will read [games_config.json](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/games_config.json).
- It will automatically iterate through the default/selected depots (Base Game, English Language, and DirectX) just like the GUI does, but without opening a window.
- It will execute the [DepotDownloaderMod.exe](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/DepotDownloaderMod.exe) commands sequentially and stream the output to the terminal.

#### [MODIFY] [2732960.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/2732960.bat)
I will rewrite [2732960.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/2732960.bat) to simply be a launcher for the new CLI script:
```bat
@echo off
cd /d "%~dp0"
echo Starting Command & Conquer Zero Hour Automated Download...
python depot_cli.py
pause
```

#### [MODIFY] [README.md](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/README.md)
I will update the [README.md](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/README.md) documentation to reflect the new file names (`Launch_GUI.bat` instead of [Sortify.bat](file:///f:/FFOutput/New%20folder/New%20folder%20%282%29/DepotDownloader0/DepotDownloader/download%20Command%20&%20Conquer%20Generals%20Zero%20Hour/Sortify.bat), and explain the new Python terminal logic).

## User Review Required
> [!IMPORTANT]
> Please review the proposed new names (`Launch_GUI.bat` and `depot_cli.py`). Let me know if you prefer different names before I proceed with the modifications!
