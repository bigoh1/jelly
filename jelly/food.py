from threading import Lock
from enum import IntEnum
from random import randint, choices
from jelly.player import Player
from jelly.utils import distance


class FoodKind(IntEnum):
    ORDINARY = 1
    SPEEDING_UP = 2
    SLOWING_DOWN = 3
    FREEZING = 4


class FoodUnit:
    def __init__(self, x: int, y: int, size: int, kind: FoodKind):
        self.x = x
        self.y = y
        self.size = size
        self.kind = FoodKind(kind)

    @property
    def xy(self):
        return self.x, self.y

    @property
    def color(self):
        if self.kind == FoodKind.ORDINARY:
            # Red
            return 225, 24, 69
        elif self.kind == FoodKind.SPEEDING_UP:
            # Green
            return 135, 233, 17
        elif self.kind == FoodKind.SLOWING_DOWN:
            # Blue
            return 0, 87, 233
        elif self.kind == FoodKind.FREEZING:
            # Purple
            return 137, 49, 239
        else:
            raise RuntimeError("Behaviour for `{}` is not implemented.".format(str(self.kind)))


def food_was_eaten(eater: Player, target: FoodUnit) -> bool:
    return eater.size > target.size > 0 and distance(eater.xy, target.xy) < eater.size


class Food:
    def __init__(self, probability_weights: list[int] = None, min_size: int = None, max_size: int = None,
                 init: list = None):
        self.probability_weights = probability_weights
        self.min_size = min_size
        self.max_size = max_size

        self.data = []
        self.mutex = Lock()
        if init is not None and isinstance(init, list):
            self.data = init

    def spawn(self, xy: (int, int), size=None, kind=None) -> None:
        assert self.probability_weights is not None
        assert self.min_size is not None
        assert self.max_size is not None

        if size is None:
            size = randint(self.min_size, self.max_size)
        if kind is None:
            kind = choices(range(1, len(FoodKind) + 1), weights=self.probability_weights)[0]
        with self.mutex:
            self.data.append([xy[0], xy[1], size, int(kind)])

    def pop(self, food: FoodUnit) -> None:
        with self.mutex:
            self.data = [f for f in self.data if f[0] != food.x and f[1] != food.y]

    def get_food_raw(self) -> list[list]:
        return self.data

    def get_food(self) -> list[FoodUnit]:
        return [FoodUnit(*food) for food in self.data]

    def clear(self) -> None:
        with self.mutex:
            self.data.clear()

