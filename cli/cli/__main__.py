from cli.app import app

@app.command()
def hello():
    """Say hello."""
    print("Hello World!")

if __name__ == "__main__":
    app()