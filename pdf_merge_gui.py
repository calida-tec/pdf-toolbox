from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pdf_merge_core import (
    IMAGE_SUFFIXES,
    collect_from_directory,
    convert_images_to_pdf,
    merge_pdfs,
    validate_image_inputs,
    validate_pdf_inputs,
)


class FileJobFrame(ttk.Frame):
    def __init__(
        self,
        master: ttk.Notebook,
        *,
        title: str,
        subtitle: str,
        add_file_text: str,
        add_dir_text: str,
        filetypes: list[tuple[str, str]],
        suffixes: set[str],
        output_filename: str,
        status_ready: str,
        status_label: str,
        import_label: str,
        start_button_text: str,
        directory_title: str,
        merge_title: str,
        success_title: str,
        success_template: str,
        processor,
        validator,
    ) -> None:
        super().__init__(master, padding=16)
        self.filetypes = filetypes
        self.suffixes = suffixes
        self.output_filename = output_filename
        self.status_label = status_label
        self.import_label = import_label
        self.start_button_text = start_button_text
        self.directory_title = directory_title
        self.merge_title = merge_title
        self.success_title = success_title
        self.success_template = success_template
        self.processor = processor
        self.validator = validator

        self.files: list[Path] = []
        self.output_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value=status_ready)

        title_label = ttk.Label(self, text=title, font=("Microsoft YaHei UI", 16, "bold"))
        title_label.pack(anchor="w")

        subtitle_label = ttk.Label(self, text=subtitle)
        subtitle_label.pack(anchor="w", pady=(4, 12))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text=add_file_text, command=self.add_files).pack(side="left")
        ttk.Button(toolbar, text=add_dir_text, command=self.add_directory).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="上移", command=self.move_up).pack(side="left", padx=(24, 0))
        ttk.Button(toolbar, text="下移", command=self.move_down).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="移除选中", command=self.remove_selected).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="清空列表", command=self.clear_all).pack(side="left", padx=(8, 0))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=("Consolas", 10),
            activestyle="dotbox",
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        options = ttk.Frame(self)
        options.pack(fill="x", pady=(10, 8))

        ttk.Checkbutton(
            options,
            text="目录导入时递归扫描子目录",
            variable=self.recursive_var,
        ).pack(side="left")
        ttk.Checkbutton(
            options,
            text="输出文件已存在时允许覆盖",
            variable=self.overwrite_var,
        ).pack(side="left", padx=(18, 0))

        output_row = ttk.Frame(self)
        output_row.pack(fill="x", pady=(0, 8))

        ttk.Label(output_row, text="输出文件").pack(side="left")
        ttk.Entry(output_row, textvariable=self.output_var).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 8),
        )
        ttk.Button(output_row, text="选择位置", command=self.choose_output).pack(side="left")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(6, 0))

        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")
        ttk.Button(bottom, text=start_button_text, command=self.run_job).pack(side="right")

    def refresh_list(self, keep_selection: list[int] | None = None) -> None:
        self.listbox.delete(0, tk.END)
        for index, path in enumerate(self.files, start=1):
            self.listbox.insert(tk.END, f"{index:02d}. {path}")

        if keep_selection:
            for index in keep_selection:
                if 0 <= index < len(self.files):
                    self.listbox.selection_set(index)

        self.status_var.set(f"当前已选择 {len(self.files)} 个{self.status_label}。")

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title=f"选择{self.status_label}",
            filetypes=self.filetypes,
        )
        if not selected:
            return

        for item in selected:
            path = Path(item).resolve()
            if path not in self.files and path.suffix.lower() in self.suffixes:
                self.files.append(path)

        self.refresh_list()

    def add_directory(self) -> None:
        selected_dir = filedialog.askdirectory(title=self.directory_title)
        if not selected_dir:
            return

        try:
            files = collect_from_directory(
                selected_dir,
                self.recursive_var.get(),
                suffixes=self.suffixes,
            )
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))
            return

        added = 0
        for path in sorted(files, key=lambda item: str(item).lower()):
            if path not in self.files:
                self.files.append(path)
                added += 1

        self.refresh_list()
        self.status_var.set(f"从目录导入了 {added} 个{self.import_label}。")

    def remove_selected(self) -> None:
        selected = list(self.listbox.curselection())
        if not selected:
            return

        for index in reversed(selected):
            del self.files[index]

        self.refresh_list()

    def clear_all(self) -> None:
        self.files.clear()
        self.refresh_list()

    def move_up(self) -> None:
        selected = list(self.listbox.curselection())
        if not selected or selected[0] == 0:
            return

        for index in selected:
            self.files[index - 1], self.files[index] = self.files[index], self.files[index - 1]

        self.refresh_list([index - 1 for index in selected])

    def move_down(self) -> None:
        selected = list(self.listbox.curselection())
        if not selected or selected[-1] == len(self.files) - 1:
            return

        for index in reversed(selected):
            self.files[index + 1], self.files[index] = self.files[index], self.files[index + 1]

        self.refresh_list([index + 1 for index in selected])

    def choose_output(self) -> None:
        target = filedialog.asksaveasfilename(
            title="选择输出 PDF 文件",
            initialfile=self.output_filename,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if target:
            self.output_var.set(target)

    def run_job(self) -> None:
        try:
            output_text = self.output_var.get().strip()
            if not output_text:
                raise ValueError("请先选择输出文件。")

            output_path = Path(output_text).resolve()
            if output_path.exists() and not self.overwrite_var.get():
                raise FileExistsError("输出文件已存在，请勾选覆盖选项或更换输出路径。")

            input_paths = self.validator(self.files, output_path)
            file_count, page_count = self.processor(input_paths, output_path)
        except Exception as exc:
            messagebox.showerror(self.merge_title, str(exc))
            return

        self.status_var.set(f"完成：{file_count} 个{self.import_label}，{page_count} 页。")
        messagebox.showinfo(
            self.success_title,
            self.success_template.format(
                output=output_path,
                file_count=file_count,
                page_count=page_count,
            ),
        )


class PdfToolApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF 工具箱")
        self.root.geometry("960x620")
        self.root.minsize(780, 520)
        self._build_layout()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        pdf_tab = FileJobFrame(
            notebook,
            title="PDF 合并",
            subtitle="添加多个 PDF 文件，调整顺序后合并成一个新 PDF。",
            add_file_text="添加 PDF",
            add_dir_text="导入 PDF 目录",
            filetypes=[("PDF files", "*.pdf")],
            suffixes={".pdf"},
            output_filename="merged.pdf",
            status_ready="添加 PDF 文件后即可开始合并。",
            status_label="PDF 文件",
            import_label="PDF 文件",
            start_button_text="开始合并",
            directory_title="选择包含 PDF 的目录",
            merge_title="合并失败",
            success_title="合并成功",
            success_template=(
                "已生成文件：\n{output}\n\n合并文件数：{file_count}\n总页数：{page_count}"
            ),
            processor=merge_pdfs,
            validator=validate_pdf_inputs,
        )

        image_tab = FileJobFrame(
            notebook,
            title="图片转 PDF",
            subtitle="添加多张图片，调整顺序后导出为一个多页 PDF。",
            add_file_text="添加图片",
            add_dir_text="导入图片目录",
            filetypes=[
                ("Image files", "*.bmp *.gif *.jpeg *.jpg *.png *.tif *.tiff *.webp"),
            ],
            suffixes=IMAGE_SUFFIXES,
            output_filename="images.pdf",
            status_ready="添加图片后即可开始生成 PDF。",
            status_label="图片",
            import_label="图片",
            start_button_text="开始转换",
            directory_title="选择包含图片的目录",
            merge_title="转换失败",
            success_title="转换成功",
            success_template=(
                "已生成 PDF：\n{output}\n\n图片数量：{file_count}\n总页数：{page_count}"
            ),
            processor=convert_images_to_pdf,
            validator=validate_image_inputs,
        )

        notebook.add(pdf_tab, text="PDF 合并")
        notebook.add(image_tab, text="图片转 PDF")


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    PdfToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
