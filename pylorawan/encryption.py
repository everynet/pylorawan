from Cryptodome.Cipher import AES
from Cryptodome.Hash import CMAC


def aes128_cmac(key: bytes, message: bytes) -> bytes:
    cobj = CMAC.new(key, ciphermod=AES)
    cobj.update(message)

    return cobj.digest()


def aes128_encrypt(key: bytes, message: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(message)


def aes128_decrypt(key: bytes, message: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(message)


def generate_mic(key: bytes, message: bytes) -> bytes:
    return aes128_cmac(key, message)[:4]
