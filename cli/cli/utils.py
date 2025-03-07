from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()

def get_file_extensions(directory: Path) -> set[str]:
    extensions = set()
    for file in directory.glob("**/*"):
        if file.is_file():
            extensions.add(file.suffix.lower())
    return extensions

def find_documents(directory: Path, extensions: list[str] = None) -> list[Path]:
    if extensions is None:
        extensions = [
            ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf",
            ".html", ".htm", ".xml", ".csv", ".json"
        ]

    files = []
    for ext in extensions:
        files.extend(directory.glob(f"**/*{ext}"))

    return sorted(files)

def format_file_size(size_in_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_in_bytes < 1024.0 or unit == "GB":
            break
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} {unit}"

def display_document_table(documents: list[Path]):
    table = Table(title="Documents Found")
    table.add_column("Index", style="cyan")
    table.add_column("Document", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Type", style="blue")

    for i, doc in enumerate(documents, 1):
        table.add_row(
            str(i),
            str(doc),
            format_file_size(doc.stat().st_size),
            doc.suffix.lstrip(".")
        )

    console.print(table)

def parse_key_values(items: list[str]) -> dict[str, Any]:
    result = {}
    for item in items:
        if "=" in item:
            key, value = item.split("=", 1)
            try:
                if value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    value = float(value)
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
            except (ValueError, TypeError):
                pass

            result[key] = value
    return result
