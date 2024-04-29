import click

from machine.robot.cli import robot
from test_clis.hello import hello
from test_clis.math import math
from test_clis.sum import sum


@click.group()
def cli():
    pass


cli.add_command(hello)
cli.add_command(sum)
cli.add_command(math)
cli.add_command(robot)

if __name__ == "__main__":
    cli()
