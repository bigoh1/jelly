JSON protocol
=============
This protocol is used by server and client sides for TCP communication.

`GET` command request (is sent by client)s
=========================================
```json
"GET"
```

`GET` command response (is sent by server)
==========================================

```json
{
  "players": {
    "<NICK>": [<X>, <Y>, <SIZE>, <SPEED_FACTOR>, <EFFECT_END>, <COLOR>],
    ...
  },
  "food": [
    [<X>, <Y>, <SIZE>],
    ...
  ],
  "round_end": <RE>
}
```

- `<NICK>` a string that represents a player nick;
- `<X>`, `<Y>` are integer coordinates of food unit OR player;
- `<SIZE>` is integer size of food unit or player;
- `<SPEED_FACTOR>`: move step is multiplied by this constant. See `Player.move_step()`;
- `<EFFECT_END>` is a string that represents a point in time when `<SPEED_FACTOR>` is set to 1 (doesn't influence move step anymore);
- `<COLOR>` is an integer triplet in RGB format. Represents color of player `<NICK>`. The server chooses it while spawning a player randomly;
- `<RE>` is a string that represents a point in time (in ISO format) when the round is over.

`SPAWN` command request
=======================
```json
{
  "SPAWN": "<NICK>"
}
```
Tells server to spawn a player with nick `<NICK>`.

`DISCONNECT` command request
============================
```json
{
  "DISCONNECT": "<NICK>"
}
```
Tells server that player `<NICK>` has disconnected. Is usually sent if there's an uncaught exception, or the player closed the game.

`MOVE` command request
======================
```json
{
  "MOVE": [
    "<NICK>",
    <DIRECTION>
  ]
}
```
- `<DIRECTION>` is integer representation of `Direction` enum.

Tells server to move player `<NICK>` to `<DIRECTION>`.