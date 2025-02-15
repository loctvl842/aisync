import asyncio
import threading
import time
from typing import Type

import click
from aisync.assistants.actions import get_assistants
from aisync.assistants.base import Assistant
from dotenv import find_dotenv, load_dotenv
from aisync_cli.live.live_previewer import LivePreviewer


@click.command(name="chat")
@click.option("--name", help="Name of the AI to activate. E.g Jarvis")
@click.option(
    "--streaming",
    help="Stream the conversation with the AI",
    is_flag=True,
    default=False,
)
@click.option(
    "--monitor",
    help="Monitoring chat flow execution",
    is_flag=True,
    default=False,
)
@click.option("--suit", help="Name of the suit to activate", default="mark_i")
def chat(name: str, streaming: bool, monitor: bool, suit: str):
    """
    Run command aisync chat activate --name Jarvis --streaming
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
    # syslog.info(f"{assistant.name} is online.")
    chat_thread = threading.Thread(target=assistant.start, args=(streaming,))
    chat_thread.start()

    if monitor:
        previewer = LivePreviewer(assistant=assistant, suit=suit)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(previewer.run_server())

        try:
            while not (
                previewer.should_exit.is_set() and assistant.should_exit.is_set()
            ):
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            assistant.should_exit.set()
            previewer.should_exit.set()

            chat_thread.join()
            previewer.server_thread.join()

            loop.run_until_complete(previewer.shutdown())
            loop.close()
    else:
        try:
            while not assistant.should_exit.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            assistant.should_exit.set()
            chat_thread.join()

    assistant.start(streaming=streaming)


if __name__ == "__main__":
    chat()
