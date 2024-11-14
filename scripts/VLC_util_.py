import os
import errno
import ctypes
import socket
import subprocess
from time import sleep
from threading import Thread

from scripts.logger import VLCync_Logger


class ClsVLCUtil:
    TARG_ADDR = "127.0.0.1"
    TARG_PORT = 44500
    TIMEOUT = 0.01
    STATUS_CHECK_INTERVAL = 1
    DIFF_THRESHOLD = 1

    def __init__(self, config, connection_handler):
        self.logger = VLCync_Logger.get_logger('Client')
        self.timestamp = 0
        self.connection_handler = connection_handler
        self.playback = False
        self.vlcdir = config.getValue("default", "vlcdir")
        self.statThread = None
        self._validate()

    def open_file(self, file_path):
        vlc_args = (
            f"--extraintf rc --rc-host {self.TARG_ADDR}:{self.TARG_PORT}"
        )
        if os.name == "nt":
            os.startfile(self.vlcdir, arguments=f"{vlc_args} --rc-quiet")
        else:
            subprocess.Popen(["vlc", *file_path.split(), "--quiet"])

        self.playback = True
        self.paused = False
        self._vlc_transceiver(f"add {file_path}")
        self._timeKeeper()
        self.statThread = Thread(target=self._statusRetriever, daemon=True)
        self.statThread.start()

    def outside_input(self, msg):
        self._vlc_transceiver(msg)

    def _parse(self, msg):
        msg = msg.split("\r\n")[:-1]

        for line in msg:
            if "status change" in line:
                if "pause" in line:
                    self.paused = True
                    self.connection_handler.send("pause", True)

                if "play" in line:
                    self.paused = False
                    self.connection_handler.send("pause", True)

            if line.isnumeric():
                self._timeKeeper(int(line))

    def _statusRetriever(self):
        self._timeKeeper()
        while self.playback:
            response = self._vlc_transceiver("get_time")
            # self.logger.debug(f"{response = }")
            if not response:
                break

            self._parse(response)
            sleep(self.STATUS_CHECK_INTERVAL)

    def _timeKeeper(self, time=None):
        if time is None:
            self.previous_time = 0
            return

        diff = time-self.previous_time
        # self.logger.debug(f"{diff = }")
        if diff <= 1 and diff >= 0:
            self.previous_time = time
            return

        self.connection_handler.send(f"seek {time}", True)
        self.previous_time = time
        return

    def _vlc_transceiver(self, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.TARG_ADDR, self.TARG_PORT))
                sock.settimeout(self.TIMEOUT)
                response = ""
                received = ""
                sock.sendall(bytes(f"{msg}\n", "utf-8"))
                while True:
                    try:
                        received = sock.recv(1024).decode()
                        response += received

                    except TimeoutError:
                        # self.logger.debug("TimedOut temp connection")
                        break

                    except IOError as e:
                        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                            self.logger.error(f"Reading error: {str(e)}")
                            raise e
                        continue

                return response

            except ConnectionRefusedError:
                self.playback = False
                return False

    def _validate(self):
        if os.name == "nt":
            if os.path.exists(self.vlcdir):
                return

            ctypes.windll.user32.MessageBoxW(
                0, (
                    u"Unable to locate VLC media player executable."
                    "\nPlease correct directory in config."
                ),
                u"VLCync error", 0
            )
            raise FileNotFoundError(
                "Unable to locate VLC media player executable"
            )

        elif os.name == "posix":
            pass
