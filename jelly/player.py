from threading import Lock
from datetime import datetime, timedelta
from jelly.utils import Direction, distance

# TODO: document.


class Player:
    """Provides read-only access to a player."""
    def __init__(self, nick: str, x: int, y: int, size: int, factor: float, effect_end: datetime, color: (int, int, int)):
        self.nick = nick
        self.x = x
        self.y = y
        self.size = size
        self.speed_factor = factor
        self.effect_end = effect_end
        self.color = color

    @property
    def xy(self):
        return self.x, self.y

    @property
    def is_dead(self):
        return self.size <= 0

    def list(self) -> list:
        """Returns all params as a list."""
        return [self.nick, self.x, self.y, self.size, self.speed_factor, self.effect_end, self.color]

    def move_step(self, initial_player_size: int):
        """The bigger you're, the slower you're."""
        g = self.size / initial_player_size
        return round(initial_player_size / (4 * g) * self.speed_factor)

    def coords_after_move(self, direction: Direction, initial_player_size: int) -> (int, int):
        move_step = self.move_step(initial_player_size)
        x, y = self.x, self.y
        if Direction.LEFT in direction:
            x -= move_step
        if Direction.UP in direction:
            y -= move_step
        if Direction.RIGHT in direction:
            x += move_step
        if Direction.DOWN in direction:
            y += move_step
        return x, y


def player_was_eaten(a: Player, b: Player) -> (Player, Player):
    """If `a` ate `b`, returns (`a`, `b`). If vise versa, (`b`, `a`). Returns `None` if no one was eaten."""
    # If anyone is dead or of the same size.
    if a.size == 0 or b.size == 0 or a.size == b.size:
        return None

    if distance(a.xy, b.xy) > abs(a.size - b.size):
        return None

    # TODO: move away the constant.
    if a.size * 1.25 > b.size:
        return a, b
    elif a.size < b.size * 1.25:
        return b, a
    else:
        return None


class Players:
    """A high-level wrapper for players."""
    def __init__(self, initial_size: int = None, init=None):
        self.initial_size = initial_size
        self.data = dict()
        self.mutex = Lock()

        if init is not None and isinstance(init, dict):
            self.data = init

    def spawn(self, nick: str, xy: (int, int), color: (int, int, int)) -> None:
        assert self.initial_size is not None
        with self.mutex:
            self.data[nick] = [xy[0], xy[1], self.initial_size, 1, datetime.now(), color]

    def clear(self) -> None:
        with self.mutex:
            self.data.clear()

    def move(self, player: Player, direction: Direction) -> None:
        if datetime.now() > player.effect_end:
            self.clear_speed_factor(player)
        coords_after_move = player.coords_after_move(direction, self.initial_size)
        with self.mutex:
            self.data[player.nick][0] = coords_after_move[0]
            self.data[player.nick][1] = coords_after_move[1]

    def grow(self, player: Player, increment: int) -> None:
        with self.mutex:
            self.data[player.nick][2] += increment

            # FIXME: don't rely on implementation-defined behaviour.
            # Python dictionaries have the following property: they preserve the order in which the keys were added.
            # So, we sort players by `size` param to print the leader board at client side later.
            self.data = dict(sorted(self.data.items(), key=lambda item: item[1][2], reverse=True))

    def inc_speed_effect_time(self, player: Player, increment: timedelta):
        past_delta = self.data[player.nick][4] - datetime.now()
        new_end = datetime.now() + increment
        if past_delta.total_seconds() > 0:
            new_end += past_delta
        with self.mutex:
            self.data[player.nick][4] = new_end

    def mul_speed_factor(self, player: Player, m: float):
        with self.mutex:
            self.data[player.nick][3] *= m

    def clear_speed_factor(self, player: Player):
        with self.mutex:
            self.data[player.nick][3] = 1

    def kill(self, player: Player):
        with self.mutex:
            self.data[player.nick][2] = 0

    def pop(self, nick: str) -> None:
        with self.mutex:
            self.data.pop(nick, None)

    def __getitem__(self, nick: str) -> Player:
        """Returns a read-only copy."""
        return Player(nick, *self.data[nick])

    def __contains__(self, nick: str) -> bool:
        return nick in self.data

    def __iter__(self):
        return self.data.__iter__()

    def get_players(self) -> list[Player]:
        return [Player(nick, *self.data[nick]) for nick in self.data]

    def get_players_raw(self) -> dict:
        return self.data

    def nicks(self):
        return self.data.keys()
