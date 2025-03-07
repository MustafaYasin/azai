from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from cli.app import app
from cli.settings import settings
from cli.utils import console, display_document_table
from rag.chunking import DocumentChunker
from rag.extraction import DocumentExtractor

# Create extract command group
extract_app = typer.Typer(name="extract", help="Extract content from various sources")
app.add_typer(extract_app)

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    ALL = "all"

@extract_app.command("file")
def extract_file(
        file_path: Annotated[Path, typer.Argument(..., help="Path to the file to extract")],
        chunk: Annotated[bool, typer.Option(True, help="Automatically chunk the extracted content")] = True,
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
):
    """Extract content from a single file."""
    try:
        console.print(f"Extracting content from file: [bold]{file_path}[/bold]")

        extractor = DocumentExtractor()
        result = extractor.extract_from_file(file_path)

        console.print(f"Extracted document: [bold]{result['metadata']['title']}[/bold]")

        if chunk:
            chunker = DocumentChunker(
                max_tokens=max_tokens or settings.max_tokens
            )
            if 'document' in result and hasattr(result['document'], 'title'):
                # It's a docling document
                chunks = chunker.chunk_docling_document(result['document'])
                source = result['metadata']['title'] or file_path.name
                num_chunks = chunker.store_chunks(chunks, source, is_docling=True)
                console.print(f"Created and stored [bold green]{num_chunks}[/bold green] chunks")
            else:
                # It's regular text
                chunks = chunker.chunk_text(result['markdown'])
                source = result['metadata']['title'] or file_path.name
                num_chunks = chunker.store_chunks(chunks, source, is_docling=False)
                console.print(f"Created and stored [bold green]{num_chunks}[/bold green] chunks")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@extract_app.command("directory")
def extract_directory(
        directory: Annotated[Path, typer.Argument(..., help="Directory containing documents to extract")],
        file_type: Annotated[FileType, typer.Option(FileType.ALL, help="Type of files to extract")] = FileType.ALL,
        recursive: Annotated[bool, typer.Option(True, help="Search recursively in subdirectories")] = True,
        chunk: Annotated[bool, typer.Option(True, help="Automatically chunk the extracted content")] = True,
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
        skip_errors: Annotated[bool, typer.Option(False, help="Continue processing files if an error occurs")] = False,
):
    """Extract content from all documents in a directory."""
    if not directory.exists() or not directory.is_dir():
        console.print(f"[bold red]Error:[/bold red] {directory} is not a valid directory", style="red")
        raise typer.Exit(1)

    # Get file extensions based on type
    extensions = []
    if file_type == FileType.ALL:
        extensions = [".pdf", ".docx", ".doc", ".txt", ".md", ".rtf", ".html", ".htm", ".xml"]
    else:
        extensions = [f".{file_type.value}"]

    # Find all matching documents
    pattern = "**/*" if recursive else "*"
    documents = []
    for ext in extensions:
        documents.extend(directory.glob(f"{pattern}{ext}"))

    documents = sorted(documents)

    if not documents:
        console.print(f"[bold yellow]No matching documents found in {directory}[/bold yellow]")
        raise typer.Exit(0)

    # Display found documents
    display_document_table(documents)

    # Confirm with user
    if not typer.confirm(f"Process {len(documents)} document(s)?", default=True):
        raise typer.Exit(0)

    # Process documents
    extractor = DocumentExtractor()
    chunker = DocumentChunker(max_tokens=max_tokens or settings.max_tokens)
    total_chunks = 0
    processed = 0

    with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
    ) as progress:
        task = progress.add_task(f"Processing {len(documents)} documents", total=len(documents))

        for doc in documents:
            try:
                progress.update(task, description=f"Processing {doc.name}")

                result = extractor.extract_from_file(doc)

                if chunk:
                    if 'document' in result and hasattr(result['document'], 'title'):
                        # It's a docling document
                        chunks = chunker.chunk_docling_document(result['document'])
                        source = result['metadata']['title'] or doc.name
                        num_chunks = chunker.store_chunks(chunks, source, is_docling=True)
                    else:
                        # It's regular text
                        chunks = chunker.chunk_text(result['markdown'])
                        source = result['metadata']['title'] or doc.name
                        num_chunks = chunker.store_chunks(chunks, source, is_docling=False)

                    total_chunks += num_chunks

                processed += 1
                progress.advance(task)

            except Exception as e:
                console.print(f"[bold red]Error processing {doc.name}:[/bold red] {e}", style="red")
                if not skip_errors:
                    raise typer.Exit(1)

    console.print(f"[bold green]Successfully processed {processed}/{len(documents)} documents[/bold green]")
    if chunk:
        console.print(f"[bold green]Created and stored {total_chunks} chunks[/bold green]")

@extract_app.command("url")
def extract_url(
        url: Annotated[str, typer.Argument(..., help="URL to extract content from")],
        chunk: Annotated[bool, typer.Option(True, help="Automatically chunk the extracted content")] = True,
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
):
    """Extract content from a URL."""
    try:
        console.print(f"Extracting content from URL: [bold]{url}[/bold]")

        extractor = DocumentExtractor()
        result = extractor.extract_from_url(url)

        console.print(f"Extracted document: [bold]{result['metadata']['title']}[/bold]")

        if chunk:
            chunker = DocumentChunker(
                max_tokens=max_tokens or settings.max_tokens
            )
            chunks = chunker.chunk_docling_document(result['document'])
            source = result['metadata']['title'] or url
            num_chunks = chunker.store_chunks(chunks, source, is_docling=True)
            console.print(f"Created and stored [bold green]{num_chunks}[/bold green] chunks")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@extract_app.command("sitemap")
def extract_sitemap(
        base_url: Annotated[str, typer.Argument(..., help="Base URL of the website with sitemap")],
        chunk: Annotated[bool, typer.Option(True, help="Automatically chunk the extracted content")] = True,
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
):
    """Extract content from a website using its sitemap."""
    try:
        console.print(f"Extracting content from sitemap at: [bold]{base_url}[/bold]")

        extractor = DocumentExtractor()
        results = extractor.extract_from_sitemap(base_url)

        if not results:
            console.print("[bold yellow]No documents found in sitemap[/bold yellow]")
            return

        console.print(f"Extracted [bold]{len(results)}[/bold] documents")

        if chunk and results:
            chunker = DocumentChunker(
                max_tokens=max_tokens or settings.max_tokens
            )
            total_chunks = 0

            with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}[/bold blue]"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console
            ) as progress:
                task = progress.add_task(f"Processing {len(results)} documents", total=len(results))

                for result in results:
                    progress.update(task, description=f"Processing {result['metadata']['title']}")
                    chunks = chunker.chunk_docling_document(result['document'])
                    source = result['metadata']['title'] or result['metadata']['source']
                    num_chunks = chunker.store_chunks(chunks, source, is_docling=True)
                    total_chunks += num_chunks
                    progress.advance(task)

            console.print(f"Created and stored [bold green]{total_chunks}[/bold green] chunks from [bold]{len(results)}[/bold] documents")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@extract_app.command("text")
def extract_text(
        text: Annotated[str, typer.Argument(..., help="Text content to process")],
        source: Annotated[str | None, typer.Option(None, help="Name of the source")] = None,
        chunk: Annotated[bool, typer.Option(True, help="Automatically chunk the extracted content")] = True,
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
):
    """Extract content from raw text or a text file."""
    try:
        # Check if text is a file path
        text_path = Path(text)
        if text_path.exists() and text_path.is_file() and text.startswith("@"):
            # Read content from file
            with open(text_path, encoding='utf-8') as f:
                text_content = f.read()
            console.print(f"Reading content from file: [bold]{text_path}[/bold]")
        else:
            text_content = text
            console.print("Processing provided text")

        extractor = DocumentExtractor()
        result = extractor.extract_from_text(text_content, source)

        if chunk:
            chunker = DocumentChunker(
                max_tokens=max_tokens or settings.max_tokens
            )
            chunks = chunker.chunk_text(text_content)
            source_name = source or "Text Input"
            num_chunks = chunker.store_chunks(chunks, source_name, is_docling=False)
            console.print(f"Created and stored [bold green]{num_chunks}[/bold green] chunks")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
