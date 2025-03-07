from pathlib import Path
from typing import Annotated

import typer
from rag.chunking import DocumentChunker
from rich.table import Table

from cli.app import app
from cli.settings import settings
from cli.utils import console

# Create chunk command group
chunk_app = typer.Typer(name="chunk", help="Process content into chunks for embedding and retrieval")
app.add_typer(chunk_app)

@chunk_app.command("text")
def chunk_text(
        text: Annotated[str, typer.Argument(..., help="Text content to chunk")],
        source: Annotated[str, typer.Option(..., help="Name of the source")],
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
):
    """Chunk raw text content."""
    try:
        console.print(f"Chunking text with source name: [bold]{source}[/bold]")

        # Check if text is a file path
        text_path = Path(text)
        if text_path.exists() and text_path.is_file() and text.startswith("@"):
            # Read content from file
            with open(text_path, encoding='utf-8') as f:
                text_content = f.read()
            console.print(f"Reading content from file: [bold]{text_path}[/bold]")
        else:
            text_content = text

        chunker = DocumentChunker(
            max_tokens=max_tokens or settings.max_tokens
        )

        chunks = chunker.chunk_text(text_content)
        num_chunks = chunker.store_chunks(chunks, source, is_docling=False)

        console.print(f"Created and stored [bold green]{num_chunks}[/bold green] chunks")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@chunk_app.command("file")
def chunk_file(
        file_path: Annotated[Path, typer.Argument(..., help="Path to the file to chunk")],
        source: Annotated[str | None, typer.Option(None, help="Name of the source (defaults to filename)")] = None,
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
):
    """Chunk the content of a text file."""
    try:
        if not file_path.exists():
            console.print(f"[bold red]Error:[/bold red] File {file_path} does not exist", style="red")
            raise typer.Exit(1)

        source_name = source or file_path.name

        console.print(f"Chunking file: [bold]{file_path}[/bold] with source name: [bold]{source_name}[/bold]")

        with open(file_path, encoding='utf-8') as f:
            text = f.read()

        chunker = DocumentChunker(
            max_tokens=max_tokens or settings.max_tokens
        )

        chunks = chunker.chunk_text(text)
        num_chunks = chunker.store_chunks(chunks, source_name, is_docling=False)

        console.print(f"Created and stored [bold green]{num_chunks}[/bold green] chunks")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@chunk_app.command("rechunk")
def rechunk_document(
        source: Annotated[str, typer.Argument(..., help="Source identifier of the document to rechunk")],
        max_tokens: Annotated[int | None, typer.Option(None, help="Maximum tokens per chunk")] = None,
        merge_peers: Annotated[bool, typer.Option(True, help="Whether to merge peer chunks when possible")] = True,
):
    """Re-chunk an existing document by source identifier."""
    try:
        from database import open_session
        from database.models import Chunk
        from sqlmodel import delete, select

        console.print(f"Re-chunking document with source: [bold]{source}[/bold]")

        # First, fetch the content from the database by source
        chunks_content = []

        with open_session() as session:
            # Get all chunks for this source
            chunks = session.exec(
                select(Chunk).where(Chunk.chunk_title == source)
            ).all()

            if not chunks:
                console.print(f"[bold yellow]No chunks found with source: {source}[/bold yellow]")
                return

            # Collect all content
            for chunk in chunks:
                chunks_content.append(chunk.chunk_content)

            # Delete existing chunks for this source
            result = session.exec(
                delete(Chunk).where(Chunk.chunk_title == source)
            )
            session.commit()

            console.print(f"Deleted [bold]{len(chunks)}[/bold] existing chunks")

        # Join all content
        full_content = "\n\n".join(chunks_content)

        # Re-chunk the content
        chunker = DocumentChunker(
            max_tokens=max_tokens or settings.max_tokens,
            merge_peers=merge_peers
        )

        new_chunks = chunker.chunk_text(full_content)
        num_chunks = chunker.store_chunks(new_chunks, source, is_docling=False)

        console.print(f"Created and stored [bold green]{num_chunks}[/bold green] new chunks")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@chunk_app.command("list")
def list_chunks(
        source: Annotated[str | None, typer.Option(None, help="Filter by source")] = None,
        limit: Annotated[int, typer.Option(10, help="Maximum number of chunks to display")] = 10,
):
    """List chunks stored in the database."""
    try:
        from database import open_session
        from database.models import Chunk
        from sqlmodel import func, select

        with open_session() as session:
            # Count total chunks
            query = select(func.count(Chunk.id))
            if source:
                query = query.where(Chunk.chunk_title == source)
            total_chunks = session.exec(query).one()

            # Get chunks with optional source filter
            query = select(Chunk)
            if source:
                query = query.where(Chunk.chunk_title == source)
            chunks = session.exec(query.limit(limit)).all()

            # Show results
            if not chunks:
                console.print(f"[bold yellow]No chunks found{' for source: ' + source if source else ''}[/bold yellow]")
                return

            table = Table(title=f"Chunks in Database ({total_chunks} total)")
            table.add_column("ID", style="cyan")
            table.add_column("Source", style="green")
            table.add_column("Page", style="blue")
            table.add_column("Embedded", style="yellow")
            table.add_column("Preview", style="white")

            for chunk in chunks:
                embedded_status = "✅" if chunk.is_embedded else "❌"
                preview = chunk.chunk_content[:50] + "..." if len(chunk.chunk_content) > 50 else chunk.chunk_content

                table.add_row(
                    str(chunk.id)[:8],
                    chunk.chunk_title,
                    str(chunk.page_number + 1),  # +1 for human-readable page numbers
                    embedded_status,
                    preview
                )

            console.print(table)

            if len(chunks) < total_chunks:
                console.print(f"Showing {len(chunks)} of {total_chunks} chunks. Use --limit to show more.")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@chunk_app.command("delete")
def delete_chunks(
        source: Annotated[str | None, typer.Option(None, help="Delete chunks from specific source")] = None,
        confirm: Annotated[bool, typer.Option(True, help="Confirm before deleting")] = True,
):
    """Delete chunks from the database."""
    try:
        from database import open_session
        from database.models import Chunk
        from sqlmodel import delete, func, select

        with open_session() as session:
            # Count chunks to delete
            query = select(func.count(Chunk.id))
            if source:
                query = query.where(Chunk.chunk_title == source)
            count = session.exec(query).one()

            if count == 0:
                console.print(f"[bold yellow]No chunks found{' for source: ' + source if source else ''}[/bold yellow]")
                return

            # Confirm deletion
            if confirm:
                message = f"Delete {count} chunks"
                if source:
                    message += f" from source '{source}'"
                message += "?"

                if not typer.confirm(message, default=False):
                    console.print("Operation cancelled.")
                    return

            # Delete chunks
            query = delete(Chunk)
            if source:
                query = query.where(Chunk.chunk_title == source)

            session.exec(query)
            session.commit()

            console.print(f"[bold green]Successfully deleted {count} chunks[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
