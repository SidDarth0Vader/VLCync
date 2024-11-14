import os
import ctypes
from configparser import ConfigParser
from scripts.common_toolkit import ClsCommonToolkit as CTK


class ClsConfigParser:
    def __init__(self) -> None:
        self.configFileName = "config.ini"
        self.config = ConfigParser()
        if not os.path.exists(self.configFileName):
            ctypes.windll.user32.MessageBoxW(
                0,
                u"Config file not found.\nGenerating fresh config.",
                u"VLCync error",
                0
            )
            self.generate_fresh_config()

        self.config.read(self.configFileName)

    def __enter__(self):
        return self

    @CTK.verify_request
    def get_value(self, section, option):
        return self.config.get(section, option)

    def disp_config(self):
        for sec in self.config.sections():
            print(f"[{sec}]")
            for ele in list(self.config[sec]):
                print(f"{ele}={self.config[sec][ele]}")
            print()

    def save_username(self, value):
        self.add_to_config("username", value)

    def save_server_addr(self, value):
        addr, port = CTK.split_addr(value)
        self.add_to_config("serverip", addr)
        self.add_to_config("serverport", port)

    def add_to_config(self, option, value):
        self.set_config_value("user-gen", option, value)

    def set_config_value(self, section: str, option: str, value):
        if not self.config.has_section(section):
            self.config.add_section(section.lower())

        self.config.set(section, option.lower(), value)

    def generate_fresh_config(self):
        self.config.read_dict({
            "default": {
                "serverip": "127.0.0.1",
                "serverport": 42000,
                "vlcdir": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                "module": "http"
            },
            "user-gen": {
                "username": "new_user",
                "serverip": "127.0.0.1"
            }
        })
        self.save_config()

    def save_config(self):
        if self.config.has_section("user-gen"):
            for option in self.config.options("user-gen"):
                if not self.config.has_option("default", option):
                    continue

                if (
                    not self.config["default"][option] ==
                    self.config["user-gen"][option]
                ):
                    continue

                self.config.remove_option("user-gen", option)

        with open(self.configFileName, "w") as cnfg:
            self.config.write(cnfg)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.save_config()
