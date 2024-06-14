import asyncio
import importlib
from typing import List, Tuple, Type

import click
from dotenv import find_dotenv, load_dotenv

from core.logger import syslog
from core.db import sessions, DBType

from .assistants.base import Assistant


# from pgvector.psycopg import register_vector
# import psycopg

# conn = psycopg.connect(dbname='postgres', autocommit=True)

# conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
# register_vector(conn)



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
@click.option("--streaming", help="Stream the conversation with the AI", is_flag=True, default=False)
def activate(name: str, streaming: bool):
    """
    Run command python cli.py activate --name "Jarvis" --streaming
    """
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
    asyncio.run(assistant.start(streaming=streaming))


if __name__ == "__main__":
    robot()
