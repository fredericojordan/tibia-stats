import rich_click as click


@click.command()
def main():
    from .app import app
    app.run()
