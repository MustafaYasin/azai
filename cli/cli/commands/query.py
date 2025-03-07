from typing import Annotated

import typer
from rag.generation import Generator
from rag.retrieval import Retriever
from rich.markdown import Markdown
from rich.panel import Panel

from cli.app import app
from cli.settings import get_openai_api_key, settings
from cli.utils import console

# Create query command group
query_app = typer.Typer(name="query", help="Query the system to retrieve information and generate answers")
app.add_typer(query_app)

@query_app.command("similar")
def find_similar(
        question: Annotated[str, typer.Argument(..., help="Query text to find similar chunks for")],
        k: Annotated[int, typer.Option(3, help="Number of chunks to retrieve")] = 3,
        model: Annotated[str | None, typer.Option(None, help="Embedding model to use")] = None,
):
    """Find chunks similar to the question."""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            console.print("[bold red]Error:[/bold red] OpenAI API key not found. Set it in your environment or config.", style="red")
            raise typer.Exit(1)

        embedding_model = model or settings.embedding_model

        console.print(f"Finding {k} chunks most similar to: [italic]\"{question}\"[/italic]")
        console.print(f"Using embedding model: [bold]{embedding_model}[/bold]")

        retriever = Retriever(api_key=api_key, model=embedding_model)
        chunks = retriever.find_relevant_chunks(question, k=k)

        if not chunks:
            console.print("[bold yellow]No relevant chunks found[/bold yellow]")
            return

        console.print(f"[bold green]Found {len(chunks)} relevant chunks:[/bold green]\n")

        for i, chunk in enumerate(chunks, 1):
            console.print(Panel(
                f"[bold white]Source:[/bold white] {chunk.chunk_title}\n"
                f"[bold white]Page:[/bold white] {chunk.page_number + 1}\n\n"  # +1 for human-readable page numbers
                f"{chunk.chunk_content}",
                title=f"Chunk {i}",
                border_style="blue"
            ))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@query_app.command("answer")
def generate_answer(
        question: Annotated[str, typer.Argument(..., help="Query to answer")],
        k: Annotated[int, typer.Option(3, help="Number of chunks to retrieve")] = 3,
        temperature: Annotated[float, typer.Option(0, help="Generation temperature (0-1)")] = 0,
        model: Annotated[str | None, typer.Option(None, help="LLM model to use")] = None,
        embedding_model: Annotated[str | None, typer.Option(None, help="Embedding model to use")] = None,
        custom_prompt: Annotated[str | None, typer.Option(None, help="Path to custom system prompt file")] = None,
        stream: Annotated[bool, typer.Option(True, help="Stream the response")] = True,
        show_context: Annotated[bool, typer.Option(False, help="Show retrieved context")] = False,
):
    """Generate an answer to the question based on retrieved chunks."""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            console.print("[bold red]Error:[/bold red] OpenAI API key not found. Set it in your environment or config.", style="red")
            raise typer.Exit(1)

        llm_model = model or settings.model
        emb_model = embedding_model or settings.embedding_model

        console.print(f"Generating answer to: [italic]\"{question}\"[/italic]")
        console.print(f"Using model: [bold]{llm_model}[/bold]")
        console.print(f"Using embedding model: [bold]{emb_model}[/bold]")
        console.print(f"Temperature: [bold]{temperature}[/bold]")
        console.print(f"Using top {k} chunks\n")

        # Read custom prompt if provided
        custom_prompt_text = None
        if custom_prompt:
            import os
            if os.path.exists(custom_prompt):
                with open(custom_prompt, encoding='utf-8') as f:
                    custom_prompt_text = f.read()
                console.print(f"Using custom prompt from: [bold]{custom_prompt}[/bold]\n")
            else:
                console.print(f"[bold yellow]Warning:[/bold yellow] Custom prompt file not found: {custom_prompt}")

        generator = Generator(api_key=api_key, model=llm_model)

        # Show context if requested
        if show_context:
            retriever = Retriever(api_key=api_key, model=emb_model)
            chunks = retriever.find_relevant_chunks(question, k=k)

            if not chunks:
                console.print("[bold yellow]No relevant chunks found[/bold yellow]")
                return

            console.print("[bold]Retrieved Context:[/bold]")
            for i, chunk in enumerate(chunks, 1):
                console.print(Panel(
                    f"[bold white]Source:[/bold white] {chunk.chunk_title}\n"
                    f"[bold white]Page:[/bold white] {chunk.page_number + 1}\n\n"
                    f"{chunk.chunk_content}",
                    title=f"Chunk {i}",
                    border_style="blue"
                ))

        if stream:
            # Stream the response
            response = generator.generate_streaming_answer(
                query=question,
                k=k,
                temperature=temperature,
                custom_prompt=custom_prompt_text
            )

            # Print streaming response
            console.print("\n[bold]Response:[/bold]")
            full_response = ""
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    console.print(content, end="")
                    full_response += content
            console.print()  # Final newline
        else:
            # Get the complete response at once
            response = generator.generate_answer(
                query=question,
                k=k,
                temperature=temperature,
                custom_prompt=custom_prompt_text
            )

            console.print("\n[bold]Response:[/bold]")
            console.print(Markdown(response))
            full_response = response

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@query_app.command("context")
def show_context(
        question: Annotated[str, typer.Argument(..., help="Query text")],
        k: Annotated[int, typer.Option(3, help="Number of chunks to retrieve")] = 3,
        model: Annotated[str | None, typer.Option(None, help="Embedding model to use")] = None,
        format: Annotated[str, typer.Option("panel", help="Output format: panel, text, or raw")] = "panel",
):
    """Show the context that would be used to answer the question."""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            console.print("[bold red]Error:[/bold red] OpenAI API key not found. Set it in your environment or config.", style="red")
            raise typer.Exit(1)

        embedding_model = model or settings.embedding_model

        console.print(f"Retrieving context for: [italic]\"{question}\"[/italic]")
        console.print(f"Using embedding model: [bold]{embedding_model}[/bold]")

        retriever = Retriever(api_key=api_key, model=embedding_model)
        chunks = retriever.find_relevant_chunks(question, k=k)

        if not chunks:
            console.print("[bold yellow]No relevant chunks found[/bold yellow]")
            return

        if format.lower() == "raw":
            context = retriever.format_context(chunks)
            console.print(context)
        elif format.lower() == "text":
            console.print("\n[bold]Retrieved Context:[/bold]")
            for i, chunk in enumerate(chunks, 1):
                console.print(f"\n--- Chunk {i} ---")
                console.print(f"Source: {chunk.chunk_title}")
                console.print(f"Page: {chunk.page_number + 1}")  # +1 for human-readable page numbers
                console.print("\nContent:")
                console.print(chunk.chunk_content)
        else:  # panel format (default)
            console.print("\n[bold]Retrieved Context:[/bold]")
            for i, chunk in enumerate(chunks, 1):
                console.print(Panel(
                    f"[bold white]Source:[/bold white] {chunk.chunk_title}\n"
                    f"[bold white]Page:[/bold white] {chunk.page_number + 1}\n\n"
                    f"{chunk.chunk_content}",
                    title=f"Chunk {i}",
                    border_style="blue"
                ))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@query_app.command("sources")
def list_sources():
    """List all document sources in the database."""
    try:
        from database import open_session
        from database.models import Chunk
        from rich.table import Table
        from sqlmodel import func, select

        with open_session() as session:
            # Query for unique sources and counts
            query = select(
                Chunk.chunk_title,
                func.count(Chunk.id).label("chunk_count"),
                func.min(Chunk.page_number).label("min_page"),
                func.max(Chunk.page_number).label("max_page")
            ).group_by(Chunk.chunk_title)

            sources = session.exec(query).all()

            if not sources:
                console.print("[bold yellow]No sources found in the database[/bold yellow]")
                return

            # Display sources table
            table = Table(title="Document Sources")
            table.add_column("Source", style="cyan")
            table.add_column("Chunks", style="green")
            table.add_column("Pages", style="blue")

            for source in sources:
                page_range = f"{source.min_page + 1}-{source.max_page + 1}" if source.max_page > source.min_page else f"{source.min_page + 1}"

                table.add_row(
                    source.chunk_title,
                    str(source.chunk_count),
                    page_range
                )

            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
