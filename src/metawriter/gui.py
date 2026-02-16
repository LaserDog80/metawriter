"""MetaWriter GUI — ttkbootstrap desktop application with drag-and-drop."""

import json
import threading
import tkinter as tk
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .engine import tag_file, tag_files
from .reader import read_metadata
from .scanner import SUPPORTED_EXTENSIONS, scan_paths

# Try to import tkinterdnd2 for drag-and-drop support.
# Falls back gracefully if not available (browse still works).
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _HAS_DND = True
except ImportError:
    _HAS_DND = False


class MetaWriterApp:
    """Main MetaWriter GUI application."""

    def __init__(self) -> None:
        # Create root window — use TkinterDnD if available for drag-and-drop
        if _HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("MetaWriter")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)

        # Apply ttkbootstrap theme
        self.style = ttk.Style(theme="darkly")

        # Track files and processing state
        self._files: list[Path] = []
        self._processing = False
        self._recursive = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the full UI layout."""
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=BOTH, expand=True)

        self._build_drop_zone(main)
        self._build_file_list(main)
        self._build_metadata_panel(main)
        self._build_action_bar(main)

    # ------------------------------------------------------------------
    # Drop zone + browse
    # ------------------------------------------------------------------

    def _build_drop_zone(self, parent: ttk.Frame) -> None:
        """Build the drop zone with browse button."""
        frame = ttk.Labelframe(parent, text="Add Files", padding=10)
        frame.pack(fill=X, pady=(0, 10))

        # Drop target area
        self._drop_label = ttk.Label(
            frame,
            text="Drag & drop files or folders here" if _HAS_DND else "Use Browse to add files",
            anchor=CENTER,
            font=("TkDefaultFont", 11),
        )
        self._drop_label.pack(fill=X, pady=(0, 8))

        if _HAS_DND:
            # Register the label frame as a drop target
            frame.drop_target_register(DND_FILES)
            frame.dnd_bind("<<Drop>>", self._on_drop)
            self._drop_label.drop_target_register(DND_FILES)
            self._drop_label.dnd_bind("<<Drop>>", self._on_drop)

        # Button row
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=X)

        ttk.Button(
            btn_row, text="Browse Files...", bootstyle=PRIMARY,
            command=self._browse_files,
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Button(
            btn_row, text="Browse Folder...", bootstyle=SECONDARY,
            command=self._browse_folder,
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Checkbutton(
            btn_row, text="Include subfolders",
            variable=self._recursive,
        ).pack(side=LEFT, padx=(10, 0))

        ttk.Button(
            btn_row, text="Clear", bootstyle=DANGER + OUTLINE,
            command=self._clear_files,
        ).pack(side=RIGHT)

    def _on_drop(self, event: object) -> None:
        """Handle drag-and-drop events."""
        data = getattr(event, "data", "")
        paths = self.root.tk.splitlist(data)
        resolved = [Path(p) for p in paths]
        files = scan_paths(resolved, recursive=self._recursive.get())
        self._add_files(files)

    def _browse_files(self) -> None:
        """Open file dialog to select files."""
        from tkinter import filedialog

        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))
        paths = filedialog.askopenfilenames(
            title="Select media files",
            filetypes=[("Media files", exts), ("All files", "*.*")],
        )
        if paths:
            self._add_files([Path(p) for p in paths])

    def _browse_folder(self) -> None:
        """Open folder dialog to select a directory."""
        from tkinter import filedialog

        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            files = scan_paths([Path(folder)], recursive=self._recursive.get())
            self._add_files(files)

    def _add_files(self, files: list[Path]) -> None:
        """Add files to the list, avoiding duplicates."""
        existing = set(self._files)
        for f in files:
            if f not in existing:
                self._files.append(f)
                self._tree.insert(
                    "", END,
                    iid=str(f),
                    values=(f.name, str(f.parent), "pending"),
                )
        self._update_status_label()

    def _clear_files(self) -> None:
        """Clear the file list."""
        self._files.clear()
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._detail_text.config(state=NORMAL)
        self._detail_text.delete("1.0", END)
        self._detail_text.config(state=DISABLED)
        self._update_status_label()

    # ------------------------------------------------------------------
    # File list
    # ------------------------------------------------------------------

    def _build_file_list(self, parent: ttk.Frame) -> None:
        """Build the file list treeview with metadata preview."""
        frame = ttk.Labelframe(parent, text="Files", padding=5)
        frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Treeview
        columns = ("name", "folder", "status")
        self._tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=8,
            selectmode="browse",
        )
        self._tree.heading("name", text="Filename")
        self._tree.heading("folder", text="Folder")
        self._tree.heading("status", text="Status")
        self._tree.column("name", width=200)
        self._tree.column("folder", width=350)
        self._tree.column("status", width=100)
        self._tree.pack(fill=BOTH, expand=True, side=TOP)

        self._tree.bind("<<TreeviewSelect>>", self._on_file_select)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Detail preview
        detail_frame = ttk.Labelframe(frame, text="Existing Metadata (read-only)", padding=5)
        detail_frame.pack(fill=X, pady=(5, 0))

        self._detail_text = tk.Text(
            detail_frame, height=4, wrap=WORD,
            state=DISABLED, font=("TkFixedFont", 10),
        )
        self._detail_text.pack(fill=X)

    def _on_file_select(self, _event: object) -> None:
        """Show existing metadata for the selected file."""
        selected = self._tree.selection()
        if not selected:
            return

        path = Path(selected[0])
        self._detail_text.config(state=NORMAL)
        self._detail_text.delete("1.0", END)

        try:
            meta = read_metadata(path, only_mwrite=True)
            if meta:
                self._detail_text.insert("1.0", json.dumps(meta, indent=2, ensure_ascii=False))
            else:
                self._detail_text.insert("1.0", "(no MetaWriter metadata)")
        except Exception as exc:
            self._detail_text.insert("1.0", f"Error reading: {exc}")

        self._detail_text.config(state=DISABLED)

    # ------------------------------------------------------------------
    # Metadata fields
    # ------------------------------------------------------------------

    def _build_metadata_panel(self, parent: ttk.Frame) -> None:
        """Build optional metadata input fields."""
        frame = ttk.Labelframe(parent, text="Optional Metadata", padding=10)
        frame.pack(fill=X, pady=(0, 10))

        # Model
        ttk.Label(frame, text="Model:").grid(row=0, column=0, sticky=W, padx=(0, 5))
        self._model_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._model_var, width=40).grid(
            row=0, column=1, sticky=EW, pady=2,
        )

        # Source URL
        ttk.Label(frame, text="Source URL:").grid(row=1, column=0, sticky=W, padx=(0, 5))
        self._url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._url_var, width=40).grid(
            row=1, column=1, sticky=EW, pady=2,
        )

        # Prompt
        ttk.Label(frame, text="Prompt:").grid(row=2, column=0, sticky=NW, padx=(0, 5))
        self._prompt_text = tk.Text(frame, height=3, wrap=WORD, font=("TkDefaultFont", 10))
        self._prompt_text.grid(row=2, column=1, sticky=EW, pady=2)

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Action bar
    # ------------------------------------------------------------------

    def _build_action_bar(self, parent: ttk.Frame) -> None:
        """Build the bottom action bar with tag button and progress."""
        frame = ttk.Frame(parent)
        frame.pack(fill=X)

        self._tag_btn = ttk.Button(
            frame, text="Tag All", bootstyle=SUCCESS,
            command=self._start_tagging,
        )
        self._tag_btn.pack(side=LEFT, padx=(0, 10))

        self._progress = ttk.Progressbar(
            frame, mode="determinate", length=300,
        )
        self._progress.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        self._status_label = ttk.Label(frame, text="Ready")
        self._status_label.pack(side=RIGHT)

    def _update_status_label(self) -> None:
        """Update the status label with file count."""
        count = len(self._files)
        if count == 0:
            self._status_label.config(text="Ready")
        else:
            self._status_label.config(text=f"{count} file(s)")

    # ------------------------------------------------------------------
    # Tagging
    # ------------------------------------------------------------------

    def _start_tagging(self) -> None:
        """Start the tagging process in a background thread."""
        if self._processing or not self._files:
            return

        self._processing = True
        self._tag_btn.config(state=DISABLED)
        self._progress["maximum"] = len(self._files)
        self._progress["value"] = 0

        # Gather optional fields
        model = self._model_var.get().strip() or None
        source_url = self._url_var.get().strip() or None
        prompt = self._prompt_text.get("1.0", END).strip() or None

        files = list(self._files)

        thread = threading.Thread(
            target=self._tag_worker,
            args=(files, model, source_url, prompt),
            daemon=True,
        )
        thread.start()

    def _tag_worker(
        self,
        files: list[Path],
        model: str | None,
        source_url: str | None,
        prompt: str | None,
    ) -> None:
        """Worker thread that tags files."""
        tagged_count = 0
        for i, file_path in enumerate(files):
            try:
                tag_file(
                    file_path,
                    model=model,
                    source_url=source_url,
                    prompt=prompt,
                )
                tagged_count += 1
                self.root.after(0, self._update_file_status, file_path, "done", i + 1)
            except Exception as exc:
                self.root.after(
                    0, self._update_file_status, file_path, f"error: {exc}", i + 1,
                )

        self.root.after(0, self._tagging_done, tagged_count, len(files))

    def _update_file_status(self, path: Path, status: str, progress: int) -> None:
        """Update a file's status in the treeview (called from main thread)."""
        iid = str(path)
        if self._tree.exists(iid):
            self._tree.set(iid, "status", status)
        self._progress["value"] = progress
        self._status_label.config(text=f"Processing {progress} of {len(self._files)}...")

    def _tagging_done(self, tagged: int, total: int) -> None:
        """Called when tagging is complete."""
        self._processing = False
        self._tag_btn.config(state=NORMAL)
        self._status_label.config(text=f"Done. {tagged}/{total} file(s) tagged.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def mainloop(self) -> None:
        """Start the Tk event loop."""
        self.root.mainloop()
