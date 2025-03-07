import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from cli.app import app
from cli.settings import settings
from cli.utils import console

system_app = typer.Typer(name="system", help="System management commands")
app.add_typer(system_app)

config_app = typer.Typer(name="config", help="Manage configuration settings")
system_app.add_typer(config_app)

@config_app.command("show")
def show_config():
    """Show current configuration."""
    config_dict = {
        "POSTGRES_USERNAME": settings.POSTGRES_USERNAME,
        "POSTGRES_PASSWORD": "****" if settings.POSTGRES_PASSWORD else "",
        "POSTGRES_DATABASE": settings.POSTGRES_DATABASE,
        "POSTGRES_HOST": settings.POSTGRES_HOST,
        "OPENAI_KEY": "****" if settings.OPENAI_KEY else "",
        "APP_PASSWORD": "****" if settings.APP_PASSWORD else "",
        "MODEL": settings.MODEL,
        "EMBEDDING_MODEL": settings.EMBEDDING_MODEL,
        "MAX_TOKENS": settings.MAX_TOKENS,
        "MERGE_PEERS": settings.MERGE_PEERS
    }

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in config_dict.items():
        table.add_row(key, str(value))

    console.print(table)
    console.print("\nConfiguration is loaded from environment variables or .env file")

@config_app.command("edit")
def edit_env_file():
    """Open .env file for editing."""
    try:
        env_path = Path(".env")

        if not env_path.exists():
            # Create a template .env file if it doesn't exist
            with open(env_path, "w") as f:
                f.write("""# --- Database Vars ---
POSTGRES_USERNAME=sourcehub
POSTGRES_PASSWORD=sourcehub
POSTGRES_DATABASE=sourcehub
POSTGRES_HOST=localhost

# --- OpenAI Key ---
OPENAI_KEY=your_openai_key_here

# --- App Settings ---
APP_PASSWORD=pure

# --- RAG Settings ---
MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small
MAX_TOKENS=8191
MERGE_PEERS=True
""")
            console.print(f"Created template .env file at: [bold]{env_path.absolute()}[/bold]")

        # Try to open the file with the default editor
        if sys.platform == "win32":
            os.startfile(env_path)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", env_path], check=True)
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", env_path], check=True)

        console.print("Opened .env file for editing. Remember to restart the application after changes.")

    except Exception as e:
        console.print(f"[bold red]Error opening .env file:[/bold red] {e}", style="red")
        console.print(f"You can manually edit the file at: [bold]{env_path.absolute()}[/bold]")

@system_app.command("status")
def system_status():
    """Show system status overview."""
    try:
        # Show database status
        from database import build_engine_url, open_session
        from database.models import Chunk
        from sqlmodel import func, select

        console.print("[bold]System Status:[/bold]")

        # Config status
        console.print("\n[bold]Configuration:[/bold]")
        console.print(f"Environment variables loaded: [bold]{'YES' if os.environ.get('POSTGRES_USERNAME') else 'NO'}[/bold]")
        console.print(f"Database URL: [bold]{build_engine_url()}[/bold]")
        console.print(f"OpenAI API key: [bold]{'configured' if settings.OPENAI_KEY else 'not configured'}[/bold]")

        # Database status
        console.print("\n[bold]Database:[/bold]")
        try:
            with open_session() as session:
                # Count chunks
                total_chunks = session.exec(select(func.count(Chunk.id))).one()
                embedded_chunks = session.exec(
                    select(func.count(Chunk.id)).where(Chunk.is_embedded == True)
                ).one()
                pending_chunks = total_chunks - embedded_chunks

                # Count sources
                source_count = session.exec(
                    select(func.count(func.distinct(Chunk.chunk_title)))
                ).one()

                console.print("Connection: [bold green]OK[/bold green]")
                console.print(f"Total sources: [bold]{source_count}[/bold]")
                console.print(f"Total chunks: [bold]{total_chunks}[/bold]")
                console.print(f"Embedded chunks: [bold green]{embedded_chunks}[/bold green]")
                console.print(f"Pending chunks: [bold yellow]{pending_chunks}[/bold yellow]")

                if total_chunks > 0:
                    percentage = (embedded_chunks / total_chunks) * 100
                    console.print(f"Embedding progress: [bold]{percentage:.2f}%[/bold]")

        except Exception as db_error:
            console.print("Database connection: [bold red]ERROR[/bold red]")
            console.print(f"Details: {db_error}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@system_app.command("setup")
def setup_system(
        openai_key: Annotated[str | None, typer.Option(None, help="OpenAI API key")] = None,
        init_db: Annotated[bool, typer.Option(False, help="Initialize/migrate the database")] = False,
        db_username: Annotated[str | None, typer.Option(None, help="Database username")] = None,
        db_password: Annotated[str | None, typer.Option(None, help="Database password")] = None,
        db_host: Annotated[str | None, typer.Option(None, help="Database host")] = None,
        db_name: Annotated[str | None, typer.Option(None, help="Database name")] = None,
):
    """Set up the system for first use by creating/updating .env file."""
    try:
        console.print("[bold]Setting up SourceHub RAG system...[/bold]")

        # Create or update .env file
        env_path = Path(".env")
        env_vars = {}

        # Read existing .env if it exists
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

        # Update with provided values
        if db_username:
            env_vars["POSTGRES_USERNAME"] = db_username
        if db_password:
            env_vars["POSTGRES_PASSWORD"] = db_password
        if db_host:
            env_vars["POSTGRES_HOST"] = db_host
        if db_name:
            env_vars["POSTGRES_DATABASE"] = db_name
        if openai_key:
            env_vars["OPENAI_KEY"] = openai_key

        # Ensure required variables exist
        if "POSTGRES_USERNAME" not in env_vars:
            env_vars["POSTGRES_USERNAME"] = "sourcehub"
        if "POSTGRES_PASSWORD" not in env_vars:
            env_vars["POSTGRES_PASSWORD"] = "sourcehub"
        if "POSTGRES_HOST" not in env_vars:
            env_vars["POSTGRES_HOST"] = "localhost"
        if "POSTGRES_DATABASE" not in env_vars:
            env_vars["POSTGRES_DATABASE"] = "sourcehub"
        if "APP_PASSWORD" not in env_vars:
            env_vars["APP_PASSWORD"] = "pure"
        if "MODEL" not in env_vars:
            env_vars["MODEL"] = "gpt-4"
        if "EMBEDDING_MODEL" not in env_vars:
            env_vars["EMBEDDING_MODEL"] = "text-embedding-3-small"
        if "MAX_TOKENS" not in env_vars:
            env_vars["MAX_TOKENS"] = "8191"
        if "MERGE_PEERS" not in env_vars:
            env_vars["MERGE_PEERS"] = "True"

        # Write updated .env file
        with open(env_path, "w") as f:
            f.write("# --- Database Vars ---\n")
            f.write(f"POSTGRES_USERNAME={env_vars['POSTGRES_USERNAME']}\n")
            f.write(f"POSTGRES_PASSWORD={env_vars['POSTGRES_PASSWORD']}\n")
            f.write(f"POSTGRES_DATABASE={env_vars['POSTGRES_DATABASE']}\n")
            f.write(f"POSTGRES_HOST={env_vars['POSTGRES_HOST']}\n")
            f.write("\n# --- OpenAI Key ---\n")
            f.write(f"OPENAI_KEY={env_vars.get('OPENAI_KEY', '')}\n")
            f.write("\n# --- App Settings ---\n")
            f.write(f"APP_PASSWORD={env_vars['APP_PASSWORD']}\n")
            f.write("\n# --- RAG Settings ---\n")
            f.write(f"MODEL={env_vars['MODEL']}\n")
            f.write(f"EMBEDDING_MODEL={env_vars['EMBEDDING_MODEL']}\n")
            f.write(f"MAX_TOKENS={env_vars['MAX_TOKENS']}\n")
            f.write(f"MERGE_PEERS={env_vars['MERGE_PEERS']}\n")

        console.print(f"Configuration saved to: [bold green]{env_path.absolute()}[/bold green]")
        console.print("[bold yellow]Note:[/bold yellow] You need to restart the application for changes to take effect")

        # Initialize database if requested
        if init_db:
            console.print("\n[bold]Initializing database...[/bold]")

            try:
                # Run alembic migrations
                alembic_ini = Path(__file__).parent.parent.parent.parent / "database" / "alembic.ini"
                if alembic_ini.exists():
                    result = subprocess.run(
                        [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    if result.returncode == 0:
                        console.print("[bold green]Database initialization successful[/bold green]")
                    else:
                        console.print(f"[bold red]Database initialization failed:[/bold red] {result.stderr}")
                else:
                    console.print(f"[bold yellow]Could not find alembic.ini at: {alembic_ini}[/bold yellow]")
                    console.print("Please initialize the database manually")

            except Exception as db_error:
                console.print(f"[bold red]Database initialization error:[/bold red] {db_error}")

        console.print("\n[bold green]Setup complete![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")

@system_app.command("info")
def system_info():
    """Show system information."""
    try:
        console.print("[bold]SourceHub System Information:[/bold]")

        # Python version
        console.print(f"\n[bold]Python:[/bold] {sys.version}")

        # Package versions
        console.print("\n[bold]Package Versions:[/bold]")
        packages = [
            "typer", "openai", "sqlmodel", "rich", "docling",
            "tiktoken", "pydantic", "alembic"
        ]

        table = Table()
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="green")

        for package in packages:
            try:
                import importlib.metadata
                version = importlib.metadata.version(package)
                table.add_row(package, version)
            except:
                table.add_row(package, "Not installed")

        console.print(table)

        # OpenAI models
        console.print("\n[bold]OpenAI Configuration:[/bold]")
        console.print(f"LLM Model: [bold]{settings.MODEL}[/bold]")
        console.print(f"Embedding Model: [bold]{settings.EMBEDDING_MODEL}[/bold]")
        console.print(f"API Key: [bold]{'Configured' if settings.OPENAI_KEY else 'Not configured'}[/bold]")

        # Database information
        from database import build_engine_url
        console.print("\n[bold]Database Configuration:[/bold]")
        console.print(f"Connection URL: [bold]{build_engine_url()}[/bold]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
