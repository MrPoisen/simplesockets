import secrets
import string

from typing import Tuple


class Key:
    def __init__(self, key: bytes):
        self.__key: bytes = key

    @property
    def key(self) -> bytes:
        return self.__key

    def __int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    def __int_from_bytes(self, xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')

    def encrypt(self, data: bytes):
        pos = 0
        encrypted = []
        for element in data:
            as_int = element
            as_int = (as_int + self.__key[pos]) % 256
            pos = (pos + 1) % len(self.__key)
            encrypted.append(self.__int_to_bytes(as_int))

        return b''.join(encrypted)

    def decrypt(self, data: bytes):
        pos = 0
        encrypted = []
        for element in data:
            as_int = element
            as_int = (as_int - self.__key[pos]) % 256
            pos = (pos + 1) % len(self.__key)
            encrypted.append(self.__int_to_bytes(as_int))

        return b''.join(encrypted)

    def show_int(self, element: bytes):
        return self.__int_from_bytes(element)

    def show_bytes(self, element: int):
        return self.__int_to_bytes(element)


class Pad:
    def __init__(self, key: Key, beginn_pad: Tuple[int, int] = (10, 30), end_pad: Tuple[int, int] = (10, 30)):
        self.__key = key
        self.__beginn_pad = beginn_pad[0] + secrets.randbelow(beginn_pad[1] - beginn_pad[0])
        self.__end_pad = end_pad[0] + secrets.randbelow(end_pad[1] - end_pad[0])

    def encrypt(self, data: bytes):
        paddad = self.__padding(data, self.__beginn_pad, self.__end_pad)

        return self.__key.encrypt(paddad)

    def decrypt(self, data: bytes):
        decr = self.__key.decrypt(data)
        return self.__unpad(decr, self.__beginn_pad, self.__end_pad)
        #return decr

    def __padding(self, data: bytes, beginn_pad: int, end_pad: int) -> bytes:
        random_start = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase +string.digits) for _ in range(beginn_pad)).encode()
        random_end = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(end_pad)).encode()
        return b''.join([random_start, data, random_end])

    def __unpad(self, data: bytes, beginn_pad: int, end_pad: int):
        return data[beginn_pad:end_pad]

    @property
    def bytes(self):
        return f'b={self.__beginn_pad}|k={self.__key.key}|e={self.__end_pad}'.encode()

def import_pad(pad_: bytes):
    list_ = []
    for element in pad_.split(b'|'):
        list_.append(element[2:])

    if len(list_) != 3:
        raise ValueError("Cant import pad")

    return Pad((list_[0], list_[0]+1), Key(list_[1]), (list_[2], list_[2]+1))

def get_key(key_length: int = 256):
    key = secrets.randbits(key_length)
    return Key(key.to_bytes((key.bit_length() + 7) // 8, 'big'))

def bytes_to_bites(byte_: bytes):
    return byte_ * 8


