# cli/main.py
from cli.app import app
import typer
from typing import Optional

def version_callback(value: bool) -> None:
    if value:
        print("SourceHub CLI v0.1.0")
        raise typer.Exit(0)

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version information",
        callback=version_callback,
        is_eager=True,
    ),
):
    """SourceHub CLI: Manage your RAG system."""
    pass

@app.command()
def hello():
    """Say hello."""
    print("Hello World!")

if __name__ == "__main__":
    app()