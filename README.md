# Proxy-Server with Cache

## How to Run

1. Open the current directory in a terminal.
2. Run the command `python dummyServer.py`
3. Run the command `python proxyServer.py`

## How to test

1. Run the command `curl -x http://localhost:12345 http://localhost:20000/1.txt`.
2. Run the command `curl -x http://localhost:12345 http://localhost:20000/2.binary`.
3. Run the command `curl -x http://localhost:12345 http://localhost:20000/screenshot.png`.

* We get cache miss for all the above comands.

* All the files are now cached. This can be checked by running the command `curl -x http://localhost:12345 http://localhost:20000/1.txt`.
We get cache hit.

* If we update `1.txt` and again curl we get cache update.
