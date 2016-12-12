import logging
from sqlite3 import connect
from os.path import join, dirname
from threading import Thread
from queue import Queue, Empty
import socket
from re import search
from time import time, sleep

from pyrenamer import Singleton
import pyrenamer.config as config
from pyrenamer.cache import Cache


class AniDBThread(Thread):
    delays = (30, 2 * 60, 5 * 60, 10 * 60, 30 * 60, 60 * 60, 2 * 60 * 60, 3 * 60 * 60)

    def __init__(self, command_queue, result_queue):
        super().__init__()
        self._command_queue = command_queue
        """ :type: Queue """
        self._result_queue = result_queue
        """ :type: Queue """
        self._auth = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('0.0.0.0', config.outgoing_udp_port))
        self._last_send = time()
        self._current_delay_idx = 0

    def run(self):
        while True:
            try:
                item = self._command_queue.get(True, 1)
            except Empty:
                if time() - self._last_send > 30 * 60:
                    self.command_ping()
                continue
            if item is None:
                break
            f = {
                'PING': self.command_ping,
                'ANIME': self.command_anime,
                'FILE': self.command_file,
                'GROUP': self.command_group,
                'MYLISTADD': self.command_mylist_add
            }.get(item[0], None)
            if f is None:
                print("Unknown function {} - ignoring".format(item[0]))
                continue
            f(*item[1:])

    def _send(self, cmd, params=None):
        if cmd not in ('PING', 'ENCRYPT', 'ENCODING', 'AUTH', 'VERSION'):
            self._do_auth()

        to_send = cmd
        if params is None:
            params = {}
        params['s'] = self._auth
        to_send += ' ' + '&'.join(filter(lambda v: v is not None,
                                         map(lambda k, v: k + '=' + v if v is not None else None, params.items())))

        retry = 5
        while retry > 0:
            last_send_delta = time() - self._last_send
            if last_send_delta < 2:
                sleep(2 - last_send_delta)

            cmd = cmd.encode('ascii')
            self._socket.sendto(cmd, (config.anidb_host, config.anidb_port))
            result, address = self._socket.recvfrom(1400)
            result = result.decode('utf-8')  # type: str
            m = search(r'^(\d+) (.+)', result)
            self._last_send = time()
            if m:
                code = int(m.group(1))
                data = m.group(2)

                if code == 501:
                    if cmd != 'AUTH':
                        self._do_auth()
                elif code in (502, 505, 555, 598, 600, 602):
                    print(data)
                    exit(1)
                elif code == 601:
                    print(data)
                    print("Waiting 30 minutes...")
                    sleep(30 * 60)
                elif code == 604:
                    print(data)
                    print("Waiting {} seconds".format(AniDBThread.delays[self._current_delay_idx]))
                    sleep(AniDBThread.delays[self._current_delay_idx])
                    if self._current_delay_idx < len(AniDBThread.delays) - 1:
                        self._current_delay_idx += 1
                elif '{}'.format(code)[0] == '6':
                    print(data)
                    exit(1)
                elif code == 503:
                    print("Client is too old and not supported anymore. Please update.")
                    exit(1)
                elif code == 506:
                    print("ReAuth to get new session.")
                    Cache().remove('auth')
                    self._do_auth()
                else:
                    self._current_delay_idx = 0

                    return code, data
            else:
                print("Nothing received - server could be offline")
                exit(1)
        print("Maximum number of retries reached")
        exit(1)

    def _do_auth(self):
        if self._auth is None:
            c = Cache()
            self._auth = c.get('auth', 35 * 60)
            if self._auth is not None:
                return

            from pyrenamer import anidb_client_name, anidb_client_version, anidb_api_version
            code, data = self._send('AUTH', {'user': config.anidb_user, 'pass': config.anidb_password,
                                             'protover': anidb_api_version, 'client': anidb_client_name,
                                             'clientver': anidb_client_version, 'enc': 'UTF-8'})
            if code == 500:
                print("Login failed")
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
                    c.set('auth', self._auth)
                    return
            elif code == 601:
                print("AniDB out of service - Try again later.")
                exit(1)
            else:
                print("Unexpected code during AUTH: {}".format(code))
                print(data)
                exit(1)

    def command_ping(self, do_nat=False):
        code, data = self._send('PING', dict(nat=int(do_nat)))
        if code == 300:
            if do_nat:
                port = int(data.split("\n")[1])
                return port == config.outgoing_udp_port
        else:
            print("Unexepcted code during PING: {}".format(code))
            print(data)
            exit(1)

    def _do_logout(self):
        if self._auth is not None:
            self._send('LOGOUT')
            Cache().remove('auth')
            self._auth = None

    def command_anime(self, aid, amask):
        code, data = self._send('ANIME', dict(aid=aid, amask=amask))
        if code == 330:
            return None
        elif code == 230:
            fields = data.split(r'|')
            return map(lambda s: s.replace('/', '|').replace('<br />', "\n").replace('<br/>', "\n"), fields)
        else:
            print("Unexpected code during ANIME: {}".format(code))
            print(data)
            exit(1)

    def command_file(self, ed2k, size, fmask, amask):
        code, data = self._send('FILE', dict(size=size, ed2k=ed2k, fmask=fmask, amask=amask))
        if code == 220:
            fields = data.split('|')
            return map(lambda s: s.replace('/', '|').replace('<br />', "\n").replace('<br/>', "\n"), fields)
        elif code == 320:
            return None
        elif code == 322:
            print("Multiple files found!")
            return None
        else:
            print("Unexpected code during FILE: {}".format(code))
            print(data)
            exit(1)

    def command_group(self, gid):
        code, data = self._send('GROUP', dict(gid=gid))
        if code == 250:
            fields = data.split('|')
            return map(lambda s: s.replace('/', '|').replace('<br />', "\n").replace('<br/>', "\n"), fields)
        elif code == 350:
            print("No such group: {}".format(gid))
            return None
        else:
            print("Unexpected code during GROUP: {}".format(code))
            print(data)
            exit(1)

    def command_mylist_add(self, fid, **kwargs):
        code, data = self._send('MYLISTADD', dict(fid=fid, **kwargs))
        if code == 320:
            print("No such file: {}".format(fid))
            exit(1)
        elif code == 330:
            print("Should not happen: not such anime")
        elif code == 350:
            print("Should not happen: no such group")
        elif code == 210:
            lid = data.split("\n")[1]
            print("Added to myList with id {}".format(lid))
        elif code == 310:
            lid = data.split("\n")[1].split('|')[0]
            print("Already in myList with id {}".format(lid))
        elif code == 322:
            print("Should not happen: Multiple files found")
        else:
            print("Unexpected code during MYLISTADD: {}".format(code))
            print(data)
            exit(1)
