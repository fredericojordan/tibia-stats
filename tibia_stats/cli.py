import rich_click as click


@click.command()
def main():
    from .__main__ import run

    run()
