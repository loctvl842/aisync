import click


@click.group()
def math():
    pass


@math.command()
@click.option("--number", prompt="Enter a number", type=int, help="The number to square.")
def square(number):
    result = number**2
    click.echo(f"The square of {number} is: {result}")


@math.command()
@click.option("--number1", prompt="Enter the first number", type=int, help="The first number.")
@click.option("--number2", prompt="Enter the second number", type=int, help="The second number.")
def multiply(number1, number2):
    result = number1 * number2
    click.echo(f"The product of {number1} and {number2} is: {result}")
