from jelly.server import Server
from jelly.client import Client
import argparse
import configparser


def main():
    config = configparser.ConfigParser()
    config.read('jelly.cfg')

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('mode', type=str, choices=['server', 'client'],
                        help="Specify if you'd like to run a server or connect to one.")

    parser.add_argument('-n', '--nick', type=str, help='Your nick name. Required if mode is `client`.')
    parser.add_argument('-p', '--port', type=int, help='Port of the server.', default=config['DEFAULT'].getint('PORT'))
    parser.add_argument('--host', type=str, help='Host of the server.', default=config['DEFAULT']['HOST'])
    parser.add_argument('-w', '--width', type=int,
                        help='With of the map if the mode is set to `server`. Otherwise width of the screen.')
    parser.add_argument('-h', '--height', type=int,
                        help='Height of the map if the mode is set to `server`. Otherwise height of the screen.')
    parser.add_argument('-t', '--time', type=int, help='The duration of one game round.', dest='game_time')
    parser.add_argument('-fn', '--food-num', type=int, help='Number of units food on the map.')
    parser.add_argument('-fi', '--food-increment', type=int,
                        help='If a player ate a food unit its size will increase by this number.')

    parser.add_argument('--help', action='help')
    # TODO: add logging & version param
    # parser.add_argument('-l', '--log', help='Enable logging.')
    # parser.add_argument('-v', '--version', help='Print version info and exit.')

    args = parser.parse_args()
    kwargs = dict()
    for k, v in vars(args).copy().items():
        if v is not None and k not in ('mode', 'gui'):
            kwargs[k] = v

    if args.mode == 'server':
        if args.nick is not None:
            print('Argument `--nick` is not required while running in `server` mode.')
            exit(0)

        if 'width' not in kwargs:
            kwargs['width'] = config['DEFAULT'].getint('MAP_WIDTH')
        if 'height' not in kwargs:
            kwargs['height'] = config['DEFAULT'].getint('MAP_HEIGHT')

        for param in ('game_time', 'food_num', 'food_increment'):
            if param not in kwargs:
                kwargs[param] = config['DEFAULT'].getint(param.capitalize())

        server = Server(**kwargs)
    elif args.mode == 'client':
        stop = False
        for param in ('game_time', 'food_num', 'food_increment'):
            if param in kwargs:
                print("Argument `--{}` is not required while running in `client` mode.".format(param))
                stop = True
        if args.nick is None:
            print("You didn't specify a nick-name or the gui flag. See `--nick` and `--help`.")
            stop = True
        if stop:
            exit(0)

        if 'width' not in kwargs:
            kwargs['width'] = config['DEFAULT'].getint('SCREEN_WIDTH')
        if 'height' not in kwargs:
            kwargs['height'] = config['DEFAULT'].getint('SCREEN_HEIGHT')

        client = Client(**kwargs)


if __name__ == '__main__':
    main()
