import os

import rich_click as click


@click.command()
def main():
    from .app import app
    port = os.getenv("PORT") or 10000
    app.run(port=port)
