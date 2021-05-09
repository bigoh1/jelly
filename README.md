Jelly
=====
An agar.io-like game written in python.

Why?
===
I've written this little pet-project to learn **Networking (TCP)**.

Installation
============
```bash
# The same part:
$ git clone https://github.com/multifrench/jelly.git jelly && cd jelly
$ python3 -m pip install virtualenv && python3 -m virtualenv .venv && source .venv/bin/activate
$ python3 -m pip install -r requirements.txt
# At server side:
$ python3 main.py server
# At client side:
$ python3 main.py client --nick your-nick-name
```

One-liner:
```bash
$ git clone https://github.com/multifrench/jelly.git jelly && cd jelly && python3 -m pip install virtualenv && python3 -m virtualenv .venv && source .venv/bin/activate && python3 -m pip install -r requirements.txt
```

Rules
=====
1. If you eat someone who's smaller that you're (including food), you grow; you must be larger by 25%.
2. The bigger you're, the slower you're.
3. The game is limited in time. At the end, the player with the biggest size is printed out on the screen.
4. If you eat red food, you grow by its size; if you eat green food, you speed up by 15%; blue makes you slower by 5%;
purple food freezes you. The effect of green, blue and purple food units lasts for the size of the eaten food unit.
5. There's a constant amount of food units on the map. They're all spawned at the start of a round, and a new one is spawned each time another food unit was eaten.

LICENSE
=======
GPLv3

Author
======
`multifrench at pr0t0nm@1| d0t c0m`