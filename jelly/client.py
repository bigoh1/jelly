from jelly.server import Server

import socket
from json import loads, dumps
from threading import Thread, Lock
import pygame
from datetime import datetime, timedelta

from jelly.utils import Direction, assert_nick, draw_text, draw_circle, is_circle_on_screen, world2screen, offset
from jelly.food import Food
from jelly.player import Players


class Client:
    BACKGROUND = pygame.color.Color(255, 255, 255)
    LARGE_FONT_SIZE = 30
    SMALL_FONT_SIZE = 20

    def __init__(self, nick: str, host: str, port: int, width: int, height: int):
        assert_nick(nick)
        self.nick = nick

        self.HOST = host
        self.PORT = port

        self.DEFAULT_SCREEN_WIDTH = width
        self.DEFAULT_SCREEN_HEIGHT = height
        self.DEFAULT_LEADER_BOARD_WIDTH = self.DEFAULT_SCREEN_WIDTH // 4

        self.players = Players()
        self.food = Food()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.PORT))
        self.sock_mutex = Lock()

        # Precompute some commands. Those are just JSON binary string. See docs/protocol.md
        self.SPAWN = dumps({Server.SPAWN: self.nick}).encode("UTF-8")
        self.GET = dumps(Server.GET).encode("UTF-8")
        self.GET_MAP_BOUNDS = dumps(Server.GET_MAP_BOUNDS).encode("UTF-8")
        self.DISCONNECT = dumps({Server.DISCONNECT: self.nick}).encode("UTF-8")

        # Create a player with the same nick at the server side.
        self.send_spawn()

        self.round_end = None
        self.winner = None

        self.small_font = None
        self.large_font = None

        # Draw GUI
        self.game_loop()

    def __del__(self):
        """Sends `DISCONNECT` command and closes the socket."""
        self.send_disconnect()
        self.sock.close()

    def time_left(self) -> timedelta:
        """Returns how much there there's before the end of the round."""
        return self.round_end - datetime.now()

    def send_command(self, command: bytes):
        """Send `command` binary string to the server. See docs/protocol.md"""
        with self.sock_mutex:
            self.sock.sendall(command)

    def receive(self):
        """Receive and return server response."""
        with self.sock_mutex:
            response = self.sock.recv(4096)
        return response

    def send_disconnect(self):
        """After the corresponding binary string is sent to the server, the last removes data about the player."""
        self.send_command(self.DISCONNECT)

    def receive_get(self):
        """Sends `GET` command to the server. Parses server JSON response and saves it."""
        self.send_command(self.GET)

        # TODO: check if response is longer than 4048 bytes.
        raw_response = self.receive()

        # Parse the received JSON and save it into self.players
        response = loads(raw_response.decode("UTF-8"))

        # TODO here, too.
        self.players = Players(init=response["players"])

        # TODO here, too
        self.food = Food(init=response["food"])
        self.round_end = datetime.fromisoformat(response["round_end"])

    def send_move(self, direction: Direction):
        """Tells the server to move the player to `direction`."""
        command = dumps({Server.MOVE: [self.nick, int(direction)]}).encode("UTF-8")
        self.send_command(command)

    def send_spawn(self):
        """Sends `SPAWN` command to the server."""
        self.send_command(self.SPAWN)

    def get_map_bounds(self):
        """Asks server to return width and height of the map."""
        self.send_command(self.GET_MAP_BOUNDS)
        raw_response = self.receive()
        response = loads(raw_response.decode("UTF-8"))
        return response["width"], response["height"]

    @staticmethod
    def render_fonts():
        return pygame.font.Font(None, Client.SMALL_FONT_SIZE), pygame.font.Font(None, Client.LARGE_FONT_SIZE)

    def died(self, surface: pygame.Surface):
        draw_text(surface, self.large_font, "Game Over",
                  center=(surface.get_width() // 2, surface.get_height() // 2))

    def timeout(self, surface: pygame.Surface, time_left: int):
        if self.winner is None:
            # TODO: do NOT rely on implementation-dependent behaviour.
            #  Items of the dictionary aren't required to be sorted.
            self.winner = list(self.players.nicks())[0]

        draw_text(surface, self.large_font, "{} is the winner!".format(self.winner),
                  center=(surface.get_width() // 2, surface.get_height() // 2))
        draw_text(surface, self.large_font, "Reconnecting {}".format(abs(time_left)),
                  midbottom=(surface.get_width() // 2, surface.get_height()-1))

    def draw_leader_board(self, surface: pygame.Surface, lb_offset_x, lb_text_height):
        myself_in_top_ten = False
        for iter_count, nick in enumerate(list(self.players.nicks())[:10]):
            if nick == self.nick:
                myself_in_top_ten = True
            draw_text(surface, self.small_font, "#{} {}".format(iter_count + 1, nick), (0, 0, 0),
                      topleft=(lb_offset_x, lb_text_height * iter_count))
        if not myself_in_top_ten:
            rank = list(self.players.nicks()).index(self.nick)
            draw_text(surface, self.small_font, "#{} {}".format(rank + 1, self.nick), (0, 0, 0),
                      topleft=(lb_offset_x, lb_text_height * 10))

    def game_loop(self):
        pygame.init()

        # Create a resizable window.
        surface = pygame.display.set_mode((self.DEFAULT_SCREEN_WIDTH, self.DEFAULT_SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Jelly - {}".format(self.nick))

        self.small_font, self.large_font = Client.render_fonts()

        lb_offset_x = self.DEFAULT_SCREEN_WIDTH - self.DEFAULT_LEADER_BOARD_WIDTH
        lb_text_height = self.large_font.render('#0 TEST', True, (0, 0, 0)).get_height()

        # Init all data.
        self.receive_get()

        map_wh = self.get_map_bounds()
        run = True
        while run:
            get_thread = Thread(target=self.receive_get, daemon=True)
            get_thread.start()

            pygame.time.delay(20)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    run = False
                if e.type == pygame.VIDEORESIZE:
                    surface = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                    lb_offset_x = e.w - self.DEFAULT_LEADER_BOARD_WIDTH

            surface.fill((0, 0, 0))
            self.draw_leader_board(surface, lb_offset_x, lb_text_height)
            if self.players[self.nick].is_dead:
                get_thread.join()
                self.died(surface)
            elif self.time_left().total_seconds() > 0:
                self.winner = None

                keys = pygame.key.get_pressed()

                direction = Direction.NONE
                if keys[pygame.K_LEFT]:
                    direction |= Direction.LEFT
                if keys[pygame.K_UP]:
                    direction |= Direction.UP
                if keys[pygame.K_RIGHT]:
                    direction |= Direction.RIGHT
                if keys[pygame.K_DOWN]:
                    direction |= Direction.DOWN

                post_thread = Thread(target=self.send_move, args=(direction,), daemon=True)

                if direction != Direction.NONE:
                    post_thread.start()

                get_thread.join()
                offset_xy = offset(self.players[self.nick].xy, surface.get_size())

                # Draw map bounds
                top_left_world = (0, 0)
                top_left_screen = world2screen(top_left_world, offset_xy)
                rectangle = pygame.Rect(top_left_screen, map_wh)
                pygame.draw.rect(surface, self.BACKGROUND, rectangle)

                for player in self.players.get_players():
                    screen_xy = world2screen(player.xy, offset_xy)
                    if is_circle_on_screen(screen_xy, player.size, surface.get_size()) or player.nick == self.nick:
                        draw_circle(surface, screen_xy, player.size, player.color)
                        nick_color = (192, 192, 192) if player.is_dead else (0, 0, 0)
                        draw_text(surface, self.large_font, player.nick, nick_color, center=screen_xy)

                for food in self.food.get_food():
                    screen_xy = world2screen(food.xy, offset_xy)

                    if is_circle_on_screen(screen_xy, food.size, surface.get_size()):
                        draw_circle(surface, screen_xy, food.size, food.color)

                draw_text(surface, self.small_font, "Time left: {}".format(int(self.time_left().total_seconds())),
                          topleft=(2, 0))
                draw_text(surface, self.small_font, "Size: {}".format(self.players[self.nick].size),
                          bottomleft=(2, surface.get_height()-1))
                self.draw_leader_board(surface, lb_offset_x, lb_text_height)

                if direction != Direction.NONE:
                    post_thread.join()
            else:
                self.timeout(surface, int(-self.time_left().total_seconds()) + 1)
                pass

            pygame.display.update()
        pygame.quit()

