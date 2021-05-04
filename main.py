from jelly.server import Server
from jelly.client import Client
from jelly.food import FoodKind
import config as default
import argparse
import configparser


def main():
    config = configparser.ConfigParser()
    config.read('jelly.cfg')

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('mode', type=str, choices=['server', 'client'],
                        help="Specify if you'd like to run a server or connect to one.")

    parser.add_argument('-n', '--nick', type=str, help='Your nick name. Required if mode is `client`.')
    parser.add_argument('-p', '--port', type=int, help='Port of the server.', default=default.PORT)
    parser.add_argument('--host', type=str, help='Host of the server.', default=default.HOST)
    parser.add_argument('-w', '--width', type=int,
                        help='With of the map if the mode is set to `server`. Otherwise width of the screen.')
    parser.add_argument('-h', '--height', type=int,
                        help='Height of the map if the mode is set to `server`. Otherwise height of the screen.')
    parser.add_argument('-t', '--time', type=int, help='The duration of one game round.', dest='game_time')
    parser.add_argument('-fn', '--food-num', type=int, help='Number of units food on the map.')
    parser.add_argument('-fmin', '--food-min-size', type=int, metavar='FMIN',
                        help='Food units are generated of a random size in [`FMIN`; `FMAX`].')
    parser.add_argument('-fmax', '--food-max-size', type=int, metavar='FMAX',
                        help='Food units are generated of a random size in [`FMIN`; `FMAX`].')
    parser.add_argument('-rt', '--restart-time', type=int, metavar='RT',
                        help='After game time is out, what for `RT` seconds before respawning players.')
    parser.add_argument('-fp', '--food-probability', type=int, nargs=len(FoodKind),
                        help='See the comment for `FOOD_PROBABILITY` in config.py')
    parser.add_argument('-ip', '--init-player-size', type=int, help='New players will be spawned with this size.')

    parser.add_argument('--help', action='help')
    # TODO: add logging & version param
    # parser.add_argument('-l', '--log', help='Enable logging.')
    # parser.add_argument('-v', '--version', help='Print version info and exit.')

    server_args = ('game_time', 'food_num', 'food_min_size', 'food_max_size', 'restart_time', 'food_probability',
                   'init_player_size')

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
            kwargs['width'] = default.MAP_WIDTH
        if 'height' not in kwargs:
            kwargs['height'] = default.MAP_HEIGHT

        for param in server_args:
            if param not in kwargs:
                kwargs[param] = getattr(default, param.upper())

        server = Server(**kwargs)
    elif args.mode == 'client':
        stop = False
        for param in server_args:
            if param in kwargs:
                print("Argument `--{}` is not required while running in `client` mode.".format(param))
                stop = True
        if args.nick is None:
            print("You didn't specify a nick-name or the gui flag. See `--nick` and `--help`.")
            stop = True
        if stop:
            exit(0)

        if 'width' not in kwargs:
            kwargs['width'] = default.SCREEN_WIDTH
        if 'height' not in kwargs:
            kwargs['height'] = default.SCREEN_HEIGHT

        client = Client(**kwargs)


if __name__ == '__main__':
    main()
