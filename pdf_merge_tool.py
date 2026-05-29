from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdf_merge_core import (
    collect_from_directory,
    expand_patterns,
    merge_pdfs,
    sort_paths,
    validate_pdf_inputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge multiple PDF files into a single output file."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="PDF files or glob patterns, for example: a.pdf b.pdf docs\\*.pdf",
    )
    parser.add_argument(
        "-d",
        "--input-dir",
        help="Merge all PDF files in a directory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output PDF path.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subdirectories when --input-dir is used.",
    )
    parser.add_argument(
        "--sort",
        choices=("name", "mtime"),
        default="name",
        help="Sort order when collecting files from patterns or directories.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        collected: list[Path] = []
        if args.inputs:
            collected.extend(expand_patterns(args.inputs))
        if args.input_dir:
            collected.extend(collect_from_directory(args.input_dir, args.recursive))

        output_path = Path(args.output).resolve()
        if output_path.exists() and not args.overwrite:
            raise FileExistsError(
                f"Output already exists: {output_path}. Use --overwrite to replace it."
            )

        input_paths = validate_pdf_inputs(sort_paths(collected, args.sort), output_path)
        file_count, page_count = merge_pdfs(input_paths, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Merged {file_count} PDF files into: {output_path}")
    print(f"Total pages: {page_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
