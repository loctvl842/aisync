import click

from aisync_cli.chat import chat


@click.group()
def main():
    pass


main.add_command(chat)


if __name__ == "__main__":
    main()
