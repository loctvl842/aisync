import click

from machine.robot.cli import robot


@click.group()
def cli():
    pass


cli.add_command(robot)

if __name__ == "__main__":
    cli()
