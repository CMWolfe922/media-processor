from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import UnidentifiedImageError

from media_processor import (
    DockerKeywordAnalyzer,
    FilenameKeywordAnalyzer,
    ImageProcessor,
    PLATFORM_RATIO_CHOICES,
    SafeKeywordAnalyzer,
    SUPPORTED_PLATFORMS,
)


class MediaProcessorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Media Processor")
        self.root.geometry("760x420")

        self.selected_files: tuple[str, ...] = ()
        analyzer = SafeKeywordAnalyzer(
            primary=DockerKeywordAnalyzer(),
            fallback=FilenameKeywordAnalyzer(),
        )
        self.processor = ImageProcessor(base_dir=Path(__file__).parent, analyzer=analyzer)

        self.platform_var = tk.StringVar(value="Website")
        self.ratio_var = tk.StringVar(value="Original")
        self.format_var = tk.StringVar(value="webp")

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame, text="Select Photos", command=self.select_files).grid(
            row=0, column=0, sticky="w"
        )
        self.file_label = ttk.Label(frame, text="No files selected")
        self.file_label.grid(row=0, column=1, padx=12, sticky="w")

        ttk.Label(frame, text="Usage Target").grid(row=1, column=0, pady=(16, 8), sticky="w")
        platform_menu = ttk.Combobox(
            frame,
            textvariable=self.platform_var,
            values=SUPPORTED_PLATFORMS,
            state="readonly",
            width=24,
        )
        platform_menu.grid(row=1, column=1, sticky="w")
        platform_menu.bind("<<ComboboxSelected>>", self._on_platform_changed)

        ttk.Label(frame, text="Crop Ratio").grid(row=2, column=0, pady=(8, 8), sticky="w")
        self.ratio_menu = ttk.Combobox(frame, textvariable=self.ratio_var, state="readonly", width=24)
        self.ratio_menu.grid(row=2, column=1, sticky="w")
        self._on_platform_changed()

        ttk.Label(frame, text="Output Format").grid(row=3, column=0, pady=(8, 8), sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.format_var,
            values=["webp", "jpg", "png"],
            state="readonly",
            width=24,
        ).grid(row=3, column=1, sticky="w")

        ttk.Button(frame, text="Process Photos", command=self.process).grid(
            row=4, column=0, pady=(24, 0), sticky="w"
        )

    def _on_platform_changed(self, _event: object | None = None) -> None:
        platform = self.platform_var.get()
        choices = PLATFORM_RATIO_CHOICES.get(platform, ["Original"])
        self.ratio_menu["values"] = choices
        self.ratio_var.set(choices[0])

    def select_files(self) -> None:
        self.selected_files = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")],
        )
        count = len(self.selected_files)
        self.file_label.configure(text=f"{count} files selected" if count else "No files selected")

    def process(self) -> None:
        if not self.selected_files:
            messagebox.showwarning("No files selected", "Please choose at least one image.")
            return

        try:
            output = self.processor.process_images(
                image_paths=[Path(item) for item in self.selected_files],
                platform=self.platform_var.get(),
                ratio_label=self.ratio_var.get(),
                output_format=self.format_var.get(),
            )
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            messagebox.showerror("Processing failed", str(exc))
            return

        messagebox.showinfo("Done", f"Processed {len(output)} file(s).")


if __name__ == "__main__":
    root = tk.Tk()
    MediaProcessorApp(root)
    root.mainloop()
