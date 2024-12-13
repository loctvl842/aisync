import click

from aisync_cli.chat import chat
from aisync_cli.live import live


@click.group()
def main():
    pass


main.add_command(chat)
main.add_command(live)


if __name__ == "__main__":
    main()
