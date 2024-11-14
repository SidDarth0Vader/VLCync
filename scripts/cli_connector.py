import errno
import socket

from scripts.com_packet import CommPacket
from scripts.logger import VLCync_Logger
from scripts.encryption import ClsEncryptTool


class ClsCliConnector:
    def __init__(self, config):
        self.logger = VLCync_Logger.get_logger('Client')
        self.config = config
        # self.codec = ClsEncryptTool(key)
        self.isConnected = False

        self.def_usn = config.getValue("user-gen", "username", "")
        self.def_host = config.getValue("user-gen", "serverip", "")
        self.def_port = config.getValue("user-gen", "serverport", "")

        if not len(self.def_host):
            self.def_host = config.getValue("default", "serverip", "")

        if not len(self.def_port):
            self.def_port = config.getValue("default", "serverport", "")

    def __enter__(self):
        return self

    def defaultAddr(self):
        if (not len(self.def_host)) and (not len(self.def_port)):
            return ""
        return f"{self.def_host}:{self.def_port}"

    def connect(self, host, port, usn):
        self.cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cli_sock.connect((host, int(port)))
        self.cli_sock.setblocking(False)
        self.logger.info("Established connection with server")
        # stream = None
        while True:
            try:
                stream = self.cli_sock.recv(1024)
                if not len(stream):
                    raise Exception(
                        "Established connection but no response from server, "
                        "the server might have crashed"
                    )
                break
            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                continue

            except Exception as e:
                self.logger.exception(e)
                break

        _, msg, _ = CommPacket.from_stream(stream, self.codec)

        msg = msg.split("=")
        if msg[0] == "HEADER_SIZE":
            self.config.header_size = int(msg[1].strip())

        self.logger.info("Received session header from server")
        self.cli_sock.send(
            CommPacket.to_stream(self.config, self.codec, (usn, None, False))
        )

        while True:
            try:
                stream = self.receive()

                if stream is True:
                    continue

                if stream is False:
                    raise Exception(
                        "Connection unexpectedly broken, try again"
                    )

                _, msg, _ = stream
                if "Welcome to the server" not in msg:
                    raise Exception(msg)

                self.usn = usn
                self.isConnected = True
                return stream

            except Exception as e:
                self.logger.exception(e)
                raise e

    def disconnect(self):
        self.isConnected = False
        self.cli_sock.close()
        self.logger.info("Socket closed upon connection termination")

    def receive(self):
        try:
            msg_len = self.cli_sock.recv(self.config.header_size)
            if not len(msg_len):
                return False
            stream = self.cli_sock.recv(int(msg_len.decode('utf-8').strip()))
            return CommPacket.from_stream(stream, self.codec)

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                self.logger.error(f"Reading error: {str(e)}")
                raise e
            return True

    def send(self, msg, for_vlc):
        self.cli_sock.send(
            CommPacket.to_stream(
                self.config, self.codec, (self.usn, msg, for_vlc)
            )
        )

    def setKey(self, key):
        self.codec = ClsEncryptTool(key)
        self.logger.debug(f"{self.codec.key=}")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if hasattr(self, "cli_sock"):
            self.isConnected = False
            self.cli_sock.close()
            self.logger.info("Socket closed upon exit")
