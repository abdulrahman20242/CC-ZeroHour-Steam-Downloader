import os
import sys
import re
import json
import threading
import queue
import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

_IS_WIN = sys.platform == "win32"
_IS_MAC = sys.platform == "darwin"

try:
    _POPEN_FLAGS = subprocess.CREATE_NO_WINDOW if _IS_WIN else 0
except AttributeError:
    _POPEN_FLAGS = 0


class DepotDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_path = os.path.join(self.base_dir, "games_config.json")
        self.config = {}
        self.games = []
        self.game_buttons = []               # ← عشان نعمل disable/enable
        self.current_thread = None
        self.current_process = None
        self.log_queue = queue.Queue()
        self.stop_flag = threading.Event()

        self._pending_status = None
        self._pending_progress = None

        if ctk:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("dark-blue")

        root.title("DepotDownloader Mod GUI")
        root.geometry("1000x650")
        root.minsize(800, 500)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.build_ui()
        self.load_config()
        self.root.after(100, self._poll_updates)

    # ──────────────────────────────────────────────
    #  Safe Close
    # ──────────────────────────────────────────────
    def _on_close(self):
        if self.current_thread and self.current_thread.is_alive():
            if not messagebox.askyesno(
                "تأكيد", "فيه تحميل شغال، متأكد تقفل؟"
            ):
                return
            self.stop_flag.set()
            self._kill_process(self.current_process)
        self.root.destroy()

    # ──────────────────────────────────────────────
    #  Thread-Safe GUI Updates
    # ──────────────────────────────────────────────
    def set_status(self, text):
        self._pending_status = text

    def set_progress(self, value):
        self._pending_progress = max(0.0, min(1.0, value))

    def _apply_pending_updates(self):
        if self._pending_status is not None:
            txt = self._pending_status
            self._pending_status = None
            if ctk:
                self.status_label.configure(text=txt)
            else:
                self.status_label.config(text=txt)

        if self._pending_progress is not None:
            val = self._pending_progress
            self._pending_progress = None
            if ctk:
                self.progress.set(val)
            else:
                self.progress_var.set(val * 100)

    # ──────────────────────────────────────────────
    #  Cross-platform Mouse Wheel
    # ──────────────────────────────────────────────
    @staticmethod
    def _bind_mousewheel(widget, callback):
        """بتربط الـ scroll بالـ widget المحدد بس"""
        if _IS_WIN or _IS_MAC:
            widget.bind("<MouseWheel>", callback)
        else:
            # Linux
            widget.bind("<Button-4>", callback)
            widget.bind("<Button-5>", callback)

    @staticmethod
    def _get_scroll_delta(event):
        """بترجع عدد الوحدات للـ scroll (cross-platform)"""
        if _IS_WIN:
            return -1 * (event.delta // 120)
        elif _IS_MAC:
            return -1 * event.delta
        else:
            # Linux: Button-4 = up, Button-5 = down
            return -1 if event.num == 4 else 1

    # ──────────────────────────────────────────────
    #  Build UI
    # ──────────────────────────────────────────────
    def build_ui(self):
        if ctk:
            self.main_frame = ctk.CTkFrame(self.root)
        else:
            self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ─── Left: Games (scrollable) ───
        if ctk:
            self.games_frame = ctk.CTkScrollableFrame(
                self.main_frame, width=350
            )
            self.games_frame.pack(
                side="left", fill="both", expand=True, padx=(0, 5)
            )
        else:
            games_outer = tk.LabelFrame(
                self.main_frame, text="Games",
                font=("Arial", 11, "bold"),
            )
            games_outer.pack(
                side="left", fill="both", expand=True, padx=(0, 5)
            )

            self._games_canvas = tk.Canvas(
                games_outer, highlightthickness=0
            )
            games_sb = tk.Scrollbar(
                games_outer, orient="vertical",
                command=self._games_canvas.yview,
            )
            self.games_frame = tk.Frame(self._games_canvas)

            self.games_frame.bind(
                "<Configure>",
                lambda e: self._games_canvas.configure(
                    scrollregion=self._games_canvas.bbox("all")
                ),
            )
            self._games_canvas.create_window(
                (0, 0), window=self.games_frame, anchor="nw"
            )
            self._games_canvas.configure(yscrollcommand=games_sb.set)
            self._games_canvas.pack(side="left", fill="both", expand=True)
            games_sb.pack(side="right", fill="y")

            # ─── Mouse wheel للـ games canvas بس ───
            def _scroll_games(event):
                delta = self._get_scroll_delta(event)
                self._games_canvas.yview_scroll(delta, "units")

            # bind على الـ canvas والـ frame جواه بس
            self._bind_mousewheel(self._games_canvas, _scroll_games)
            self._bind_mousewheel(self.games_frame, _scroll_games)

        # ─── Right: Log + Progress ───
        if ctk:
            self.side_frame = ctk.CTkFrame(self.main_frame, width=450)
        else:
            self.side_frame = tk.Frame(self.main_frame, width=450)
        self.side_frame.pack(side="right", fill="both", expand=True)

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
                maximum=100,
            )
        self.progress.pack(fill="x", padx=5, pady=(10, 5))

        # Status label
        if ctk:
            self.status_label = ctk.CTkLabel(
                self.side_frame, text="⏳ Idle"
            )
        else:
            self.status_label = tk.Label(
                self.side_frame, text="⏳ Idle",
                anchor="w", font=("Consolas", 10),
            )
        self.status_label.pack(fill="x", padx=5)

        # Log text
        if ctk:
            self.log_text = ctk.CTkTextbox(
                self.side_frame, height=25, width=50
            )
            self.log_text.pack(
                fill="both", expand=True, padx=5, pady=5
            )
        else:
            log_container = tk.Frame(self.side_frame)
            log_container.pack(
                fill="both", expand=True, padx=5, pady=5
            )
            log_sb = tk.Scrollbar(log_container)
            log_sb.pack(side="right", fill="y")
            self.log_text = tk.Text(
                log_container, height=25, width=50,
                yscrollcommand=log_sb.set,
                bg="#1e1e1e", fg="#d4d4d4",
                font=("Consolas", 9), wrap="word",
            )
            self.log_text.pack(side="left", fill="both", expand=True)
            log_sb.config(command=self.log_text.yview)

        # Bottom buttons
        if ctk:
            self.bottom_frame = ctk.CTkFrame(self.side_frame)
        else:
            self.bottom_frame = tk.Frame(self.side_frame)
        self.bottom_frame.pack(fill="x", padx=5, pady=(0, 5))

        btn_defs = [
            ("🔄 Reload", self.reload_config, None),
            ("⛔ Stop", self.stop_download, "#cc3333"),
            ("🧹 Clear", self.clear_log, None),
        ]
        for text, cmd, color in btn_defs:
            if ctk:
                kw = {"fg_color": color} if color else {}
                b = ctk.CTkButton(
                    self.bottom_frame, text=text,
                    command=cmd, width=90, **kw
                )
            else:
                kw = {"bg": color, "fg": "white"} if color else {}
                b = tk.Button(
                    self.bottom_frame, text=text, command=cmd, **kw
                )
            b.pack(side="left", padx=(0, 5))

    # ──────────────────────────────────────────────
    #  Enable/Disable Game Buttons
    # ──────────────────────────────────────────────
    def _set_buttons_state(self, enabled):
        """بتعمل enable أو disable لأزرار الألعاب"""
        for btn in self.game_buttons:
            try:
                if ctk:
                    if enabled:
                        btn.configure(state="normal")
                    else:
                        btn.configure(state="disabled")
                else:
                    btn.config(state="normal" if enabled else "disabled")
            except tk.TclError:
                pass  # الزر ممكن يكون اتمسح

    # ──────────────────────────────────────────────
    #  Config
    # ──────────────────────────────────────────────
    def load_config(self):
        self.games = []
        self.game_buttons = []

        for w in self.games_frame.winfo_children():
            w.destroy()

        if not os.path.exists(self.config_path):
            self.log("Config not found → creating template...")
            self.create_default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "JSON Error",
                f"سطر {e.lineno}، عمود {e.colno}:\n{e.msg}",
            )
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{e}")
            return

        self.games = self.config.get("games", [])
        if not self.games:
            self.log("⚠ No games in config.")
            return

        cols = 2
        for idx, game in enumerate(self.games):
            row, col = divmod(idx, cols)
            name = game.get("name", f"Game {idx + 1}")
            n_depots = len(game.get("depots", []))
            label = f"{name}\n({n_depots} depots)"

            if ctk:
                btn = ctk.CTkButton(
                    self.games_frame, text=label,
                    command=lambda g=game: self.start_download_for_game(g),
                    height=80, width=200,
                )
            else:
                btn = tk.Button(
                    self.games_frame, text=label,
                    command=lambda g=game: self.start_download_for_game(g),
                    width=25, height=4, wraplength=180,
                    justify="center", bg="#2d5aa0", fg="white",
                    activebackground="#3d6ab0",
                    font=("Arial", 10, "bold"),
                )

                # ─── لو الماوس فوق الزر يلف الـ canvas ───
                if not ctk and hasattr(self, '_games_canvas'):
                    def _scroll_btn(event, canvas=self._games_canvas):
                        delta = self._get_scroll_delta(event)
                        canvas.yview_scroll(delta, "units")
                    self._bind_mousewheel(btn, _scroll_btn)

            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.games_frame.grid_rowconfigure(row, weight=1)
            self.games_frame.grid_columnconfigure(col, weight=1)
            self.game_buttons.append(btn)    # ← نحفظ reference

        self.log(f"✅ Loaded {len(self.games)} game(s).")

    def create_default_config(self):
        template = {
            "depotdownloader_path": "DepotDownloaderMod.exe",
            "max_downloads": 256,
            "verify_all": True,
            "games": [
                {
                    "id": "example",
                    "name": "Example Game",
                    "app_id": 2050650,
                    "depotkeys_file": "2050650.key",
                    "output_dir": "",
                    "depots": [
                        {
                            "depot_id": 2050652,
                            "manifest_id": "6176917678100737873",
                            "manifest_file": "2050652_6176917678100737873.manifest",
                            "desc": "Base Game",
                        }
                    ],
                }
            ],
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reload_config(self):
        self.load_config()

    # ──────────────────────────────────────────────
    #  Logging
    # ──────────────────────────────────────────────
    def log(self, text):
        self.log_queue.put(text)

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def _poll_updates(self):
        count = 0
        while count < 200:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{ts}] {line}\n")
            count += 1
        if count:
            self.log_text.see("end")

        self._apply_pending_updates()
        self.root.after(100, self._poll_updates)

    # ──────────────────────────────────────────────
    #  Download Dialog
    # ──────────────────────────────────────────────
    def start_download_for_game(self, game):
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showwarning("Busy", "A download is already running.")
            return

        depots = game.get("depots", [])
        if not depots:
            self.log("❌ No depots for this game.")
            return

        if ctk:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Select Components")
            dialog.geometry("520x560")
            dialog.transient(self.root)
            dialog.attributes("-topmost", True)
            dialog.after(200, lambda: dialog.attributes("-topmost", False))
            dialog.focus_force()
        else:
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Components")
            dialog.geometry("520x560")
            dialog.transient(self.root)
            dialog.attributes("-topmost", True)
            dialog.after(200, lambda: dialog.attributes("-topmost", False))
            dialog.grab_set()
            dialog.focus_force()

        title = f"🎮 {game.get('name', 'Game')}\nاختر الأقسام:"
        if ctk:
            ctk.CTkLabel(
                dialog, text=title, font=("Arial", 15, "bold")
            ).pack(pady=10)
            scroll = ctk.CTkScrollableFrame(dialog, width=460, height=380)
            scroll.pack(pady=5, fill="both", expand=True)
        else:
            tk.Label(
                dialog, text=title,
                font=("Arial", 13, "bold"), justify="center",
            ).pack(pady=10)
            scroll = tk.Frame(dialog)
            scroll.pack(pady=5, fill="both", expand=True)

        vars_dict = {}
        for d in depots:
            did = str(d.get("depot_id"))
            desc = d.get("desc", "")
            label = f"Depot {did}"
            if desc:
                label += f" — {desc}"

            default = any(
                kw in desc for kw in ("Base", "English", "DirectX", "Core")
            )
            var = tk.BooleanVar(value=default)

            if ctk:
                ctk.CTkCheckBox(
                    scroll, text=label, variable=var
                ).pack(anchor="w", pady=4, padx=10)
            else:
                tk.Checkbutton(
                    scroll, text=label, variable=var
                ).pack(anchor="w", pady=2, padx=10)
            vars_dict[did] = var

        if ctk:
            bf = ctk.CTkFrame(dialog)
        else:
            bf = tk.Frame(dialog)
        bf.pack(pady=5)

        def set_all(val):
            for v in vars_dict.values():
                v.set(val)

        for txt, val in [("✅ Select All", True), ("❎ Deselect", False)]:
            if ctk:
                ctk.CTkButton(
                    bf, text=txt, width=110,
                    command=lambda v=val: set_all(v),
                ).pack(side="left", padx=5)
            else:
                tk.Button(
                    bf, text=txt, command=lambda v=val: set_all(v)
                ).pack(side="left", padx=5)

        def on_confirm():
            chosen = [
                d for d in depots
                if vars_dict[str(d.get("depot_id"))].get()
            ]
            if not chosen:
                messagebox.showwarning(
                    "Warning", "No components selected.", parent=dialog
                )
                return
            dialog.destroy()
            self._begin_download(game, chosen)

        if ctk:
            ctk.CTkButton(
                dialog, text="⬇ بدء التحميل",
                command=on_confirm, height=40,
            ).pack(pady=10)
        else:
            tk.Button(
                dialog, text="⬇ بدء التحميل (Start)",
                command=on_confirm,
                bg="#228B22", fg="white",
                font=("Arial", 12, "bold"),
            ).pack(pady=10)

    # ──────────────────────────────────────────────
    #  Download Core
    # ──────────────────────────────────────────────
    def _begin_download(self, game, chosen_depots):
        self.stop_flag.clear()
        self.set_status(f"▶ Starting: {game.get('name', 'Game')}")
        self.set_progress(0)
        self._set_buttons_state(False)       # ← disable الأزرار

        self.current_thread = threading.Thread(
            target=self._download_worker,
            args=(game, chosen_depots),
            daemon=True,
        )
        self.current_thread.start()

    def stop_download(self):
        if self.current_thread and self.current_thread.is_alive():
            self.log("⛔ Stopping...")
            self.stop_flag.set()
            self._kill_process(self.current_process)
        else:
            self.log("No active download.")

    @staticmethod
    def _kill_process(proc):
        if proc is None:
            return
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        except Exception:
            pass

    def _download_worker(self, game, chosen_depots):
        try:
            self._run_downloads(game, chosen_depots)
        finally:
            # ─── دايماً نرجع الأزرار حتى لو حصل error ───
            self.current_process = None
            self.root.after(0, lambda: self._set_buttons_state(True))

    def _run_downloads(self, game, chosen_depots):
        exe = os.path.join(
            self.base_dir,
            self.config.get("depotdownloader_path", "DepotDownloaderMod.exe"),
        )
        if not os.path.exists(exe):
            self.log(f"❌ Not found: {exe}")
            self.set_status("Error: exe missing")
            return

        app_id = str(game.get("app_id"))
        keys_file = game.get("depotkeys_file", "")
        output_dir = game.get("output_dir", "")
        max_dl = self.config.get("max_downloads", 256)
        verify = self.config.get("verify_all", True)

        keys_path = (
            os.path.join(self.base_dir, keys_file) if keys_file else None
        )
        if keys_path and not os.path.exists(keys_path):
            self.log(f"❌ Keys missing: {keys_path}")
            self.set_status("Error: keys missing")
            return

        total = len(chosen_depots)
        self.log(f"📦 {game.get('name')} — {total} depot(s)")

        for idx, depot in enumerate(chosen_depots, start=1):
            if self.stop_flag.is_set():
                break

            depot_id = str(depot.get("depot_id"))
            manifest_id = str(depot.get("manifest_id"))
            mf = depot.get("manifest_file", "")
            mf_path = os.path.join(self.base_dir, mf) if mf else None

            if mf_path and not os.path.exists(mf_path):
                self.log(f"⚠ Manifest missing: {mf}, skip")
                continue

            desc = depot.get("desc", depot_id)
            self.set_status(f"📥 [{idx}/{total}] {desc}")

            cmd = [exe, "-app", app_id, "-depot", depot_id,
                   "-manifest", manifest_id]
            if mf_path:
                cmd += ["-manifestfile", mf_path]
            if keys_path:
                cmd += ["-depotkeys", keys_path]
            if max_dl:
                cmd += ["-max-downloads", str(max_dl)]
            if verify:
                cmd += ["-verify-all"]
            if output_dir:
                out = os.path.join(self.base_dir, output_dir)
                os.makedirs(out, exist_ok=True)
                cmd += ["-outputdir", out]

            self.log(f"🔧 {' '.join(cmd)}")

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=_POPEN_FLAGS,
                )
                self.current_process = proc
            except Exception as e:
                self.log(f"❌ Failed: {e}")
                break

            try:
                for line in proc.stdout:
                    if self.stop_flag.is_set():
                        self._kill_process(proc)
                        break
                    line = line.rstrip()
                    if not line:
                        continue
                    self.log(line)
                    perc = self._extract_percentage(line)
                    if perc is not None:
                        overall = ((idx - 1) + perc / 100.0) / total
                        self.set_progress(overall)
            except Exception as e:
                self.log(f"⚠ Read error: {e}")

            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._kill_process(proc)

            self.current_process = None

            if self.stop_flag.is_set():
                self.log("⛔ Stopped by user.")
                break

            rc = proc.returncode
            if rc == 0:
                self.log(f"✅ Depot {depot_id} done.")
            else:
                self.log(f"⚠ Depot {depot_id} exit: {rc}")

            self.set_progress(idx / total)

        if self.stop_flag.is_set():
            self.set_status("⛔ Stopped")
        else:
            self.set_status("✅ Done")
            self.log("🏁 All depots processed.")

    @staticmethod
    def _extract_percentage(line):
        m = re.search(r'(\d{1,3})\s*%', line)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 100:
                return val
        return None


