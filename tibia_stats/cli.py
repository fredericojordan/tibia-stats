import os

import rich_click as click


@click.command()
def main():
    from .app import app

    host = os.getenv("HOST") or "0.0.0.0"
    port = os.getenv("PORT") or 10_000
    app.run(host=host, port=port)
