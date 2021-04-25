Jelly
=====
An agar.io-like game written in python.

Why?
===
You might ask why I've created this one if there are much more that people play and like.  
This was not the reason. I'm not going to maintain it for a long time. **I've created it to learn** networking (TCP) concepts.

Installation
============
```bash
# The same part:
$ git clone https://github.com/multifrench/jelly.git jelly; cd jelly
$ python3 -m pip install -r requirements.txt
# At server side:
$ python3 main.py server
# At client side:
$ python3 main.py client
```

Rules
=====
1. If you eat someone who's smaller that you're (including food), you grow.
2. The bigger you're, the slower you're.
3. The game is limited in time. At the end, the player with the biggest size is printed out on the screen.

LICENSE
=======
GPLv3

Author
======
`multifrench at pr0t0nm@1| d0t c0m`