from jelly.server import Server
from jelly.client import Client
import argparse
import random
import string


def random_nick(length=10):
    return "".join([random.choice(string.printable) for _ in range(length)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs=1, type=str)
    args = parser.parse_args()

    if args.mode[0].startswith('s'):
        server = Server()
    else:
        client = Client(nick=random_nick())


if __name__ == '__main__':
    main()
