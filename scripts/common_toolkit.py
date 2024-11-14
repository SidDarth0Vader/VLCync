import re
import secrets
from xmltodict import parse
from ipaddress import ip_address, IPv4Address


class ClsCommonToolkit:
    @staticmethod
    def verify_request(func):
        def inner(self, section, option, default=None):
            if not self.config.has_section(section):
                if default is not None:
                    return default
                raise Exception("Invalid section")

            if not self.config.has_option(section, option):
                if default is not None:
                    return default

                raise Exception(
                    f"Invalid option, \"{option}\", for section \"{section}\""
                )

            otpt = func(self, section, option)

            if not len(otpt):
                return None

            return otpt

        return inner

    @staticmethod
    def is_valid_username(usn):
        if len(usn) < 3 or len(usn) > 15:
            raise Exception(
                f"Invalid Username: Username, {repr(usn)}, "
                "must be between 3 and 15 characters long"
            )

        if len(re.findall(r"[^a-zA-Z0-9-_]+", usn)):
            raise Exception(
                f"Invalid Username: Username, {repr(usn)}, "
                f"{len(re.findall(r'[^a-zA-Z0-9-_]+', usn))}, must not contain"
                " anything other than upper & lower case english characters, "
                "numbers, hyphens and underscores"
            )

    @staticmethod
    def is_valid_ip(ip):
        if ':' not in ip:
            raise Exception("Invalid IP: \":\" missing")

        addr, port = ip.rsplit(":", 1)

        addr = ip_address(addr)
        port = int(port)

        if not isinstance(addr, IPv4Address):
            raise Exception("Invalid IP: Not an IPV4 address")

        if port >= 2**16 or port < 0:
            raise Exception("Invalid IP: Port must be in range 0-65535")

    @staticmethod
    def split_addr(addr):
        return addr.rsplit(":", 1)

    @staticmethod
    def parse_xml(xml):
        return parse(xml).get("root", {})

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(64)
