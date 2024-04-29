import click


@click.command()
@click.argument("numbers", nargs=-1, type=int)
def sum(numbers):
    total = sum(numbers)
    click.echo(f"The sum of the numbers is: {total}")
