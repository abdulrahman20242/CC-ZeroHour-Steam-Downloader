# 🎮 CC-ZeroHour-Steam-Downloader

A standalone, fully configured automated tool based on `DepotDownloader` to directly download Steam's Clean Files for **Command & Conquer Generals Zero Hour** (AppID: 2732960) with a Smart UI for language selection.

![Zero Hour](https://steamcdn-a.akamaihd.net/steam/apps/2732960/header.jpg)

## ✨ Features
* **Completely Standalone:** Contains all required `.dll` files, `.exe` engine, and decryption keys out-of-the-box.
* **Smart UI (`depot_gui.py`):** An intuitive Python GUI to intercept and manage your downloads.
* **Save Bandwidth:** The UI automatically pre-checks only the Base Game, DirectX, and English Language Pack while unchecking the other 8 language packs (saving ~8 GB of data).
* **Automated Decryption:** Uses pre-configured `2732960.key` to instantly decrypt the downloaded Steam Depots.

---

## 🚀 How to Use (طريقة الاستخدام)

### Simply click and go (Recommended Method)
This tool strictly uses the Visual Smart GUI to select the depots your require.
1. Ensure you have **Python** installed on your system.
2. Double-click on `Launch_GUI.bat` to launch the Graphical Interface.
3. Click on the game name, and a popup will appear showing all available languages and their exact file sizes.
4. Select your preferred languages (Base game and English are checked by default).
5. Click **"Start Download"**.

---

## 📁 Directory Structure
* `DepotDownloaderMod.exe` : The core download engine.
* `games_config.json` : The configuration file connecting the UI to the game manifests and sizes.
* `2732960.key` : The Hex Decryption keys for all the game's depots.
* `.manifest files` : The version definitions mapped to Steam servers.
* `depot_gui.py` : The Python GUI script.

---

## ⚠️ Disclaimer
This tool uses [DepotDownloader](https://github.com/SteamAutoCracks/DepotDownloaderMod) and the SteamKit2 library. It is designed to act as an automated wrapper for downloading clean files for this specific game. No copyrighted game files are hosted in this repository; it only retrieves files directly from public Steam Content Delivery Networks.
