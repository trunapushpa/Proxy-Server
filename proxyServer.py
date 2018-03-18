import signal
import socket
import threading
import sys
import urlparse
import os
import hashlib
import time

config = {
    "HOST_NAME": "0.0.0.0",
    "BIND_PORT": 12345,
    "MAX_REQUEST_LEN": 1024,
    "CONNECTION_TIMEOUT": 15,
    "CACHE_SIZE": 3
}


class Server:
    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown)
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind(
            (config['HOST_NAME'], config['BIND_PORT']))
        self.serverSocket.listen(10)
        self.__clients = {}

    def listenForClient(self):
        print 'Listening...'
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxyThread,
                                 args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()

    def proxyThread(self, conn, client_addr):
        print 'Client Connected: ', client_addr

        request = conn.recv(config['MAX_REQUEST_LEN'])

        first_line = request.split('\n')[0]
        url = first_line.split(' ')[1]

        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]

        port_pos = temp.find(":")

        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1

        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        try:

            old = request.split(' ')[1]
            new = urlparse.urlparse(request.split(' ')[1]).__getattribute__('path')
            request = request.replace(old, new, 1)

            hash_object = hashlib.md5(old.encode())
            cache_filename = hash_object.hexdigest() + ".cached"

            if os.path.exists(cache_filename):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config['CONNECTION_TIMEOUT'])
                s.connect((webserver, port))

                tempreq = request.split('\n')[0] + '\n'
                t = (time.strptime(time.ctime(os.path.getmtime(cache_filename)), "%a %b %d %H:%M:%S %Y"))
                tempreq = tempreq + 'If-Modified-Since: ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', t) + '\n'
                for i in request.split('\n')[1:]:
                    tempreq = tempreq + i + '\n'
                # print(tempreq)

                s.sendall(tempreq)

                first = True
                while 1:
                    data = s.recv(config['MAX_REQUEST_LEN'])
                    if first:
                        if data.split(' ')[1] == '304':
                            print "Cache hit"
                        else:
                            o = open(cache_filename, 'wb')
                            print "Cache Updated"
                            if len(data) > 0:
                                o.write(data)
                            else:
                                break
                        first = False
                    else:
                        o = open(cache_filename, 'a')
                        if len(data) > 0:
                            o.write(data)
                        else:
                            break
            else:
                print "Cache miss"
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config['CONNECTION_TIMEOUT'])
                s.connect((webserver, port))

                s.sendall(request)

                while 1:
                    data = s.recv(config['MAX_REQUEST_LEN'])
                    o = open(cache_filename, 'a')
                    if len(data) > 0:
                        o.write(data)
                    else:
                        break
                s.close()

            cache_counter = 0
            cacheFiles = []
            for file in os.listdir("."):
                if file.endswith(".cached"):
                    cache_counter += 1
                    cacheFiles.append(file)
            while cache_counter > config['CACHE_SIZE']:
                mint = time.gmtime()
                minf = cacheFiles[0]
                for fileName in cacheFiles:
                    cft = os.path.getmtime(fileName)
                    if cft < mint:
                        mint = cft
                        minf = fileName
                os.remove(minf)
                cache_counter = 0
                cacheFiles = []
                for file in os.listdir("."):
                    if file.endswith(".cached"):
                        cache_counter += 1
                        cacheFiles.append(file)

            data = open(cache_filename).readlines()
            data2 = ''.join(data)
            conn.send(data2)

            conn.close()

        except socket.error as error_msg:
            print 'ERROR: ', client_addr, error_msg
            if s:
                s.close()
            if conn:
                conn.close()

    def _getClientName(self, cli_addr):
        return "Client " + str(cli_addr)

    def shutdown(self, signum, frame):
        self.serverSocket.close()
        sys.exit(0)


server = Server(config)
server.listenForClient()

