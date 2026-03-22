from __future__ import annotations

import logging
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from app.config import Settings
from app.runtime import BotRuntime
from utils.logging_utils import configure_logging

ENV_PATH = Path('.env')


class TkLogHandler(logging.Handler):
    def __init__(self, sink: queue.Queue[str]):
        super().__init__()
        self.sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.sink.put_nowait(self.format(record))
        except Exception:  # noqa: BLE001
            pass


def load_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        out[k.strip()] = v.strip()
    return out


def save_env_file(values: dict[str, str], path: Path = ENV_PATH) -> None:
    existing = load_env_file(path)
    existing.update(values)
    lines = [f"{k}={v}" for k, v in sorted(existing.items())]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


class ControlPanelApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('AutoBetBot Control Panel')
        self.root.geometry('980x650')

        self.runtime: BotRuntime | None = None
        self.runtime_thread: threading.Thread | None = None
        self.status_var = tk.StringVar(value='Stopped')
        self.snapshot_vars = {
            'discovered_count': tk.StringVar(value='0'),
            'candidate_count': tk.StringVar(value='0'),
            'open_positions': tk.StringVar(value='0'),
            'deployed': tk.StringVar(value='0.00'),
            'realized_pnl': tk.StringVar(value='0.00'),
            'last_error': tk.StringVar(value=''),
        }

        self.settings_fields: dict[str, tk.StringVar] = {}
        self.key_fields: dict[str, tk.StringVar] = {}
        self.mode_var = tk.StringVar(value='paper')

        self.book_tree: ttk.Treeview | None = None
        self.log_text: tk.Text | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()

        self._build_ui()
        self._wire_log_capture()
        self._load_existing_settings()
        self._refresh_status_loop()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        overview_tab = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        keys_tab = ttk.Frame(notebook)
        books_tab = ttk.Frame(notebook)
        logs_tab = ttk.Frame(notebook)

        notebook.add(overview_tab, text='Overview')
        notebook.add(settings_tab, text='Settings')
        notebook.add(keys_tab, text='Polymarket Keys')
        notebook.add(books_tab, text='Books Monitor')
        notebook.add(logs_tab, text='Logs')

        self._build_overview(overview_tab)
        self._build_settings(settings_tab)
        self._build_keys(keys_tab)
        self._build_books(books_tab)
        self._build_logs(logs_tab)

    def _build_overview(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text='Bot status:', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(8, 2), padx=8)
        ttk.Label(parent, textvariable=self.status_var).pack(anchor='w', padx=8)

        grid = ttk.Frame(parent)
        grid.pack(fill='x', padx=8, pady=8)
        for idx, key in enumerate(['discovered_count', 'candidate_count', 'open_positions', 'deployed', 'realized_pnl', 'last_error']):
            ttk.Label(grid, text=f"{key.replace('_', ' ').title()}:").grid(row=idx, column=0, sticky='w', pady=2)
            ttk.Label(grid, textvariable=self.snapshot_vars[key]).grid(row=idx, column=1, sticky='w', pady=2)

        btns = ttk.Frame(parent)
        btns.pack(fill='x', padx=8, pady=16)
        ttk.Button(btns, text='Start Bot', command=self.start_bot).pack(side='left', padx=6)
        ttk.Button(btns, text='Stop Bot', command=self.stop_bot).pack(side='left', padx=6)

    def _build_settings(self, parent: ttk.Frame) -> None:
        fields = [
            ('BANKROLL', 'Bankroll'),
            ('MAX_POSITION_SIZE_DOLLARS', 'Risk Size ($)'),
            ('MAX_POSITION_SIZE_FRACTION', 'Risk Size Fraction'),
            ('TP_PRICE', 'Take Profit'),
            ('SL_PRICE', 'Stop Loss'),
            ('MAX_OPEN_POSITIONS_GLOBAL', 'Max Open Positions (Global)'),
            ('MAX_CAPITAL_DEPLOYED_FRACTION', 'Max Capital Deployed Fraction'),
        ]
        frm = ttk.Frame(parent)
        frm.pack(fill='x', padx=12, pady=12)

        ttk.Label(frm, text='Mode').grid(row=0, column=0, sticky='w', pady=4)
        ttk.Combobox(frm, textvariable=self.mode_var, values=['paper', 'live'], state='readonly', width=25).grid(row=0, column=1, sticky='w', pady=4)

        for row, (key, label) in enumerate(fields, start=1):
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky='w', pady=4)
            var = tk.StringVar()
            self.settings_fields[key] = var
            ttk.Entry(frm, textvariable=var, width=28).grid(row=row, column=1, sticky='w', pady=4)

        ttk.Button(parent, text='Save Settings', command=self.save_settings).pack(anchor='w', padx=12, pady=8)

    def _build_keys(self, parent: ttk.Frame) -> None:
        fields = [
            ('POLYMARKET_API_KEY', 'API Key'),
            ('POLYMARKET_API_SECRET', 'API Secret'),
            ('POLYMARKET_PASSPHRASE', 'Passphrase'),
        ]
        frm = ttk.Frame(parent)
        frm.pack(fill='x', padx=12, pady=12)

        for row, (key, label) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky='w', pady=4)
            var = tk.StringVar()
            self.key_fields[key] = var
            ttk.Entry(frm, textvariable=var, width=40, show='*').grid(row=row, column=1, sticky='w', pady=4)

        ttk.Button(parent, text='Save Keys', command=self.save_keys).pack(anchor='w', padx=12, pady=8)

    def _build_books(self, parent: ttk.Frame) -> None:
        columns = ('asset', 'horizon', 'yes_bid', 'yes_ask', 'yes_mid', 'no_bid', 'no_ask', 'no_mid')
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=14)
        for col in columns:
            tree.heading(col, text=col.upper())
            tree.column(col, width=100 if col not in {'asset', 'horizon'} else 80)
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.book_tree = tree

    def _build_logs(self, parent: ttk.Frame) -> None:
        text = tk.Text(parent, wrap='none', height=20)
        yscroll = ttk.Scrollbar(parent, orient='vertical', command=text.yview)
        xscroll = ttk.Scrollbar(parent, orient='horizontal', command=text.xview)
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        text.grid(row=0, column=0, sticky='nsew')
        yscroll.grid(row=0, column=1, sticky='ns')
        xscroll.grid(row=1, column=0, sticky='ew')
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.log_text = text

    def _wire_log_capture(self) -> None:
        handler = TkLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s'))
        logging.getLogger().addHandler(handler)

    def _load_existing_settings(self) -> None:
        values = load_env_file()
        defaults = {
            'BANKROLL': '2000',
            'MAX_POSITION_SIZE_DOLLARS': '150',
            'MAX_POSITION_SIZE_FRACTION': '0.05',
            'TP_PRICE': '0.95',
            'SL_PRICE': '0.75',
            'MAX_OPEN_POSITIONS_GLOBAL': '4',
            'MAX_CAPITAL_DEPLOYED_FRACTION': '0.4',
            'MODE': 'paper',
        }
        self.mode_var.set(values.get('MODE', defaults['MODE']))
        for key, var in self.settings_fields.items():
            var.set(values.get(key, defaults.get(key, '')))
        for key, var in self.key_fields.items():
            var.set(values.get(key, ''))

    def save_settings(self) -> None:
        values = {k: v.get().strip() for k, v in self.settings_fields.items()}
        values['MODE'] = self.mode_var.get().strip()
        save_env_file(values)
        messagebox.showinfo('Saved', 'Settings saved to .env')

    def save_keys(self) -> None:
        save_env_file({k: v.get().strip() for k, v in self.key_fields.items()})
        messagebox.showinfo('Saved', 'Polymarket keys saved to .env')

    def _apply_env_to_process(self) -> None:
        for k, v in load_env_file().items():
            os.environ[k] = v

    def start_bot(self) -> None:
        if self.runtime_thread and self.runtime_thread.is_alive():
            messagebox.showwarning('Running', 'Bot is already running')
            return

        self._apply_env_to_process()
        settings = Settings.from_env()
        configure_logging(settings.log_level)
        self.runtime = BotRuntime(settings)
        self.runtime_thread = threading.Thread(target=self.runtime.run, daemon=True)
        self.runtime_thread.start()
        self.status_var.set(f'Running ({settings.mode.value})')

    def stop_bot(self) -> None:
        if self.runtime:
            self.runtime.stop()
        self.status_var.set('Stopped')

    def _refresh_books_table(self, rows: list[dict[str, float | str]]) -> None:
        if not self.book_tree:
            return
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
        ordered = sorted(rows, key=lambda x: str(x.get('asset', '')))
        for row in ordered:
            self.book_tree.insert('', 'end', values=(
                row.get('asset', ''),
                row.get('horizon', ''),
                row.get('yes_bid', ''),
                row.get('yes_ask', ''),
                row.get('yes_mid', ''),
                row.get('no_bid', ''),
                row.get('no_ask', ''),
                row.get('no_mid', ''),
            ))

    def _flush_log_queue(self) -> None:
        if not self.log_text:
            return
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.insert('end', line + '\n')
            self.log_text.see('end')

    def _refresh_status_loop(self) -> None:
        if self.runtime:
            snap = self.runtime.snapshot()
            self.snapshot_vars['discovered_count'].set(str(snap['discovered_count']))
            self.snapshot_vars['candidate_count'].set(str(snap['candidate_count']))
            self.snapshot_vars['open_positions'].set(str(snap['open_positions']))
            self.snapshot_vars['deployed'].set(f"{float(snap['deployed']):.2f}")
            self.snapshot_vars['realized_pnl'].set(f"{float(snap['realized_pnl']):.2f}")
            self.snapshot_vars['last_error'].set(str(snap['last_error']))
            self._refresh_books_table(snap.get('books', []))

        self._flush_log_queue()
        self.root.after(1000, self._refresh_status_loop)


def main() -> None:
    root = tk.Tk()
    app = ControlPanelApp(root)
    root.protocol('WM_DELETE_WINDOW', lambda: (app.stop_bot(), root.destroy()))
    root.mainloop()


if __name__ == '__main__':
    main()
