from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from processor import ProcessConfig, process_folder


def discover_python_candidates() -> list[str]:
    candidates = []

    current = sys.executable
    if current:
        candidates.append(current)

    for name in ["python", "python3", "py"]:
        path = shutil.which(name)
        if path:
            candidates.append(path)

    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        venv_python = str(Path(venv) / ("Scripts" if os.name == "nt" else "bin") / "python")
        if Path(venv_python).exists():
            candidates.append(venv_python)

    # dedupe while preserving order
    unique = []
    seen = set()
    for c in candidates:
        if c not in seen:
            unique.append(c)
            seen.add(c)
    return unique


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("人物抠图工具")
        self.geometry("720x420")

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.random_enabled = tk.BooleanVar(value=False)
        self.random_count = tk.IntVar(value=10)
        self.status_var = tk.StringVar(value="就绪")

        self.python_candidates = discover_python_candidates()
        self.python_var = tk.StringVar(value=self.python_candidates[0] if self.python_candidates else sys.executable)

        self._build()

    def _build(self) -> None:
        pad = {"padx": 8, "pady": 6}

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(frame, text="输入文件夹:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(frame, text="浏览", command=self._pick_input).grid(row=0, column=2, **pad)

        ttk.Label(frame, text="输出文件夹:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(frame, text="浏览", command=self._pick_output).grid(row=1, column=2, **pad)

        ttk.Label(frame, text="Python环境:").grid(row=2, column=0, sticky="w", **pad)
        combo = ttk.Combobox(frame, textvariable=self.python_var, values=self.python_candidates, state="readonly")
        combo.grid(row=2, column=1, sticky="ew", **pad)

        ttk.Checkbutton(
            frame,
            text="随机抽取",
            variable=self.random_enabled,
            command=self._on_random_toggle,
        ).grid(row=3, column=0, sticky="w", **pad)

        ttk.Label(frame, text="数量:").grid(row=3, column=1, sticky="w", padx=8, pady=6)
        self.count_spin = ttk.Spinbox(frame, from_=1, to=100000, textvariable=self.random_count, width=10)
        self.count_spin.grid(row=3, column=1, sticky="e", padx=8, pady=6)
        self.count_spin.configure(state="disabled")

        self.progress = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)

        ttk.Label(frame, textvariable=self.status_var).grid(row=5, column=0, columnspan=3, sticky="w", **pad)

        ttk.Button(frame, text="开始处理", command=self._start).grid(row=6, column=0, columnspan=3, pady=18)

        frame.columnconfigure(1, weight=1)

    def _pick_input(self) -> None:
        value = filedialog.askdirectory()
        if value:
            self.input_var.set(value)

    def _pick_output(self) -> None:
        value = filedialog.askdirectory()
        if value:
            self.output_var.set(value)

    def _on_random_toggle(self) -> None:
        self.count_spin.configure(state="normal" if self.random_enabled.get() else "disabled")

    def _start(self) -> None:
        input_dir = Path(self.input_var.get().strip())
        output_dir = Path(self.output_var.get().strip())

        if not input_dir.exists() or not input_dir.is_dir():
            messagebox.showerror("错误", "输入文件夹不存在")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        cfg = ProcessConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            random_pick_enabled=self.random_enabled.get(),
            random_pick_count=int(self.random_count.get()),
        )

        self.progress["value"] = 0
        self.status_var.set("处理中...")

        threading.Thread(target=self._run_process, args=(cfg,), daemon=True).start()

    def _run_process(self, cfg: ProcessConfig) -> None:
        def cb(i, total, name, stats):
            self.after(0, lambda: self._update_progress(i, total, name, stats))

        stats = process_folder(cfg, progress_callback=cb)
        self.after(0, lambda: self._done(stats))

    def _update_progress(self, i, total, name, stats) -> None:
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = i
        self.status_var.set(
            f"处理中 {i}/{total}: {name} | 成功 {stats.success} 跳过 {stats.skipped} 失败 {stats.failed}"
        )

    def _done(self, stats) -> None:
        self.status_var.set(
            f"完成: 总计 {stats.total}，成功 {stats.success}，跳过 {stats.skipped}，失败 {stats.failed}"
        )
        messagebox.showinfo("完成", self.status_var.get())


if __name__ == "__main__":
    App().mainloop()
