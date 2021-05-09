# JSON protocol
This protocol is used by server and client sides for TCP communication.

## `GET_MAP_BOUNDS`
#### Asks server to return width and height of the map.
### Client request:
```json
"GET_MAP_BOUNDS;"
```
### Server response:
```json
{
  "width": <MAP_WIDTH>,
  "height": <MAP_HEIGHT>
}
```
- `<MAP_WIDTH>` and `<MAP_HEIGHT>` are with and height of the map, respectively.


## `GET`
#### Asks server to return a list of players, food and end of the round time.
### Client request: 
```json
"GET;"
```
### Server response:
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

## `SPAWN`
#### Tells server to spawn a player with nick `<NICK>`.
### Client request
```json
{
  "SPAWN": "<NICK>"
};
```


## `DISCONNECT`
#### Tells server that player `<NICK>` has disconnected. Is usually sent if there's an uncaught exception, or the player closed the game.
### Client request
```json
{
  "DISCONNECT": "<NICK>"
};
```

## `MOVE`
#### Tells server to move player `<NICK>` to `<DIRECTION>`.
### Client request
```json
{
  "MOVE": [
    "<NICK>",
    <DIRECTION>
  ]
};
```
- `<DIRECTION>` is integer representation of `Direction` enum.