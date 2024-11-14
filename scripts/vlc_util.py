from abc import ABC, abstractmethod
import ctypes
import os


class ClsVLCUtil(ABC):
    @abstractmethod
    def begin_playback(self, file_path):
        pass

    def outside_input(self, msg):
        pass

    @abstractmethod
    def _parse(self, msg):
        pass

    @abstractmethod
    def _status_retriever(self):
        pass

    @abstractmethod
    def _vlc_transceiver(self, msg):
        pass

    def _validate(self):
        if os.name == "nt":
            if os.path.exists(self.vlcdir):
                return

            ctypes.windll.user32.MessageBoxW(
                0, (
                    u"Unable to locate VLC media player executable.\n"
                    u"Please correct directory in config."
                ), u"VLCync error", 0
            )
            raise FileNotFoundError(
                "Unable to locate VLC media player executable"
            )

        elif os.name == "posix":
            pass
