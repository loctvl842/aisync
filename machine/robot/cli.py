import importlib
import os

import click

from .assistants.base import Assistant


@click.group()
def robot():
    pass


def get_ai_options():
    options = []
    package_path = os.path.join("machine", "robot", "assistants")
    init_by_path = os.path.join(package_path, "__init__.py")

    file_name = os.path.splitext(init_by_path)[0]
    module_name = file_name.replace(os.sep, ".")
    module = importlib.import_module(module_name)
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
    options = get_ai_options()
    ai_class = None
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

        choice = click.prompt("Enter the number of the AI to activate", type=int, default=1, show_default=True)

        if 1 <= choice <= len(options):
            ai_class = options[choice - 1][1]
        else:
            click.echo("Invalid choice. Please enter a valid number.")
            exit(1)
    assistant = ai_class()
    assistant.start()


if __name__ == "__main__":
    robot()
