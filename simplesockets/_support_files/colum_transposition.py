import os
from collections import OrderedDict
from simplesockets._support_files import error


def _int_to_bytes(x: int) -> bytes:
    if x != 0:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')
    else:
        return b'\x00'


def _int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')


class Transposition:
    def __init__(self, key: bytes, check=True):
        """

        Args:
            key: the key
            check: if the key should be checked if it is valid, if not will raise an Exception

        Raises:
            RepeatingValueError: If a value of the key exists more then 1 time in the key
            NoEffectError: If the key would have no affect on the to be encrypted data
        """
        self.__key = key

        if len(key) <= 1:
            raise ValueError("The key must be larger then 1")

        if check:
            temp = 0
            lower_follow_value = 0

            for byte in key:
                if len(key.split(_int_to_bytes(byte))) != 2:
                    raise error.RepeatingValueError("The key is invalid, there is a repeating value")
                if byte < temp:
                    lower_follow_value += 1
                temp = byte

            if lower_follow_value == 0:
                for v in key:
                    print(v)
                raise error.NoEffectError("The key is invalid")


    def __str__(self):
        return f'key={self.key}'

    def __repr__(self):
        return f'{self.key}'

    @property
    def key(self):
        return self.__key

    def _encrypt(self, data: bytes):
        columns = {}

        key_length = len(self.__key)

        position = 0

        for element in data:
            if self.__key[position] in columns.keys():
                columns[(self.__key[position])].append(_int_to_bytes(element))
            else:
                columns[self.__key[position]] = [_int_to_bytes(element)]

            position = (position + 1) % key_length

        sorted_ = OrderedDict(sorted(columns.items()))

        encrypted = b''
        listed = []
        for list_ in sorted_.values():
            listed.append(list_)

        position = 0

        to_multiply = len(data) // key_length if (len(data) // key_length) % key_length == 0 and (len(data) // key_length) != 0 else (len(data) // key_length) + 1
        range_ = to_multiply * key_length

        for index in range(range_):
            index = index % key_length
            try:
                encrypted += listed[index][position]
            except IndexError:
                pass

            if (index + 1) == key_length and index != 0:
                position += 1

        return encrypted

    def _decrypt(self, data: bytes):

        def split_(to_split: bytes, length: int) -> list:
            range_ = len(to_split) // length if len(to_split) % length == 0 else (len(to_split) // length) + 1
            splited = [[] for _ in range(range_)]
            position = 0
            for index, element in enumerate(to_split):
                try:
                    splited[position].append(_int_to_bytes(element))
                except IndexError:
                    pass
                if (index + 1) % length == 0 and index != 0:
                    position += 1
            return splited

        def create_transposition_table(key_: bytes) -> dict:
            table = {}
            listed = []

            for byte_ in key_:
                listed.append(byte_)

            listed.sort()

            for index, key_value in enumerate(key_):
                table[index] = listed.index(key_value)
            return table

        key = self.__key

        key_length = len(self.__key)

        to_decrypt: list = split_(data, key_length)
        table = create_transposition_table(key)

        decrypted = b''
        rest = len(data) % key_length
        for list_ in to_decrypt:
            if len(list_) != key_length:
                temp_table = create_transposition_table(key[:rest])
                for value in temp_table.values():
                    try:
                        decrypted += list_[value]
                    except IndexError:
                        pass
            else:
                for value in table.values():
                    try:
                        decrypted += list_[value]
                    except IndexError:
                        pass
        return decrypted

    def encrypt(self, data: bytes, times: int = 1) -> bytes:
        """
        encrypts data

        Args:
            data: data to be encrypted
            times: how often it should be encrypted

        Returns:
            returns decrypted key

        Raises:
            NotEncryptedError: If the encrypted data is the same as the not encrypted one

        """
        start_data = data
        for _ in range(times):
            data = self._encrypt(data)

        if start_data == data:
            raise error.NotEncryptedError("The encrypted data is the same as the not encrypted one")
        return data

    def decrypt(self, data: bytes, times: int = 1) -> bytes:
        """
        decrypts data

        Args:
            data: data to be decrypted
            times: how often it should be decrypted

        Returns:
            returns decrypted key

        """
        for _ in range(times):
            data = self._decrypt(data)
        return data


def get_key(size: tuple = (2, 257)) -> Transposition:
    """
    creates an key for column transposition
    
    Args:
        size: range for the length of the key

    Returns:
        returns a Transposition class

    Raises:
        ValueError: If the size is not between 1 and 257 (included)

    """
    import secrets

    if size[0] < 2 or size[1] > 257:
        raise ValueError("size must be between 1 and 257 (included) ")

    key = []
    size = size[0] + secrets.randbelow(size[1] - size[0])
    to_generate = size

    temp = 0
    lower_follow_value = 0

    while len(key) < size:
        generated = os.urandom(to_generate)
        for element in generated:
            element_byte = _int_to_bytes(element)
            if element_byte not in key:
                if element < temp: # for valid key, there must be a big value followed by a small one
                    lower_follow_value += 1
                temp = element
                key.append(element_byte)
                to_generate -= 1
            else:
                continue
    if lower_follow_value == 0:
        return get_key(size)
    return Transposition(b''.join(key), True)
