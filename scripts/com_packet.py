import pickle
from dataclasses import dataclass


@dataclass
class CommPacket:
    username: str
    message: str
    forVLC: bool

    @staticmethod
    def create_packet(usn, message, forVLC):
        return CommPacket(usn, message, forVLC)

    @staticmethod
    def unravel_packet(pack):
        return pack.username, pack.message, pack.forVLC

    @staticmethod
    def to_stream(config, codec, pack, init=False):
        nonce, cipher_text, tag = codec.encrypt(
            pickle.dumps(CommPacket.create_packet(*pack))
        )
        enc_stream = nonce+tag+cipher_text
        if not init:
            return (
                f"{len(enc_stream):<{config.header_size}}".encode('utf-8') +
                enc_stream
            )
        return enc_stream

    @staticmethod
    def from_stream(enc_stream, codec):
        nonce = enc_stream[:16]
        tag = enc_stream[16:32]
        cipher_text = enc_stream[32:]
        dec_stream = codec.decrypt(nonce, cipher_text, tag)
        if dec_stream:
            return CommPacket.unravel_packet(pickle.loads(dec_stream))

        raise Exception("Failed to decrypt")
