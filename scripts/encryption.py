from Crypto.Cipher import AES
from Crypto.Hash import SHA256

class ClsEncryptTool:
    def __init__(self, key:str):
        self.key = SHA256.new(str(key).encode()).digest()

    def encrypt(self, msg):
        cipher = AES.new(self.key, AES.MODE_GCM)
        nonce = cipher.nonce
        cipher_text, tag = cipher.encrypt_and_digest(msg)#.encode('UTF-8'))
        return nonce, cipher_text, tag

    def decrypt(self, nonce, cipher_text, tag):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        plain_text = cipher.decrypt(cipher_text)
        try:
            cipher.verify(tag)
            return plain_text#.decode('UTF-8')
        except:
            return False