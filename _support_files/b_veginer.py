import secrets
import os
from typing import Tuple
import simplesockets._support_files.error as error


class Key:
    def __init__(self, key: bytes):
        self.__key: bytes = key

    def __eq__(self, other):
        return other.key == self.__key

    def __str__(self):
        return str(self.__int_from_bytes(self.key))

    @property
    def key(self) -> bytes:
        return self.__key

    def __int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'little')

    def __int_from_bytes(self, xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'little')

    def encrypt(self, data: bytes):
        pos = 0
        encrypted = []
        for element in data:
            as_int = element
            as_int = (as_int + self.__key[pos]) % 256
            pos = (pos + 1) % len(self.__key)
            if as_int == 0:
                encrypted.append(b'\x00')
            encrypted.append(self.__int_to_bytes(as_int))

        return b''.join(encrypted)

    def decrypt(self, data: bytes):
        pos = 0
        decrypted = []
        for element in data:
            as_int = element
            as_int = (as_int - self.__key[pos]) % 256
            pos = (pos + 1) % len(self.__key)
            decrypted.append(self.__int_to_bytes(as_int))

        return b''.join(decrypted)

    def show_int(self, element: bytes):
        return self.__int_from_bytes(element)

    def show_bytes(self, element: int):
        return self.__int_to_bytes(element)


class Pad:
    def __init__(self, key: Key, beginn_pad: Tuple[int, int] = (10, 30), end_pad: Tuple[int, int] = (10, 30)):
        self.__key = key
        self.__beginn_pad = beginn_pad
        self.__end_pad = end_pad

    def __eq__(self, other):
        return other.bytes == self.bytes

    def __str__(self):
        return self.bytes.decode()

    def __repr__(self):
        return self.bytes.decode()

    def encrypt(self, data: bytes):
        beginn_pad = self.__beginn_pad[0] + secrets.randbelow(self.__beginn_pad[1] - self.__beginn_pad[0])
        end_pad = self.__end_pad[0] + secrets.randbelow(self.__end_pad[1] - self.__end_pad[0])
        paddad = self.__padding(data, beginn_pad, end_pad)

        return self.__key.encrypt(paddad)

    def decrypt(self, data: bytes):
        decr = self.__key.decrypt(data)
        return self.__unpad(decr)

    def __padding(self, data: bytes, beginn_pad: int, end_pad: int) -> bytes:
        random_start = os.urandom(beginn_pad)
        random_end = os.urandom(end_pad)
        return b''.join([random_start, b'\x02\x02pad', data, b'\02\x02pad', random_end])

    def __unpad(self, data: bytes):
        s = data.split(b'\x02\x02pad')
        if len(s) != 3:
            raise error.VPadError("Could't unpad")
        return s[1]

    @property
    def bytes(self):
        return b''.join([b'b=', str(self.__beginn_pad).encode(), b'||k=', self.__key.key, b'||e=', str(self.__end_pad).encode()])


def import_pad(pad_: bytes):
    list_ = []
    for element in pad_.split(b'||'):
        list_.append(element[2:])

    if len(list_) != 3:
        raise ValueError("Can't import pad, couldn't find needed information")

    return Pad(Key(list_[1]), tuple(list_[0]), tuple(list_[2]))


def get_key(key_length: int = 256):
    key = secrets.randbits(key_length)
    return Key(key.to_bytes((key.bit_length() + 7) // 8, 'little'))


def bytes_to_bites(byte_: bytes):
    return byte_ * 8
