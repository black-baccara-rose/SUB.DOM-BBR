"""
SUB.DOM-BBR  //  passive subdomain finder
made by  : Black Baccara Rose
official : https://black-baccara-rose.netlify.app/
"""
import csv
import json
import queue
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

TOOL_NAME = "SUB.DOM-BBR"
AUTHOR = "Black Baccara Rose"
OFFICIAL_LINK = "https://black-baccara-rose.netlify.app/"
APP_TITLE = f"{TOOL_NAME} // {AUTHOR}"

# ---- Black Baccara palette: void black + blood rose ----
BG = "#050205"
PANEL = "#0d0609"
PANEL2 = "#090406"
INPUT = "#030103"
BORDER = "#2a0e17"
ACCENT = "#ff2d55"
ACCENT_HI = "#ff6b86"
ACCENT_DK = "#7a0f26"
TEXT = "#f3e7eb"
MUTED = "#8c6f78"
GREEN = "#6ee7a8"
RED = "#ff4d6d"
YELLOW = "#ffd166"
MONO = "Consolas"

BOOT_LINES = [
    "root@blackbaccara: sudo bloom --force",
    "[ ENCRYPTED ] connection secured",
    "loading modules: crt.sh / ctlogs / certspotter / hostsearch",
    "mission: liberate information. protect the fragile. bloom in the dark.",
]


def normalize_domain(value):
    value = value.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0].split(":")[0].rstrip(".")
    if value.startswith("*."):
        value = value[2:]
    if not value or "." not in value or len(value) > 253:
        raise ValueError("Enter a valid domain, e.g. example.com")
    if any(not re.fullmatch(r"[a-z0-9-]+", label) for label in value.split(".")):
        raise ValueError("Domain contains invalid characters.")
    if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
           for label in value.split(".")):
        raise ValueError("Domain labels are invalid.")
    return value


class SubdomainFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1160x780")
        self.root.minsize(940, 660)
        self.root.configure(bg=BG)
        self.events = queue.Queue()
        self.results = {}
        self.running = False
        self.current_domain = "target"
        self.cursor_on = True
        self.cancel_event = threading.Event()
        self._style()
        self._build()
        self.root.after(100, self._poll_events)
        self.root.after(550, self._blink)

    # ------------------------------------------------------------ styling
    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=PANEL2, foreground=TEXT,
                        fieldbackground=PANEL2, rowheight=28, borderwidth=0,
                        font=(MONO, 10))
        style.configure("Treeview.Heading", background="#1a0910", foreground=ACCENT,
                        font=(MONO, 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT_DK)],
                  foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", "#2a0e17")])
        style.configure("TProgressbar", troughcolor="#1a0910", background=ACCENT,
                        bordercolor="#1a0910", lightcolor=ACCENT, darkcolor=ACCENT)
        style.configure("Vertical.TScrollbar", background="#1a0910", troughcolor=PANEL2,
                        bordercolor=PANEL2, arrowcolor=ACCENT)

    def _label(self, parent, text, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.get("bg", PANEL),
                        fg=kwargs.get("fg", TEXT), font=kwargs.get("font", (MONO, 10)),
                        anchor=kwargs.get("anchor", "w"))

    def _button(self, parent, text, command, primary=False, **grid):
        if primary:
            btn = tk.Button(parent, text=text, command=command, bg=ACCENT, fg="#150006",
                            activebackground=ACCENT_HI, activeforeground="#150006",
                            relief="flat", font=(MONO, 10, "bold"), padx=18, pady=10,
                            cursor="hand2", bd=0)
        else:
            btn = tk.Button(parent, text=text, command=command, bg="#1a0910", fg=TEXT,
                            activebackground=ACCENT_DK, activeforeground="#ffffff",
                            disabledforeground="#5a4249", relief="flat",
                            font=(MONO, 10, "bold"), padx=14, pady=10, cursor="hand2", bd=0)
        return btn

    def _open_link(self, _event=None):
        webbrowser.open(OFFICIAL_LINK)

    # ------------------------------------------------------------ layout
    def _build(self):
        # top rose line
        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill="x")

        header = tk.Frame(self.root, bg=BG, padx=24, pady=14)
        header.pack(fill="x")
        left = tk.Frame(header, bg=BG)
        left.pack(side="left")
        title_row = tk.Frame(left, bg=BG)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="SUB.DOM", bg=BG, fg=TEXT,
                 font=(MONO, 26, "bold")).pack(side="left")
        tk.Label(title_row, text="-BBR", bg=BG, fg=ACCENT,
                 font=(MONO, 26, "bold")).pack(side="left")
        tk.Label(title_row, text="  // তথ্য বদ্ধ থাকার জিনিস নয় — এটি বাগানের মতো, যত্ন করলে ফোটে, আটকে রাখলে শুকিয়ে যায়।", bg=BG, fg=MUTED,
                 font=(MONO, 8)).pack(side="left", pady=(10, 0))
        self.boot_label = tk.Label(left, text="", bg=BG, fg=GREEN, font=(MONO, 9), anchor="w")
        self.boot_label.pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")
        tk.Label(right, text="BLACK  BACCARA  ROSE", bg=BG, fg=ACCENT,
                 font=(MONO, 12, "bold")).pack(anchor="e")
        link = tk.Label(right, text=OFFICIAL_LINK, bg=BG, fg=ACCENT_HI, cursor="hand2",
                        font=(MONO, 9, "underline"))
        link.pack(anchor="e", pady=(3, 0))
        link.bind("<Button-1>", self._open_link)
        tk.Label(right, text="CT LOGS + DNS RESOLUTION  |  PASSIVE RECON", bg=BG, fg=MUTED,
                 font=(MONO, 8)).pack(anchor="e", pady=(3, 0))

        controls = tk.Frame(self.root, bg=PANEL, padx=18, pady=15,
                            highlightbackground=BORDER, highlightthickness=1)
        controls.pack(fill="x", padx=24)
        self._label(controls, "// 01 — TARGET DOMAIN", fg=ACCENT, font=(MONO, 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        self.domain_var = tk.StringVar()
        self.domain_entry = tk.Entry(controls, textvariable=self.domain_var, bg=INPUT,
                                     fg=TEXT, insertbackground=ACCENT, relief="flat",
                                     font=(MONO, 12), width=42, highlightthickness=1,
                                     highlightbackground=BORDER, highlightcolor=ACCENT)
        self.domain_entry.grid(row=1, column=0, sticky="ew", ipady=9, padx=(0, 12))
        self.domain_entry.insert(0, "example.com")
        self.domain_entry.bind("<Return>", lambda _e: self.start_scan())
        self.resolve_var = tk.BooleanVar(value=True)
        tk.Checkbutton(controls, text="Resolve DNS / IPs", variable=self.resolve_var,
                       bg=PANEL, fg=TEXT, selectcolor=INPUT, activebackground=PANEL,
                       activeforeground=ACCENT, font=(MONO, 10)).grid(
                           row=1, column=1, padx=6, sticky="w")
        self.scan_btn = self._button(controls, "▶  BLOOM", self.start_scan, primary=True)
        self.scan_btn.grid(row=1, column=2, padx=(12, 6))
        self.stop_btn = self._button(controls, "■ STOP", self.stop_scan)
        self.stop_btn.config(state="disabled")
        self.stop_btn.grid(row=1, column=3, padx=6)
        controls.grid_columnconfigure(0, weight=1)

        stats = tk.Frame(self.root, bg=BG, padx=24, pady=12)
        stats.pack(fill="x")
        self.stat_total = self._stat(stats, "DISCOVERED", "0")
        self.stat_live = self._stat(stats, "DNS RESOLVED", "0")
        self.stat_source = self._stat(stats, "SOURCES", "4 / PASSIVE")
        self.stat_state = self._stat(stats, "STATUS", "[ READY ]")

        main = tk.Frame(self.root, bg=BG, padx=24, pady=4)
        main.pack(fill="both", expand=True)
        results_panel = tk.Frame(main, bg=PANEL, padx=10, pady=10,
                                 highlightbackground=BORDER, highlightthickness=1)
        results_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        top = tk.Frame(results_panel, bg=PANEL)
        top.pack(fill="x", pady=(0, 8))
        self._label(top, "// 02 — DISCOVERED HOSTS", fg=ACCENT,
                    font=(MONO, 11, "bold")).pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._refresh_tree())
        tk.Entry(top, textvariable=self.filter_var, bg=INPUT, fg=TEXT, insertbackground=ACCENT,
                 relief="flat", font=(MONO, 10), width=22, highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT).pack(side="right", ipady=4)
        self._label(top, "grep ›", fg=MUTED, font=(MONO, 9)).pack(side="right", padx=(0, 6))

        columns = ("subdomain", "ip", "status", "source", "open", "copy")
        self.tree = ttk.Treeview(results_panel, columns=columns, show="headings")
        for col, title, width in [
            ("subdomain", "SUBDOMAIN", 270), ("ip", "IP ADDRESS", 140),
            ("status", "DNS STATUS", 105), ("source", "SOURCE", 90),
            ("open", "OPEN", 70), ("copy", "COPY", 70)
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center" if col in ("open", "copy") else "w",
                             stretch=col == "subdomain")
        self.tree.tag_configure("resolved", foreground=GREEN)
        self.tree.tag_configure("nodns", foreground=MUTED)
        self.tree.tag_configure("plain", foreground=TEXT)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._show_menu)
        self.tree.bind("<Button-2>", self._show_menu)
        self.menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT, activebackground=ACCENT_DK,
                            activeforeground="#ffffff", font=(MONO, 10), bd=0)
        self.menu.add_command(label="↗  Open in browser", command=self.open_selected)
        self.menu.add_command(label="⧉  Copy URL (https://)", command=self.copy_selected_urls)
        self.menu.add_command(label="⧉  Copy subdomain", command=self._copy_selected)
        yscroll = ttk.Scrollbar(results_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        side = tk.Frame(main, bg=PANEL, width=310, padx=12, pady=10,
                        highlightbackground=BORDER, highlightthickness=1)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        self._label(side, "// 03 — ACTIVITY LOG", fg=ACCENT,
                    font=(MONO, 11, "bold")).pack(anchor="w", pady=(0, 8))
        self.log = tk.Text(side, bg=INPUT, fg=MUTED, insertbackground=ACCENT,
                           relief="flat", font=(MONO, 9), wrap="word", height=18,
                           highlightthickness=0)
        self.log.pack(fill="both", expand=True)
        self.log.tag_configure("ok", foreground=GREEN)
        self.log.tag_configure("warn", foreground=YELLOW)
        self.log.tag_configure("err", foreground=RED)
        self.log.tag_configure("info", foreground=ACCENT_HI)
        self._button(side, "↗ OPEN IN BROWSER", self.open_selected, primary=True).pack(fill="x", pady=(10, 5))
        self._button(side, "⧉ COPY URL", self.copy_selected_urls).pack(fill="x", pady=(0, 5))
        self._button(side, "EXPORT CSV", self.export_csv).pack(fill="x", pady=(0, 5))
        self._button(side, "EXPORT TXT", self.export_txt).pack(fill="x")
        self._button(side, "COPY ALL", self.copy_all).pack(fill="x", pady=(5, 0))

        footer = tk.Frame(self.root, bg=BG, padx=24, pady=10)
        footer.pack(fill="x")
        self.progress = ttk.Progressbar(footer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 8))
        tk.Label(footer, text="PASSIVE DISCOVERY ONLY  •  Use only on domains you own or are authorized to assess",
                 bg=BG, fg=MUTED, font=(MONO, 8)).pack(anchor="w")
        bottom = tk.Frame(footer, bg=BG)
        bottom.pack(fill="x", pady=(4, 0))
        self.prompt = tk.Label(bottom, text="guest@blackbaccara:~$ █", bg=BG, fg=ACCENT,
                               font=(MONO, 9))
        self.prompt.pack(side="left")
        credit = tk.Label(bottom, text=f"© {AUTHOR.upper()} — internet is open to all {{^-^}}",
                          bg=BG, fg=MUTED, font=(MONO, 8), cursor="hand2")
        credit.pack(side="right")
        credit.bind("<Button-1>", self._open_link)

        self._boot_sequence()
        self._log("Ready. Enter a domain you own or have permission to assess.", "info")

    def _stat(self, parent, label, value):
        box = tk.Frame(parent, bg=PANEL, padx=14, pady=9,
                       highlightbackground=BORDER, highlightthickness=1)
        box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(box, text=label, bg=PANEL, fg=MUTED, font=(MONO, 8, "bold")).pack(anchor="w")
        val = tk.Label(box, text=value, bg=PANEL, fg=ACCENT, font=(MONO, 15, "bold"))
        val.pack(anchor="w", pady=(4, 0))
        return val

    # ------------------------------------------------------------ small effects
    def _boot_sequence(self):
        self._boot_i = 0
        self._boot_pos = 0
        self._boot_tick()

    def _boot_tick(self):
        line = BOOT_LINES[self._boot_i % len(BOOT_LINES)]
        if self._boot_pos <= len(line):
            self.boot_label.config(text="$ " + line[:self._boot_pos])
            self._boot_pos += 1
            self.root.after(28, self._boot_tick)
        else:
            self._boot_i += 1
            self._boot_pos = 0
            self.root.after(2200, self._boot_tick)

    def _blink(self):
        self.cursor_on = not self.cursor_on
        self.prompt.config(text="guest@blackbaccara:~$ " + ("█" if self.cursor_on else " "))
        self.root.after(550, self._blink)

    def _log(self, message, tag="info"):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{stamp}] {message}\n", tag)
        self.log.see("end")

    # ------------------------------------------------------------ tree helpers
    @staticmethod
    def _row_tag(row):
        if row["status"] == "RESOLVED":
            return "resolved"
        if row["status"] == "NO DNS":
            return "nodns"
        return "plain"

    def _matches_filter(self, row):
        needle = self.filter_var.get().strip().lower()
        if not needle:
            return True
        return needle in " ".join(str(v) for v in row.values()).lower()

    def _insert_row(self, row):
        self.tree.insert("", "end", values=(row["subdomain"], row["ip"], row["status"], row["source"],
                                            "↗ open", "⧉ copy"),
                         tags=(self._row_tag(row),))

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.results.values():
            if self._matches_filter(row):
                self._insert_row(row)

    def _copy_selected(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        text = "\n".join(self.tree.item(i, "values")[0] for i in sel)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log(f"Copied {len(sel)} subdomain(s) to clipboard.", "ok")

    # ---- one-click open / copy ----
    @staticmethod
    def _url(host):
        return "https://" + host

    def _clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _on_tree_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item:
            return
        host = self.tree.item(item, "values")[0]
        if col == "#5":
            webbrowser.open(self._url(host))
            self._log(f"Opened {self._url(host)}", "ok")
            return "break"
        if col == "#6":
            self._clipboard(self._url(host))
            self._log(f"Copied {self._url(host)}", "ok")
            return "break"

    def _on_tree_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item and self.tree.identify_column(event.x) not in ("#5", "#6"):
            host = self.tree.item(item, "values")[0]
            webbrowser.open(self._url(host))
            self._log(f"Opened {self._url(host)}", "ok")

    def _show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        if item not in self.tree.selection():
            self.tree.selection_set(item)
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Select one or more subdomains first.")
            return
        if len(sel) > 5 and not messagebox.askyesno(
                "Open many tabs", f"Open {len(sel)} tabs in your browser?"):
            return
        for i in sel:
            webbrowser.open(self._url(self.tree.item(i, "values")[0]))
        self._log(f"Opened {len(sel)} URL(s) in browser.", "ok")

    def copy_selected_urls(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Select one or more subdomains first.")
            return
        self._clipboard("\n".join(self._url(self.tree.item(i, "values")[0]) for i in sel))
        self._log(f"Copied {len(sel)} URL(s) to clipboard.", "ok")

    def copy_all(self):
        if not self.results:
            messagebox.showinfo("Nothing to copy", "Run a scan first.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(sorted(self.results)))
        self._log(f"Copied {len(self.results)} subdomains to clipboard.", "ok")

    # ------------------------------------------------------------ scan control
    def start_scan(self):
        if self.running:
            return
        try:
            domain = normalize_domain(self.domain_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid domain", str(exc))
            return
        if not messagebox.askyesno("Authorization check",
                                   f"Confirm you own or are authorized to assess {domain}.\n\n"
                                   "This tool uses passive certificate data and optional DNS lookups. Continue?"):
            return
        self.domain_var.set(domain)
        self.current_domain = domain
        self.results.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.stat_total.config(text="0")
        self.stat_live.config(text="0")
        self.stat_state.config(text="[ RUNNING ]")
        self.running = True
        self.cancel_event.clear()
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start(12)
        self._log(f"sudo bloom --target {domain}", "info")
        self._log(f"Starting passive certificate lookup for {domain}", "info")
        threading.Thread(target=self._worker, args=(domain, self.resolve_var.get()), daemon=True).start()

    def stop_scan(self):
        if self.running:
            self.cancel_event.set()
            self._log("Stop requested; waiting for current request to finish.", "warn")
            self.stop_btn.config(state="disabled")

    def _fetch_json_with_retry(self, url, source_name, attempts=3):
        """Fetch a public passive-discovery endpoint with short retries."""
        last_error = None
        for attempt in range(1, attempts + 1):
            if self.cancel_event.is_set():
                return None
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "SUB.DOM-BBR/2.0 (passive DNS discovery)",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=25) as response:
                    return json.loads(response.read(15_000_000).decode("utf-8", errors="replace"))
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}"
                # Retrying transient server/rate-limit errors can help; do not retry most client errors.
                if exc.code not in (408, 425, 429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                last_error = str(exc)
            if attempt < attempts:
                self.events.put(("log", f"{source_name}: attempt {attempt}/{attempts} failed ({last_error}); retrying…", "warn"))
                # Small bounded backoff, interruptible by Stop.
                for _ in range(attempt * 5):
                    if self.cancel_event.is_set():
                        return None
                    time.sleep(0.2)
        self.events.put(("log", f"{source_name} unavailable after {attempts} attempts: {last_error}", "warn"))
        return None

    def _fetch_text_with_retry(self, url, source_name, attempts=3):
        last_error = None
        for attempt in range(1, attempts + 1):
            if self.cancel_event.is_set():
                return None
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "SUB.DOM-BBR/2.0 (passive subdomain discovery)",
                        "Accept": "text/plain, application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    return response.read(8_000_000).decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}"
                if exc.code not in (408, 425, 429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
            if attempt < attempts:
                self.events.put(("log", f"{source_name}: attempt {attempt}/{attempts} failed ({last_error}); retrying…", "warn"))
                for _ in range(attempt * 5):
                    if self.cancel_event.is_set():
                        return None
                    time.sleep(0.2)
        self.events.put(("log", f"{source_name} unavailable after {attempts} attempts: {last_error}", "warn"))
        return None

    def _worker(self, domain, do_resolve):
        discovered = {}
        source_errors = 0
        sources = [
            (
                "crt.sh",
                "https://crt.sh/?" + urllib.parse.urlencode(
                    {"q": f"%.{domain}", "output": "json"}
                ),
                "crt",
            ),
            (
                "ctlogs.dev",
                "https://ctlogs.dev/search?" + urllib.parse.urlencode(
                    {"q": f"%.{domain}", "output": "json"}
                ),
                "crt",
            ),
            (
                "CertSpotter",
                "https://api.certspotter.com/v1/issuances?" + urllib.parse.urlencode({
                    "domain": domain,
                    "include_subdomains": "true",
                    "expand": "dns_names",
                    "limit": "1000",
                }),
                "certspotter",
            ),
            (
                "HackerTarget",
                "https://api.hackertarget.com/hostsearch/?" + urllib.parse.urlencode(
                    {"q": domain}
                ),
                "hostsearch",
            ),
        ]

        for source_name, url, source_kind in sources:
            if self.cancel_event.is_set():
                break
            self.events.put(("log", f"Querying live source: {source_name}", "info"))
            if source_kind == "hostsearch":
                data = self._fetch_text_with_retry(url, source_name)
            else:
                data = self._fetch_json_with_retry(url, source_name)
            if data is None:
                source_errors += 1
                continue

            count_before = len(discovered)
            try:
                if source_kind == "hostsearch":
                    # Format: hostname,ip on each line. Error messages are plain text too.
                    for line in str(data).splitlines():
                        bits = line.strip().split(",", 1)
                        if len(bits) != 2:
                            continue
                        host = bits[0].strip().lower().rstrip(".")
                        if self._is_subdomain(host, domain) and host != domain:
                            discovered.setdefault(host, set()).add(source_name)
                else:
                    rows = data if isinstance(data, list) else []
                    for row in rows:
                        if self.cancel_event.is_set():
                            break
                        if source_kind == "crt":
                            names = str(row.get("name_value", "")).splitlines()
                            if not names and row.get("dns_names"):
                                names = row.get("dns_names", [])
                        else:
                            names = row.get("dns_names", [])
                            if isinstance(names, str):
                                names = [names]
                        for name in names:
                            host = str(name).strip().lower().rstrip(".")
                            if host.startswith("*."):
                                host = host[2:]
                            if self._is_subdomain(host, domain) and host != domain:
                                discovered.setdefault(host, set()).add(source_name)
                self.events.put((
                    "log",
                    f"{source_name} returned {len(discovered) - count_before} new unique subdomains.",
                    "ok",
                ))
            except (AttributeError, TypeError, ValueError) as exc:
                source_errors += 1
                self.events.put(("log", f"Could not parse {source_name} response: {exc}", "warn"))

        if not discovered and source_errors == len(sources):
            self.events.put(("log", "All live API sources failed. Check internet access, firewall, DNS, or API rate limits.", "err"))
            self.events.put(("done", "Error"))
            return
        if not discovered:
            self.events.put(("log", "No subdomains returned by available sources. This does not prove none exist.", "warn"))

        for host in sorted(discovered):
            if self.cancel_event.is_set():
                break
            ips = []
            status = "NOT CHECKED"
            if do_resolve:
                try:
                    infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
                    ips = sorted({item[4][0] for item in infos})
                    status = "RESOLVED" if ips else "NO DNS"
                except (socket.gaierror, OSError):
                    status = "NO DNS"
            row = {
                "subdomain": host,
                "ip": ", ".join(ips),
                "status": status,
                "source": ", ".join(sorted(discovered[host])),
            }
            self.events.put(("result", row))
        self.events.put(("done", "Stopped" if self.cancel_event.is_set() else "Complete"))

    @staticmethod
    def _is_subdomain(host, domain):
        if not host or len(host) > 253:
            return False
        if not re.fullmatch(r"[a-z0-9.-]+", host):
            return False
        labels = host.split(".")
        if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
               for label in labels):
            return False
        return host == domain or host.endswith("." + domain)

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self._log(event[1], event[2])
                elif kind == "result":
                    row = event[1]
                    self.results[row["subdomain"]] = row
                    if self._matches_filter(row):
                        self._insert_row(row)
                    self.stat_total.config(text=str(len(self.results)))
                    self.stat_live.config(text=str(sum(1 for r in self.results.values() if r["status"] == "RESOLVED")))
                elif kind == "done":
                    self.running = False
                    self.progress.stop()
                    self.scan_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.stat_state.config(text=f"[ {event[1].upper()} ]")
                    self._log(f"Scan {event[1].lower()}. Total results: {len(self.results)}", "ok" if event[1] == "Complete" else "warn")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def export_csv(self):
        if not self.results:
            messagebox.showinfo("Nothing to export", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=f"SUB.DOM-BBR_{self.current_domain}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=["subdomain", "ip", "status", "source"])
                writer.writeheader()
                writer.writerows(self.results.values())
            self._log(f"Exported CSV: {path}", "ok")
            messagebox.showinfo("Export complete", f"Saved {len(self.results)} results.")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))

    def export_txt(self):
        if not self.results:
            messagebox.showinfo("Nothing to export", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                    filetypes=[("Text files", "*.txt")],
                    initialfile=f"SUB.DOM-BBR_{self.current_domain}.txt")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(f"# {TOOL_NAME} | made by {AUTHOR} | {OFFICIAL_LINK}\n")
                file.write(f"# target: {self.current_domain} | {datetime.now():%Y-%m-%d %H:%M}\n")
                for host in sorted(self.results):
                    file.write(host + "\n")
            self._log(f"Exported TXT: {path}", "ok")
            messagebox.showinfo("Export complete", f"Saved {len(self.results)} subdomains.")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = SubdomainFinderApp(root)
    root.mainloop()
