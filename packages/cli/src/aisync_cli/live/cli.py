import asyncio
import time
from typing import Type

import click
from aisync.assistants.actions import get_assistants
from aisync.assistants.base import Assistant
from dotenv import find_dotenv, load_dotenv

from aisync_cli.live.live_previewer import LivePreviewer


@click.command(name="live-preview")
@click.option("--name", help="Name of the AI to activate. E.g Jarvis")
@click.option("--suit", help="Name of the suit to activate", default="mark_i")
def live(name: str, suit: str):
    """
    Run command aisync chat live --name Jarvis --suit mark_i
    """
    load_dotenv(find_dotenv())
    options = get_assistants()
    ai_class: Type[Assistant] | None = None
    if name:
        for name_, ai_class_ in options:
            if name == name_:
                ai_class = ai_class_
                break
        if ai_class is None:
            click.echo(
                f"AI {name} not found. Please choose from the following options:"
            )
            for index, (name, _) in enumerate(options, start=1):
                click.echo(f"{index}. {name}")
            exit(1)
    else:
        click.echo("Select an AI to activate:")
        for index, (name, _) in enumerate(options, start=1):
            click.echo(f"{index}. {name}")

        choice: int = click.prompt(
            "Enter the number of the AI to activate",
            type=int,
            default=1,
            show_default=True,
        )

        if 1 <= choice <= len(options):
            _, ai_class = options[choice - 1]
        else:
            click.echo("Invalid choice. Please enter a valid number.")
            exit(1)

    assistant = ai_class(suit=suit)
    previewer = LivePreviewer(assistant=assistant, suit=suit)
    try:
        asyncio.run(previewer.run_server())
        while not previewer.should_exit.is_set():
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                click.echo("\nShutting down server...")
                break
    finally:
        asyncio.run(previewer.shutdown())


if __name__ == "__main__":
    live()
