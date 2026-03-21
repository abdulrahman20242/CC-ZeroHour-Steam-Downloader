# PRD for AI: Create a Standalone Game Downloader (DepotDownloaderMod)

## 📌 Objective / الهدف
The objective of this task is to create a complete, isolated, and standalone download directory for a specific Steam game using `DepotDownloaderMod`. The AI must extract the necessary keys and manifests, copy all required executables and DLLs, and configure the tools so the user can download the game with a single click.

---

## 📋 Required Information (User provides this)
- **Game Name:** [اكتب اسم اللعبة هنا]
- **App ID:** [اكتب رقم اللعبة App ID هنا]
- **Source of Keys/Manifests:** (e.g., `[AppID].lua` or `ALL depotkeys.json`)

---

## 🛠️ Step-by-Step Instructions for the AI

### Step 1: Identify Dependencies and Requirements
The AI must locate the following files for the specified `App ID`:
1. The Depot IDs associated with the game.
2. The Manifest IDs for each Depot.
3. The Decryption Keys (Hex Keys) for each Depot.
*(These are usually found in the `[App ID].lua` file provided by SteamTools or inside `ALL depotkeys.json`)*.

### Step 2: Set up the Isolated Directory
1. Create a new directory named: `download [Game Name]` inside the main `DepotDownloader` folder.
2. Copy the core executables and required DLLs to this new folder. Specifically:
   - `DepotDownloaderMod.exe`
   - `DepotDownloaderMod.dll`
   - `SteamKit2.dll`
   - `QRCoder.dll`
   - `System.IO.Hashing.dll`
   - `ZstdSharp.dll`
   - `protobuf-net.dll`
   - `protobuf-net.Core.dll`
   - `DepotDownloaderMod.deps.json`
   - `DepotDownloaderMod.runtimeconfig.json`

### Step 3: Copy UI & Helper Scripts (Optional but Recommended)
Copy the following files to the new folder:
- `depot_gui.py`
- `ALL depotkeys.json`
- `download manifest api.txt`
- Any `Sortify.bat` or `.bat` launchers designed for the root.

### Step 4: Game-Specific File Generation
1. **Manifests:** Ensure all `.manifest` files belonging to the game's depots (including shared depot `228990` if required) are copied to the new folder.
2. **Keys File (`[App ID].key`):** Create a text file named `[App ID].key`. Each line MUST be formatted as `DepotID;HexKey`.
3. **Download Script (`[App ID].bat`):** Create a `.bat` file with a download command for **each** depot. Format:
   `DepotDownloaderMod.exe -app [App ID] -depot [Depot ID] -manifest [Manifest ID] -manifestfile [Manifest_File_Name.manifest] -depotkeys [App ID].key -max-downloads 256 -verify-all`
4. **Games Config (`games_config.json`):** Generate a `games_config.json` in the new folder containing the exact JSON structure required by `depot_gui.py`, mapping the new `App ID`, its depots, and the `[App ID].key` file.

### Step 5: Final Review
The AI must verify that the new isolated folder contains roughly ~28-30 files (including the 8 essential executable DLL/EXE files, the configuration JSON, the keys file, the `.bat` executing script, and all `.manifest` files).

---
**💡 Message to AI:** Once you finish generating this folder, confirm to the user that all files have been placed properly and that they just need to run `[App ID].bat` or `depot_gui.py` to start downloading.
