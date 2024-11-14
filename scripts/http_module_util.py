import os
import requests
from requests.exceptions import ConnectTimeout
from time import sleep
from urllib.parse import quote
from threading import Thread
from subprocess import Popen
from scripts.vlc_util import ClsVLCUtil
from scripts.logger import VLCync_Logger
from scripts.common_toolkit import ClsCommonToolkit as CTK


class HTTPmodule(ClsVLCUtil):
    TARG_ADDR = "127.0.0.1"
    TARG_PORT = 44500
    TIMEOUT = 1
    STATUS_CHECK_INTERVAL = 0.75
    DIFF_THRESHOLD = 1

    def __init__(self, config, connection_handler) -> None:
        self.logger = VLCync_Logger.get_logger('Client')
        self.connection_handler = connection_handler
        self.playback = False
        self.playing = False
        self.vlcdir = config.getValue("default", "vlcdir")
        self.statThread = None
        self.is_position_volatile = False
        self._validate()

    def outside_input(self, msg):
        if "seek" in msg:
            self.is_position_volatile = True
            self.previous_time = int(msg.split(" ")[-1])
            self._vlc_transceiver("seek", time=msg.split(" ")[-1])
            self.is_position_volatile = False

        else:
            self.playing = not self.playing
            self._vlc_transceiver("toggle_play")

    def begin_playback(self, file_path):
        if not self.playback:
            self.session_token = CTK.generate_token()
            vlc_args = " ".join([
                "--extraintf http",
                f"--http-host {self.TARG_ADDR}",
                f"--http-port {self.TARG_PORT}",
                f"--http-password {self.session_token}"
            ])

            if os.name == "nt":
                os.startfile(self.vlcdir, arguments=vlc_args)

            else:
                Popen(["vlc", *file_path.split(), "--quiet"])

            self.playback = True
            self.playing = True
            self._vlc_transceiver("begin", path=file_path)
            sleep(2)
            self._time_keeper()
            self.statThread = Thread(
                target=self._status_retriever, daemon=True
            )
            self.statThread.start()

    def update_resume_point(self):
        resp = self._vlc_transceiver()
        self.connection_handler.send(f"CURRTIME {resp.get('time')}", False)

    def _status_retriever(self):
        while self.playback:
            try:
                response = self._vlc_transceiver()

                self._parse(response)
                sleep(self.STATUS_CHECK_INTERVAL)

            except ConnectTimeout:
                self.logger.info("VLC Client closed")
                self.playback = False
                self.connection_handler.disconnect()

    def _parse(self, vlc_status):
        t_keeper = self._time_keeper(int(vlc_status.get("time")))
        self.logger.debug(f"{t_keeper=}")
        pl_state = {
            "playing": False,
            "paused": True
            }.get(vlc_status.get("state"))

        if t_keeper is not None:
            self.connection_handler.send(f"seek {t_keeper}", True)

        if pl_state != self.playing:
            self.connection_handler.send("toggle_play", True)
            self.playing = not self.playing

    def _time_keeper(self, time=None):
        if time is None:
            self.previous_time = 0
            return

        diff = abs(time-self.previous_time)
        self.logger.debug(
            f"{diff=} | {self.previous_time=} | {self.is_position_volatile=}"
        )

        if self.is_position_volatile:
            return

        if diff <= 1 and diff >= 0:
            self.previous_time = time
            return

        self.previous_time = time
        return time

    def _query_parser(self, query, **kwargs):
        query_dict = {
            "begin": (
                "in_play&input=file:///"
                f"{self._clean_path(kwargs.get('path', ''))}"
            ),
            "toggle_play": "pl_pause",
            "seek": f"seek&val={kwargs.get('time')}"
        }
        url = f"http://{self.TARG_ADDR}:{self.TARG_PORT}/requests/status.xml"

        if query is None:
            return url

        return f'{url}{quote(f"?command={query_dict.get(query)}", safe="?=&")}'

    def _vlc_transceiver(self, query=None, **kwargs):
        url_encoded_query = self._query_parser(query, **kwargs)
        response = CTK.parse_xml(requests.get(
            url_encoded_query,
            auth=("", self.session_token),
            timeout=self.TIMEOUT
            ).content)

        self.logger.debug(
            f"{response.get('state')=} | {response.get('time')=}"
        )
        return response

    def _clean_path(self, path):
        if os.name == 'nt':
            return path.replace('\\', '/')

        return path
