import asyncio
import importlib
from typing import List, Tuple, Type

import click
from dotenv import find_dotenv, load_dotenv

from core.logger import syslog

from .assistants.base import Assistant


@click.group()
def robot():
    pass


def get_ai_options() -> List[Tuple[str, Type[Assistant]]]:
    options = []
    package_path = "machine.robot.assistants"

    try:
        module = importlib.import_module(package_path)
    except ImportError:
        raise ImportError(f"Could not import module {package_path}")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and Assistant in attr.__bases__:
            class_name = attr.__name__
            ai_class = attr
            options.append((class_name, ai_class))
    return options


@robot.command()
@click.option("--name", help="Name of the AI to activate")
def activate(name):
    load_dotenv(find_dotenv())

    options = get_ai_options()
    ai_class: Type[Assistant] | None = None
    if name:
        for name_, ai_class_ in options:
            if name == name_:
                ai_class = ai_class_
                break
        if ai_class is None:
            click.echo(f"AI {name} not found. Please choose from the following options:")
            for index, (name, _) in enumerate(options, start=1):
                click.echo(f"{index}. {name}")
            exit(1)
    else:
        click.echo("Select an AI to activate:")
        for index, (name, _) in enumerate(options, start=1):
            click.echo(f"{index}. {name}")

        choice: int = click.prompt("Enter the number of the AI to activate", type=int, default=1, show_default=True)

        if 1 <= choice <= len(options):
            _, ai_class = options[choice - 1]
        else:
            click.echo("Invalid choice. Please enter a valid number.")
            exit(1)

    assistant = ai_class()
    syslog.info(f"{assistant.name} is online.")
    asyncio.run(assistant.start(streaming=True))


if __name__ == "__main__":
    robot()
