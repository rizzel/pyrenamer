import logging
from sqlite3 import connect
from os.path import join, dirname
from threading import Thread
from queue import Queue
import socket
from re import search
from time import time, sleep

from pyrenamer import Singleton
import pyrenamer.config as config


class AniDB(metaclass=Singleton):
    def __init__(self):
        self.init_db()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config.debug_level.upper())

    @staticmethod
    def init_db():
        dbh = connect(config.cache_db)
        with open(join(dirname(__file__), 'schema.sql')) as f:
            dbh.executescript(f.read())


class AniDBThread(Thread):
    delays = (30, 2*60, 5*60, 10*60, 30*60, 60*60, 2*60*60, 3*60*60)

    def __init__(self, command_queue, result_queue):
        super().__init__()
        self._command_queue = command_queue
        self._result_queue = result_queue
        self._auth = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('0.0.0.0', config.outgoing_udp_port))
        self._last_send = time()
        self._delay = 0

    def run(self):
        pass

    def _send(self, cmd, params={}):
        """

        :param str cmd: The command to send
        :return: The received stuff
        :rtype: str|None
        """
        retry = 5
        while retry > 0:
            if cmd not in ('PING', 'ENCRYPT', 'ENCODING', 'AUTH', 'VERSION'):
                self._do_auth()
            code, data = self._send_raw(cmd + ' ' + '&'.join(map(lambda k, v: k + '=' + v, params.items())))
            if code is None:

    def _send_raw(self, cmd):
        last_send_delta = time() - self._last_send
        if last_send_delta < 2:
            sleep(2 - last_send_delta)

        cmd = cmd.encode('ascii')
        self._socket.sendto(cmd, (config.anidb_host, config.anidb_port))
        result, address = self._socket.recvfrom(1400)
        result = result.decode('utf-8')  # type: str
        m = search(r'^(\d+) (.+)', result)
        if m:
            code = int(m.group(1))
            data = m.group(2)

            if code == 501:
                self._do_auth()
            elif code in (502, 505, 506, 555, 598, 600, 602):
                print(data)
                exit(1)
            elif code == 601:
                print(data)
                print("Waiting 30 minutes...")
                sleep(30*60)
            elif code == 604:
                print(data)
                print("Waiting {} seconds".format(AniDBThread.delays[self._delay]))
                sleep(AniDBThread.delays[self._delay])
                self._delay += 1 if self._delay < len(AniDBThread.delays) - 1
            elif '{}'.format(code)[0] == '6':
                print(data)
                exit(1)
            else:
                self._delay = 0

                return code, data
        else:
            return None, None

    def _do_auth(self):
        from pyrenamer import anidb_client_name, anidb_client_version, anidb_api_version
        if self._auth is None:
            code, data = self._send_raw('AUTH user={}&pass={}&protover={}&client={}&clientver={}&enc=UTF-8'.format(
                config.anidb_user, config.anidb_password, anidb_api_version, anidb_client_name, anidb_client_version
            ))
            if code == 500:
                print("Login failed")
                exit(1)
            elif code == 503:
                print("Client is too old and not supported anymore. Please update.")
                exit(1)
            elif code == 506:
                print("Invalid session on auth - should not happen")
                exit(1)
            elif code == 200 or code == 201:
                if code == 201:
                    print("Newer version of the client is available. please update.")
                m = search(r'^(\w+) LOGIN ACCEPTED', data)
                if m:
                    self._auth = m.group(1)
                    return True
            elif code == 601:
                print("AniDB out of service - Try again later.")
                exit(1)


    def command_ping(self):
        pass
