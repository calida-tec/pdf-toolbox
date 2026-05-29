from __future__ import annotations

import glob
from pathlib import Path

from PIL import Image, ImageOps
from pypdf import PdfWriter

PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def expand_patterns(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = [Path(item).resolve() for item in glob.glob(pattern)]
        if matches:
            files.extend(matches)
            continue

        path = Path(pattern).resolve()
        if path.exists():
            files.append(path)
            continue

        raise FileNotFoundError(f"Input not found: {pattern}")
    return files


def collect_from_directory(
    input_dir: str,
    recursive: bool,
    suffixes: set[str] | None = None,
) -> list[Path]:
    base = Path(input_dir).resolve()
    if not base.is_dir():
        raise NotADirectoryError(f"Directory not found: {base}")

    pattern = "**/*" if recursive else "*"
    allowed = {suffix.lower() for suffix in (suffixes or PDF_SUFFIXES)}
    return [
        path.resolve()
        for path in base.glob(pattern)
        if path.is_file() and path.suffix.lower() in allowed
    ]


def sort_paths(paths: list[Path], sort_mode: str) -> list[Path]:
    unique_paths = list(dict.fromkeys(paths))
    if sort_mode == "mtime":
        return sorted(
            unique_paths,
            key=lambda path: (path.stat().st_mtime, str(path).lower()),
        )
    return sorted(unique_paths, key=lambda path: str(path).lower())


def validate_files(
    paths: list[Path],
    output: Path,
    allowed_suffixes: set[str],
    label: str,
) -> list[Path]:
    valid_paths: list[Path] = []
    for path in paths:
        if path.suffix.lower() not in allowed_suffixes:
            raise ValueError(f"Only {label} files are supported: {path}")
        if path == output:
            continue
        valid_paths.append(path)

    if not valid_paths:
        raise ValueError(f"No input {label} files found.")
    return valid_paths


def validate_pdf_inputs(paths: list[Path], output: Path) -> list[Path]:
    return validate_files(paths, output, PDF_SUFFIXES, "PDF")


def validate_image_inputs(paths: list[Path], output: Path) -> list[Path]:
    return validate_files(paths, output, IMAGE_SUFFIXES, "image")


def merge_pdfs(input_paths: list[Path], output_path: Path) -> tuple[int, int]:
    writer = PdfWriter()

    for path in input_paths:
        writer.append(str(path))

    total_pages = len(writer.pages)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as handle:
        writer.write(handle)

    writer.close()
    return len(input_paths), total_pages


def convert_images_to_pdf(input_paths: list[Path], output_path: Path) -> tuple[int, int]:
    prepared_images: list[Image.Image] = []
    source_images: list[Image.Image] = []

    try:
        for path in input_paths:
            source = Image.open(path)
            source_images.append(source)

            image = ImageOps.exif_transpose(source)
            if image.mode in ("RGBA", "LA"):
                canvas = Image.new("RGB", image.size, "white")
                alpha = image.getchannel("A")
                canvas.paste(image.convert("RGBA"), mask=alpha)
                image = canvas
            elif image.mode != "RGB":
                image = image.convert("RGB")

            prepared_images.append(image)

        if not prepared_images:
            raise ValueError("No input image files found.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        first, rest = prepared_images[0], prepared_images[1:]
        first.save(output_path, "PDF", resolution=100.0, save_all=True, append_images=rest)
        return len(input_paths), len(prepared_images)
    finally:
        for image in prepared_images:
            image.close()
        for image in source_images:
            image.close()
