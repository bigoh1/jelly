from jelly.server import Server
from jelly.client import Client
import argparse
import random
import string
import PySimpleGUI as sg


def random_nick(length=10):
    return "".join([random.choice(string.ascii_letters) for _ in range(length)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs=1, type=str)
    args = parser.parse_args()

    if args.mode[0].startswith('s'):
        server = Server()
    else:
        event, values = sg.Window('Jelly', [[sg.T("Your nick name:")],
                                            [sg.I(key='nick')],
                                            [sg.B('Ok')]]).read(close=True)
        client = Client(nick=values['nick'])


if __name__ == '__main__':
    main()
