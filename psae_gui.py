"""
PSAE GUI — tkinter wrapper for the PSAE backtest & signal CLI tools.
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import sys
import os
import io
from datetime import datetime, timedelta

# ── colour palette ──────────────────────────────────────────────────────────
BG      = "#0d1117"   # GitHub dark background
PANEL   = "#161b22"
BORDER  = "#30363d"
ACCENT  = "#238636"   # green
ACCENT2 = "#1f6feb"   # blue
FG      = "#e6edf3"
FG2     = "#8b949e"
RED     = "#f85149"
FONT    = ("Consolas", 10)
FONT_B  = ("Consolas", 10, "bold")
FONT_H  = ("Consolas", 14, "bold")


class PSAEApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PSAE — Presidential Sentiment Alpha Engine")
        self.geometry("1000x700")
        self.minsize(800, 560)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._build_header()
        self._build_notebook()
        self._build_status_bar()

    # ── header ───────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=PANEL, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚡ PSAE", font=("Consolas", 18, "bold"),
                 bg=PANEL, fg=ACCENT).pack(side="left", padx=16)
        tk.Label(hdr, text="Presidential Sentiment Alpha Engine",
                 font=("Consolas", 11), bg=PANEL, fg=FG2).pack(side="left")

        # live clock
        self._clock_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._clock_var, font=FONT,
                 bg=PANEL, fg=FG2).pack(side="right", padx=16)
        self._tick_clock()

    def _tick_clock(self):
        self._clock_var.set(datetime.utcnow().strftime("UTC  %Y-%m-%d  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    # ── notebook tabs ────────────────────────────────────────────────────────
    def _build_notebook(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook",        background=BG,    borderwidth=0)
        style.configure("TNotebook.Tab",    background=PANEL, foreground=FG2,
                        padding=[14, 6],    font=FONT_B)
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", FG)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        nb.add(self._tab_backtest(nb),  text="  📈 Backtest  ")
        nb.add(self._tab_sentiment(nb), text="  🧠 Sentiment  ")
        nb.add(self._tab_ingest(nb),    text="  📡 Ingest  ")
        nb.add(self._tab_log(nb),       text="  📋 Log  ")

    # ── BACKTEST tab ─────────────────────────────────────────────────────────
    def _tab_backtest(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.columnconfigure(1, weight=1)

        row = 0
        def lbl(text, r):
            tk.Label(f, text=text, font=FONT_B, bg=BG, fg=FG2, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(20,8), pady=6)

        lbl("Strategy", row)
        self._strat = ttk.Combobox(f, values=["psae_v1"], state="readonly",
                                   font=FONT, width=20)
        self._strat.set("psae_v1")
        self._strat.grid(row=row, column=1, sticky="w", pady=6); row+=1

        lbl("Start date", row)
        self._start = tk.Entry(f, font=FONT, bg=PANEL, fg=FG,
                               insertbackground=FG, relief="flat", bd=4, width=14)
        self._start.insert(0, (datetime.utcnow()-timedelta(days=365)).strftime("%Y-%m-%d"))
        self._start.grid(row=row, column=1, sticky="w", pady=6); row+=1

        lbl("End date", row)
        self._end = tk.Entry(f, font=FONT, bg=PANEL, fg=FG,
                             insertbackground=FG, relief="flat", bd=4, width=14)
        self._end.insert(0, datetime.utcnow().strftime("%Y-%m-%d"))
        self._end.grid(row=row, column=1, sticky="w", pady=6); row+=1

        lbl("Initial cash ($)", row)
        self._cash = tk.Entry(f, font=FONT, bg=PANEL, fg=FG,
                              insertbackground=FG, relief="flat", bd=4, width=14)
        self._cash.insert(0, "1000000")
        self._cash.grid(row=row, column=1, sticky="w", pady=6); row+=1

        lbl("Signals CSV", row)
        sig_frame = tk.Frame(f, bg=BG)
        sig_frame.grid(row=row, column=1, sticky="ew", pady=6); row+=1
        self._signals = tk.Entry(sig_frame, font=FONT, bg=PANEL, fg=FG,
                                 insertbackground=FG, relief="flat", bd=4, width=34)
        self._signals.insert(0, "(optional — leave blank to use mock)")
        self._signals.pack(side="left")
        tk.Button(sig_frame, text="Browse", font=FONT, bg=PANEL, fg=FG,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._browse_signals).pack(side="left", padx=6)

        lbl("Output file", row)
        self._output = tk.Entry(f, font=FONT, bg=PANEL, fg=FG,
                                insertbackground=FG, relief="flat", bd=4, width=34)
        self._output.insert(0, "results/backtest_result.pkl")
        self._output.grid(row=row, column=1, sticky="w", pady=6); row+=1

        # results panel
        tk.Frame(f, bg=BORDER, height=1).grid(row=row, column=0, columnspan=3,
                                               sticky="ew", padx=16, pady=8); row+=1
        self._bt_result = scrolledtext.ScrolledText(
            f, font=FONT, bg=PANEL, fg=FG, relief="flat", height=10,
            insertbackground=FG, state="disabled")
        self._bt_result.grid(row=row, column=0, columnspan=3,
                             sticky="nsew", padx=16, pady=(0,8))
        f.rowconfigure(row, weight=1); row+=1

        btn_frame = tk.Frame(f, bg=BG)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(0,12))
        tk.Button(btn_frame, text="▶  Run Backtest", font=FONT_B,
                  bg=ACCENT, fg="white", relief="flat", bd=0,
                  padx=20, pady=8, cursor="hand2",
                  command=self._run_backtest).pack()
        return f

    def _browse_signals(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv"),("All","*.*")])
        if path:
            self._signals.delete(0, "end")
            self._signals.insert(0, path)

    def _run_backtest(self):
        self._append_bt("Running backtest…\n")
        args = dict(
            strategy=self._strat.get(),
            start=self._start.get(),
            end=self._end.get(),
            cash=self._cash.get(),
            output=self._output.get(),
            signals=self._signals.get() if "optional" not in self._signals.get() else None
        )
        threading.Thread(target=self._do_backtest, args=(args,), daemon=True).start()

    def _do_backtest(self, args):
        try:
            from psae_backtest.engine.runner import BacktestRunner
            from psae_backtest.strategy.psae_v1 import PSAEv1Strategy
            strat = PSAEv1Strategy()
            runner = BacktestRunner(
                strategy=strat,
                start=args["start"],
                end=args["end"],
                signals_path=args["signals"],
                initial_cash=float(args["cash"])
            )
            results = runner.run()
            msg = (
                f"\n✅ Backtest complete\n"
                f"   Sharpe Ratio : {results.get('sharpe', 'N/A')}\n"
                f"   Max Drawdown : {results.get('max_drawdown', 0):.2%}\n"
                f"   Net Beta     : {results.get('avg_net_beta', 'N/A')}\n"
                f"   Output       : {args['output']}\n"
            )
            self._append_bt(msg)
            self._log(f"Backtest {args['start']}→{args['end']} complete")
        except Exception as e:
            self._append_bt(f"\n❌ Error: {e}\n")
            self._log(f"Backtest error: {e}")

    def _append_bt(self, text):
        self._bt_result.configure(state="normal")
        self._bt_result.insert("end", text)
        self._bt_result.see("end")
        self._bt_result.configure(state="disabled")

    # ── SENTIMENT tab ────────────────────────────────────────────────────────
    def _tab_sentiment(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.columnconfigure(0, weight=1)

        tk.Label(f, text="Paste presidential text to analyse:",
                 font=FONT_B, bg=BG, fg=FG2).pack(anchor="w", padx=16, pady=(16,4))

        self._sent_input = scrolledtext.ScrolledText(
            f, font=FONT, bg=PANEL, fg=FG, relief="flat",
            insertbackground=FG, height=8)
        self._sent_input.pack(fill="x", padx=16, pady=(0,8))

        row2 = tk.Frame(f, bg=BG)
        row2.pack(fill="x", padx=16)
        tk.Label(row2, text="Provider:", font=FONT_B, bg=BG, fg=FG2).pack(side="left")
        self._provider = ttk.Combobox(row2, values=["huggingface_api","local"],
                                      state="readonly", font=FONT, width=18)
        self._provider.set("huggingface_api")
        self._provider.pack(side="left", padx=8)
        tk.Button(row2, text="▶  Analyse", font=FONT_B, bg=ACCENT2, fg="white",
                  relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._run_sentiment).pack(side="left", padx=12)

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=16, pady=10)

        self._sent_result = scrolledtext.ScrolledText(
            f, font=FONT, bg=PANEL, fg=FG, relief="flat",
            insertbackground=FG, height=10, state="disabled")
        self._sent_result.pack(fill="both", expand=True, padx=16, pady=(0,12))
        return f

    def _run_sentiment(self):
        text = self._sent_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty input", "Please enter some text first.")
            return
        provider = self._provider.get()
        self._append_sent(f"Analysing [{provider}]…\n")
        threading.Thread(target=self._do_sentiment,
                         args=(text, provider), daemon=True).start()

    def _do_sentiment(self, text, provider):
        try:
            os.environ["PSAE_SENTIMENT_PROVIDER"] = provider
            from psae_signal.models.sentiment import SentimentModel
            result = SentimentModel().predict(text)
            msg = (
                f"\n📊 Result\n"
                f"   Label  : {result.get('label','?')}\n"
                f"   Score  : {result.get('score',0):.4f}\n\n"
                f"   Input  : {text[:120]}{'…' if len(text)>120 else ''}\n"
            )
            self._append_sent(msg)
            self._log(f"Sentiment: {result.get('label')} ({result.get('score',0):.3f})")
        except Exception as e:
            self._append_sent(f"\n❌ Error: {e}\n")
            self._log(f"Sentiment error: {e}")

    def _append_sent(self, text):
        self._sent_result.configure(state="normal")
        self._sent_result.insert("end", text)
        self._sent_result.see("end")
        self._sent_result.configure(state="disabled")

    # ── INGEST tab ───────────────────────────────────────────────────────────
    def _tab_ingest(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.columnconfigure(1, weight=1)

        def lbl(text, r):
            tk.Label(f, text=text, font=FONT_B, bg=BG, fg=FG2, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(20,8), pady=8)

        lbl("Source", 0)
        self._ingest_src = ttk.Combobox(
            f, values=["federal_register", "white_house"],
            state="readonly", font=FONT, width=22)
        self._ingest_src.set("federal_register")
        self._ingest_src.grid(row=0, column=1, sticky="w", pady=8)

        lbl("Look-back days", 1)
        self._ingest_days = tk.Entry(f, font=FONT, bg=PANEL, fg=FG,
                                     insertbackground=FG, relief="flat", bd=4, width=8)
        self._ingest_days.insert(0, "7")
        self._ingest_days.grid(row=1, column=1, sticky="w", pady=8)

        tk.Button(f, text="▶  Fetch Documents", font=FONT_B,
                  bg=ACCENT, fg="white", relief="flat", bd=0,
                  padx=16, pady=7, cursor="hand2",
                  command=self._run_ingest).grid(row=2, column=0, columnspan=2, pady=12)

        tk.Frame(f, bg=BORDER, height=1).grid(row=3, column=0, columnspan=3,
                                               sticky="ew", padx=16)

        self._ingest_result = scrolledtext.ScrolledText(
            f, font=FONT, bg=PANEL, fg=FG, relief="flat",
            insertbackground=FG, state="disabled")
        self._ingest_result.grid(row=4, column=0, columnspan=3,
                                 sticky="nsew", padx=16, pady=12)
        f.rowconfigure(4, weight=1)
        return f

    def _run_ingest(self):
        src   = self._ingest_src.get()
        days  = int(self._ingest_days.get() or 7)
        self._append_ing(f"Fetching from {src} (last {days} days)…\n")
        threading.Thread(target=self._do_ingest,
                         args=(src, days), daemon=True).start()

    def _do_ingest(self, source, days):
        try:
            if source == "federal_register":
                from psae_ingest.sources.federal_register import FederalRegisterSource
                src = FederalRegisterSource()
            else:
                from psae_ingest.sources.white_house import WhiteHouseSource
                src = WhiteHouseSource()
            docs = src.fetch(days=days)
            lines = [f"\n✅ Fetched {len(docs)} documents\n"]
            for d in docs[:20]:
                lines.append(f"  [{d.get('date','?')}] {d.get('title','?')[:90]}")
            if len(docs) > 20:
                lines.append(f"  … and {len(docs)-20} more")
            self._append_ing("\n".join(lines) + "\n")
            self._log(f"Ingest {source}: {len(docs)} docs fetched")
        except Exception as e:
            self._append_ing(f"\n❌ Error: {e}\n")
            self._log(f"Ingest error: {e}")

    def _append_ing(self, text):
        self._ingest_result.configure(state="normal")
        self._ingest_result.insert("end", text)
        self._ingest_result.see("end")
        self._ingest_result.configure(state="disabled")

    # ── LOG tab ──────────────────────────────────────────────────────────────
    def _tab_log(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)
        self._log_box = scrolledtext.ScrolledText(
            f, font=FONT, bg=BG, fg=FG2, relief="flat",
            insertbackground=FG, state="disabled")
        self._log_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        tk.Button(f, text="Clear log", font=FONT, bg=PANEL, fg=FG2,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._clear_log).grid(row=1, column=0, pady=6)
        return f

    def _log(self, msg):
        ts = datetime.utcnow().strftime("%H:%M:%S")
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{ts}] {msg}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ── status bar ───────────────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = tk.Frame(self, bg=PANEL, height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="PSAE v0.1.0  |  psae-project/psae-backtest",
                 font=("Consolas", 9), bg=PANEL, fg=FG2).pack(side="left", padx=12)
        tk.Label(bar, text="© 2025 PSAE Project",
                 font=("Consolas", 9), bg=PANEL, fg=FG2).pack(side="right", padx=12)


if __name__ == "__main__":
    app = PSAEApp()
    app.mainloop()
