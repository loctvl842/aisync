import click


@click.group()
def aisync():
    """A CLI for controlling your AI assistants"""
    pass


@aisync.command()
@click.option("--name", prompt="Assistant name", help="Name of the AI assistant")
@click.option("--streaming", is_flag=True, help="Enable streaming mode")
def activate(name, streaming):
    """Activate an AI assistant"""
    click.echo(f"Activating {name} with streaming set to {streaming}")


# Add more commands here as needed

if __name__ == "__main__":
    aisync()
