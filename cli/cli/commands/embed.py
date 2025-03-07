from pathlib import Path
from typing import Annotated

import typer
from rag.embedding import Embedder
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from cli.app import app
from cli.settings import get_openai_api_key, settings
from cli.utils import console

# Create embed command group
embed_app = typer.Typer(name="embed", help="Manage embeddings for document chunks")
app.add_typer(embed_app)

@embed_app.command("process")
def process_embeddings(
        batch_size: Annotated[int, typer.Option(100, help="Number of chunks to process in each batch")] = 100,
        model: Annotated[str | None, typer.Option(None, help="Embedding model to use")] = None,
):
    """Process all pending embeddings in the database."""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            console.print("[bold red]Error:[/bold red] OpenAI API key not found. Set it in your environment or config.", style="red")
            raise typer.Exit(1)

        embedding_model = model or settings.embedding_model

        console.print(f"Processing pending embeddings with batch size: [bold]{batch_size}[/bold]")
        console.print(f"Using embedding model: [bold]{embedding_model}[/bold]")

        embedder = Embedder(api_key=api_key, model=embedding_model)

        # Get count of pending embeddings
        from database import open_session
        from database.models import Chunk
        from sqlmodel import func, select

        with open_session() as session:
            pending_count = session.exec(
                select(func.count(Chunk.id)).where(Chunk.is_embedded == False)
            ).one()

            if pending_count == 0:
                console.print("[bold green]No pending embeddings to process[/bold green]")
                return

            console.print(f"Found [bold]{pending_count}[/bold] pending embeddings")

        # Process embeddings with progress bar
        with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}[/bold blue]"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
        ) as progress:
            task = progress.add_task("Processing embeddings", total=pending_count)

            # Process in batches and update progress
            total_processed = 0
            while total_processed < pending_count:
                new_processed = embedder.process_pending_embeddings(batch_size=batch_size)
                if new_processed == 0:
                    break

                total_processed += new_processed
                progress.update(task, completed=total_processed)

        console.print(f"[bold green]Successfully processed {total_processed} embeddings[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@embed_app.command("calculate-cost")
def calculate_embedding_cost(
        file_path: Annotated[Path, typer.Argument(..., help="Path to the file to analyze")],
        model: Annotated[str | None, typer.Option(None, help="Embedding model to use")] = None,
):
    """Calculate the cost of embedding a file."""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            console.print("[bold red]Error:[/bold red] OpenAI API key not found. Set it in your environment or config.", style="red")
            raise typer.Exit(1)

        embedding_model = model or settings.embedding_model

        if not file_path.exists():
            console.print(f"[bold red]Error:[/bold red] File {file_path} does not exist", style="red")
            raise typer.Exit(1)

        console.print(f"Calculating embedding cost for file: [bold]{file_path}[/bold]")
        console.print(f"Using embedding model: [bold]{embedding_model}[/bold]")

        with open(file_path, encoding='utf-8') as f:
            text = f.read()

        # Split text into paragraphs
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        embedder = Embedder(api_key=api_key, model=embedding_model)
        total_tokens, cost = embedder.calculate_embedding_cost(paragraphs)

        console.print(f"File: [bold]{file_path}[/bold]")
        console.print(f"Total paragraphs: [bold]{len(paragraphs)}[/bold]")
        console.print(f"Total tokens: [bold]{total_tokens}[/bold]")
        console.print(f"Estimated cost: [bold green]${cost:.6f}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@embed_app.command("status")
def embedding_status():
    """Show embedding status for chunks in the database."""
    try:
        from database import open_session
        from database.models import Chunk
        from sqlmodel import func, select

        with open_session() as session:
            total_chunks = session.exec(select(func.count(Chunk.id))).one()
            embedded_chunks = session.exec(
                select(func.count(Chunk.id)).where(Chunk.is_embedded == True)
            ).one()
            pending_chunks = total_chunks - embedded_chunks

            # Group by source
            query = select(
                Chunk.chunk_title,
                func.count(Chunk.id).label("total"),
                func.sum(Chunk.is_embedded.cast(int)).label("embedded")
            ).group_by(Chunk.chunk_title)

            sources = session.exec(query).all()

            # Display overall status
            console.print("[bold]Embedding Status:[/bold]")
            console.print(f"Total chunks: [bold]{total_chunks}[/bold]")
            console.print(f"Embedded chunks: [bold green]{embedded_chunks}[/bold green]")
            console.print(f"Pending chunks: [bold yellow]{pending_chunks}[/bold yellow]")

            if total_chunks > 0:
                percentage = (embedded_chunks / total_chunks) * 100
                console.print(f"Progress: [bold]{percentage:.2f}%[/bold]")

            # Display status by source
            if sources:
                table = Table(title="Embedding Status by Source")
                table.add_column("Source", style="cyan")
                table.add_column("Total", style="white")
                table.add_column("Embedded", style="green")
                table.add_column("Pending", style="yellow")
                table.add_column("Progress", style="blue")

                for source in sources:
                    source_total = source.total
                    source_embedded = source.embedded or 0
                    source_pending = source_total - source_embedded
                    source_percentage = (source_embedded / source_total) * 100 if source_total > 0 else 0

                    table.add_row(
                        source.chunk_title,
                        str(source_total),
                        str(source_embedded),
                        str(source_pending),
                        f"{source_percentage:.2f}%"
                    )

                console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
