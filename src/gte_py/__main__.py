"""Command-line interface."""

import typer

app = typer.Typer(help="gte_py - A Python CLI application")


@app.command()
def hello(name: str = "World"):
    """Say hello to someone."""
    typer.echo(f"Hello {name}!")


def run():
    """Run the application."""
    app()


if __name__ == "__main__":
    run()
