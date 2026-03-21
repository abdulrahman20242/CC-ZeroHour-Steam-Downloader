from tkinter import ttk
import os
import sys
import json
import threading
import queue
import subprocess
import time
import tkinter as tk
from tkinter import messagebox, filedialog

try:
    import customtkinter as ctk
except ImportError:
    ctk = None
    # Fallback to normal tkinter only UI


class DepotDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_path = os.path.join(self.base_dir, "games_config.json")
        self.config = {}
        self.games = []
        self.current_thread = None
        self.log_queue = queue.Queue()
        self.stop_flag = threading.Event()

        if ctk:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("dark-blue")
            root.title("DepotDownloader Mod GUI")
            root.geometry("900x600")
        else:
            root.title("DepotDownloader Mod GUI")
            root.geometry("900x600")

        self.build_ui()
        self.load_config()
        self.root.after(100, self.process_log_queue)

    def build_ui(self):
        if ctk:
            self.main_frame = ctk.CTkFrame(self.root)
        else:
            self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: games grid
        if ctk:
            self.games_frame = ctk.CTkFrame(self.main_frame)
        else:
            self.games_frame = tk.LabelFrame(self.main_frame, text="Games")
        self.games_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Right: log + progress
        if ctk:
            self.side_frame = ctk.CTkFrame(self.main_frame)
        else:
            self.side_frame = tk.Frame(self.main_frame)
        self.side_frame.pack(side="right", fill="both", expand=False)

        # Progress bar
        if ctk:
            self.progress = ctk.CTkProgressBar(self.side_frame)
            self.progress.set(0)
        else:
            self.progress_var = tk.DoubleVar(value=0.0)
            self.progress = ttk.Progressbar(
                self.side_frame,
                orient="horizontal",
                mode="determinate",
                variable=self.progress_var,
                maximum=100
            )
        self.progress.pack(fill="x", padx=5, pady=(10, 5))

        # Status label
        if ctk:
            self.status_label = ctk.CTkLabel(self.side_frame, text="Idle")
        else:
            self.status_label = tk.Label(self.side_frame, text="Idle")
        self.status_label.pack(fill="x", padx=5)

        # Log text
        if ctk:
            self.log_text = ctk.CTkTextbox(self.side_frame, height=25, width=40)
        else:
            self.log_text = tk.Text(self.side_frame, height=25, width=50)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Bottom buttons
        if ctk:
            self.bottom_frame = ctk.CTkFrame(self.side_frame)
        else:
            self.bottom_frame = tk.Frame(self.side_frame)
        self.bottom_frame.pack(fill="x", padx=5, pady=(0, 5))

        if ctk:
            self.reload_button = ctk.CTkButton(
                self.bottom_frame, text="Reload Config", command=self.reload_config
            )
        else:
            self.reload_button = tk.Button(
                self.bottom_frame, text="Reload Config", command=self.reload_config
            )
        self.reload_button.pack(side="left", padx=(0, 5))

        if ctk:
            self.stop_button = ctk.CTkButton(
                self.bottom_frame, text="Stop", command=self.stop_download
            )
        else:
            self.stop_button = tk.Button(
                self.bottom_frame, text="Stop", command=self.stop_download
            )
        self.stop_button.pack(side="left")

    def load_config(self):
        self.games = []
        for widget in self.games_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.config_path):
            self.log("Config file not found: games_config.json")
            self.log("Creating a template config for you...")
            self.create_default_config()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{e}")
            return

        self.games = self.config.get("games", [])
        if not self.games:
            self.log("No games defined in config.")
            return

        # Build game buttons grid
        cols = 2
        row = 0
        col = 0
        for idx, game in enumerate(self.games):
            name = game.get("name", f"Game {idx+1}")
            if ctk:
                btn = ctk.CTkButton(
                    self.games_frame,
                    text=name,
                    command=lambda g=game: self.start_download_for_game(g),
                    height=80,
                    width=200
                )
            else:
                btn = tk.Button(
                    self.games_frame,
                    text=name,
                    command=lambda g=game: self.start_download_for_game(g),
                    width=25,
                    height=4,
                    wraplength=150,
                    justify="center"
                )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.games_frame.grid_rowconfigure(row, weight=1)
            self.games_frame.grid_columnconfigure(col, weight=1)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        self.log(f"Loaded {len(self.games)} game(s) from config.")

    def create_default_config(self):
        # Example config using your RE4 data
        template = {
            "depotdownloader_path": "DepotDownloaderMod.exe",
            "max_downloads": 256,
            "verify_all": True,
            "games": [
                {
                    "id": "re4_example",
                    "name": "Resident Evil 4 (Example)",
                    "app_id": 2050650,
                    "depotkeys_file": "2050650.key",
                    "output_dir": "",
                    "depots": [
                        {
                            "depot_id": 2050652,
                            "manifest_id": "6176917678100737873",
                            "manifest_file": "2050652_6176917678100737873.manifest"
                        },
                        {
                            "depot_id": 2050654,
                            "manifest_id": "4152569296804840016",
                            "manifest_file": "2050654_4152569296804840016.manifest"
                        },
                        {
                            "depot_id": 2050655,
                            "manifest_id": "8334430982901761350",
                            "manifest_file": "2050655_8334430982901761350.manifest"
                        }
                    ]
                }
            ]
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create default config:\n{e}")

    def reload_config(self):
        self.load_config()

    def log(self, text):
        self.log_queue.put(text)

    def process_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                timestamp = time.strftime("%H:%M:%S")
                self.log_text.insert("end", f"[{timestamp}] {line}\n")
                self.log_text.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self.process_log_queue)

    def start_download_for_game(self, game):
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showwarning("Busy", "A download is already running.")
            return

        depots = game.get("depots", [])
        if not depots:
            self.log("No depots defined for this game.")
            return

        if ctk:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(f"Select Languages/Components")
            dialog.geometry("500x550")
            dialog.attributes("-topmost", True)
        else:
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Select Languages/Components")
            dialog.geometry("500x550")
            dialog.grab_set()

        if ctk:
            lbl = ctk.CTkLabel(dialog, text="اختر اللغات أو الأقسام التي تريد تحميلها للعبة:", font=("Arial", 16, "bold"))
            lbl.pack(pady=10)
            scroll_frame = ctk.CTkScrollableFrame(dialog, width=450, height=400)
            scroll_frame.pack(pady=5, fill="both", expand=True)
        else:
            lbl = tk.Label(dialog, text="اختر اللغات أو الأقسام التي تريد تحميلها للعبة:", font=("Arial", 14, "bold"))
            lbl.pack(pady=10)
            scroll_frame = tk.Frame(dialog)
            scroll_frame.pack(pady=5, fill="both", expand=True)

        vars_dict = {}
        for d in depots:
            did = str(d.get("depot_id"))
            label_text = f"Depot {did}"
            if "desc" in d:
                label_text += f" - {d['desc']}"

            # Only pre-check English and Base components, uncheck others by default to save bandwidth
            default_chk = False
            if "desc" in d and ("Base" in d["desc"] or "English" in d["desc"] or "DirectX" in d["desc"]):
                default_chk = True

            if ctk:
                var = ctk.BooleanVar(value=default_chk)
                cb = ctk.CTkCheckBox(scroll_frame, text=label_text, variable=var)
                cb.pack(anchor="w", pady=5, padx=10)
            else:
                var = tk.BooleanVar(value=default_chk)
                cb = tk.Checkbutton(scroll_frame, text=label_text, variable=var)
                cb.pack(anchor="w", pady=2, padx=10)
            
            vars_dict[did] = var

        def on_confirm():
            chosen = [d for d in depots if vars_dict[str(d.get("depot_id"))].get()]
            if not chosen:
                if ctk:
                    messagebox.showwarning("Warning", "No components selected.")
                else:
                    messagebox.showwarning("Warning", "No components selected.", parent=dialog)
                return
            dialog.destroy()
            self._begin_download(game, chosen)

        if ctk:
            btn = ctk.CTkButton(dialog, text="بدء التحميل (Start Download)", command=on_confirm)
            btn.pack(pady=10)
        else:
            btn = tk.Button(dialog, text="بدء التحميل (Start Download)", command=on_confirm, bg="green", fg="white", font=("Arial", 12, "bold"))
            btn.pack(pady=10)

    def _begin_download(self, game, chosen_depots):
        self.stop_flag.clear()
        self.status_label.configure(text=f"Starting: {game.get('name','Game')}")
        if ctk:
            self.progress.set(0)
        else:
            self.progress_var.set(0)

        self.current_thread = threading.Thread(
            target=self.download_game_thread, args=(game, chosen_depots), daemon=True
        )
        self.current_thread.start()

    def stop_download(self):
        if self.current_thread and self.current_thread.is_alive():
            self.log("Stopping download...")
            self.stop_flag.set()
        else:
            self.log("No active download to stop.")

    def download_game_thread(self, game, chosen_depots):
        exe_path = self.config.get("depotdownloader_path", "DepotDownloaderMod.exe")
        exe_path = os.path.join(self.base_dir, exe_path)
        if not os.path.exists(exe_path):
            self.log(f"DepotDownloader executable not found: {exe_path}")
            self.status_label.configure(text="Error: exe not found")
            return

        app_id = str(game.get("app_id"))
        depots = chosen_depots
        keys_file = game.get("depotkeys_file")
        output_dir = game.get("output_dir", "")
        max_downloads = self.config.get("max_downloads", 256)
        verify_all = self.config.get("verify_all", True)

        if not depots:
            self.log("No depots defined for this game.")
            self.status_label.configure(text="Error: no depots")
            return

        keys_file_path = os.path.join(self.base_dir, keys_file) if keys_file else None
        if keys_file_path and not os.path.exists(keys_file_path):
            self.log(f"Depot keys file not found: {keys_file_path}")
            self.status_label.configure(text="Error: keys missing")
            return

        total_depots = len(depots)
        self.log(f"Starting download for {game.get('name','Game')} ({total_depots} depot(s))")

        for index, depot in enumerate(depots, start=1):
            if self.stop_flag.is_set():
                self.log("Download stopped by user.")
                break

            depot_id = str(depot.get("depot_id"))
            manifest_id = str(depot.get("manifest_id"))
            manifest_file = depot.get("manifest_file")
            manifest_path = os.path.join(self.base_dir, manifest_file) if manifest_file else None

            if manifest_path and not os.path.exists(manifest_path):
                self.log(f"Manifest file missing: {manifest_path}")
                continue

            self.status_label.configure(
                text=f"Depot {index}/{total_depots}: {depot_id}"
            )

            cmd = [exe_path, "-app", app_id, "-depot", depot_id,
                   "-manifest", manifest_id]

            if manifest_path:
                cmd += ["-manifestfile", manifest_path]

            if keys_file_path:
                cmd += ["-depotkeys", keys_file_path]

            if max_downloads:
                cmd += ["-max-downloads", str(max_downloads)]

            if verify_all:
                cmd += ["-verify-all"]

            # NOTE: Many builds of DepotDownloaderMod don't support -outputdir.
            # If yours does, set "output_dir" in config; if it gives errors, keep it "".
            if output_dir:
                out_dir_full = os.path.join(self.base_dir, output_dir)
                os.makedirs(out_dir_full, exist_ok=True)
                cmd += ["-outputdir", out_dir_full]

            self.log(f"Running: {' '.join(cmd)}")
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            except Exception as e:
                self.log(f"Failed to start process: {e}")
                break

            # Read output
            while True:
                if self.stop_flag.is_set():
                    process.terminate()
                    self.log("Process terminated.")
                    break

                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    else:
                        time.sleep(0.1)
                        continue

                line = line.rstrip()
                if line:
                    self.log(line)
                    # Try naive progress detection
                    perc = self.extract_percentage(line)
                    if perc is not None:
                        if ctk:
                            self.progress.set(perc / 100.0)
                        else:
                            self.progress_var.set(perc)

            retcode = process.poll()
            if retcode == 0:
                self.log(f"Depot {depot_id} finished successfully.")
            else:
                self.log(f"Depot {depot_id} exited with code {retcode}.")

            # Update overall depot progress (in case we never saw % output)
            frac = index / total_depots
            if ctk:
                self.progress.set(frac)
            else:
                self.progress_var.set(frac * 100)

        self.status_label.configure(text="Done")
        self.log("All requested depots processed.")

    @staticmethod
    def extract_percentage(line):
        # Try to find a pattern like ' 42%' in the line
        import re
        m = re.search(r'(\d{1,3})\s*%', line)
        if m:
            try:
                val = int(m.group(1))
                if 0 <= val <= 100:
                    return val
            except ValueError:
                return None
        return None


def main():
    if ctk:
        root = ctk.CTk()
    else:
        root = tk.Tk()
    app = DepotDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
