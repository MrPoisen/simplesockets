import secrets
import os
from typing import Tuple, Union
import simplesockets._support_files.error as error
from simplesockets._support_files.colum_transposition import Transposition, get_key, _int_to_bytes


class Key:
    def __init__(self, key: bytes):
        """
        This key encrypts based on the Vigenere cipher. This cipher should **not** be used for serious data

        Args:
            key: bytes representing the key
        """
        self.__key: bytes = key

    def __eq__(self, other):
        if isinstance(other, self) is False:
            raise NotImplementedError
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

    def encrypt(self, data: bytes) -> bytes:
        """

        Args:
            data: data to be encrypted

        Returns:
            returns encrypted data

        """
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

    def decrypt(self, data: bytes) -> bytes:
        """

        Args:
            data: data to be decrypted

        Returns:
            decrypted data

        """
        pos = 0
        decrypted = []
        for element in data:
            as_int = element
            as_int = (as_int - self.__key[pos]) % 256
            pos = (pos + 1) % len(self.__key)
            decrypted.append(self.__int_to_bytes(as_int))

        return b''.join(decrypted)


class Autokey(Key):
    def __init__(self, key: bytes):
        super().__init__(key)
        self._key_list = [byte for byte in key]

    def encrypt(self, data: bytes) -> bytes:
        """

        Args:
            data: data to be encrypted

        Returns:
            returns encrypted data

        """
        key_list = self._key_list.copy()

        encrypted = []
        for element in data:
            as_int = element
            as_int = (as_int + key_list[0]) % 256

            key_list.pop(0)
            key_list.append(element)
            if as_int == 0:
                encrypted.append(b'\x00')
            else:
                encrypted.append(_int_to_bytes(as_int))

        return b''.join(encrypted)

    def decrypt(self, data: bytes) -> bytes:
        """

        Args:
            data: data to be decrypted

        Returns:
            decrypted data

        """

        key_list = self._key_list.copy()

        encrypted = []
        for element in data:
            as_int = element
            as_int = (as_int - key_list[0]) % 256

            key_list.pop(0)
            key_list.append(as_int)

            if as_int == 0:
                encrypted.append(b'\x00')
            else:
                encrypted.append(_int_to_bytes(as_int))

        return b''.join(encrypted)


class Combined_Key(Autokey):
    """
    This class combines the Vigenere autokey with the colunm transposition
    """
    def __init__(self, vigenere_key: Key, transposition: Transposition):
        """

        Args:
            vigenere_key: The vigenere key
            transposition: The transposition key
        """
        self.__transposition_key = transposition
        super().__init__(vigenere_key.key)

    def __eq__(self, other):
        if isinstance(other, type(self)) is False:
            raise NotImplementedError
        else:
            return other.export_key() == self.export_key()

    @property
    def transposition_key(self) -> bytes:
        """

        Returns:
            returns transposition key

        """
        return self.__transposition_key.key

    @property
    def vigenere_key(self) -> bytes:
        """

        Returns:
            returns vigenere key

        """
        return self.key

    def encrypt(self, data: bytes, rounds: int = 2) -> bytes:
        """
        encrypts the data first with the vigenere autokey and then with the column transposition

        Args:
            data: data to be encrypted
            rounds: how often the column transposition will be applied

        Returns:
            returns the encrypted data

        """
        encrypted = super().encrypt(data)
        try:
            return self.__transposition_key.encrypt(encrypted, rounds)
        except Exception:
            return encrypted

    def decrypt(self, data: bytes, rounds: int = 2) -> bytes:
        """
        decrypts the data first with the column transposition and then with the vigenere autokey

        Args:
            data: data to be decrypted
            rounds: how often the column transposition will be applied

        Returns:
            returns the decrypted data

        """
        decrypted = self.__transposition_key.decrypt(data, rounds)
        return super().decrypt(decrypted)

    def export_key(self) -> bytes:
        """
        exports the key as bytes

        Returns:
            returns the exported key

        """
        bytes_ = b'v_key=' + self.key + b'|-|t_key=' + self.__transposition_key.key
        return bytes_

    @classmethod
    def import_key(cls, key: bytes):
        """
        imports the exported key

        Args:
            key: the exported key

        Returns:
            Combined_Key: returns the key as Combined_Key

        """
        decoded = key
        keys = decoded.split(b'|-|')
        if len(keys) != 2:
            raise ValueError("Wrong or invalid key")
        return Combined_Key(Key(keys[0].strip(b'v_key=')), Transposition(keys[1].strip(b't_key=')))

    @classmethod
    def get_transposition_key(cls, size: tuple = (2, 257)):
        """
        creates an column transposition key

        Args:
            size: range for the size of the key with minimum 2 and maximum 257 (included)

        Returns:
            returns a column transposition key

        """
        return get_key(size)

    @classmethod
    def get_vigenere_key(self, size: int = 32, generation_type: str = "os"):
        """
        creates a vigenere key

        Args:
            size: the size of the key
            generation_type: how the key is generated (with 'os' or 'secrets')

        Returns:
            returns a vigenere key

        """
        return get_vigenere_key(size, generation_type)

    @classmethod
    def get_combined_key(self, transposition_size: tuple = (2, 257), vigenere_size: int = 32, generation_type: str = "os"):
        """

        Args:
            transposition_size: range for the size of the transposition key with minimum 2 and maximum 257 (included)
            vigenere_size: the size of the vigenere key
            generation_type: how the vigenere key is generated (with 'os' or 'secrets')

        Returns:
            Combined_Key: returns a Combined Key

        """
        vigener_key = get_vigenere_key(vigenere_size, generation_type)
        transposition_key = get_key(transposition_size)
        return Combined_Key(vigener_key, transposition_key)

class Pad:
    def __init__(self, key: Union[Key, Autokey], begin_pad: Tuple[int, int] = (10, 30), end_pad: Tuple[int, int] = (10, 30)):
        """

        Args:
            key: the Key
            begin_pad: how much padding should be added in front of the to be encrypted data
            end_pad: how much padding should be added at the end of the to be encrypted data
        """
        self.__key = key
        self.__beginn_pad = begin_pad
        self.__end_pad = end_pad

        if begin_pad[0] >= begin_pad[1] or begin_pad[0] < 1:
            raise ValueError(
                "the first value must of begin_pad must be larger then 1 and smaller then the his second value")
        if end_pad[0] >= end_pad[1] or end_pad[0] < 1:
            raise ValueError(
                "the first value must of end_pad must be larger then 1 and smaller then the his second value")
    def __eq__(self, other):
        return other.bytes == self.bytes

    def __str__(self):
        return ''.join(['b=', str(self.__beginn_pad), '||k=', f'{self.__key.key}', '||e=', str(self.__end_pad)])

    def __repr__(self):
        return self.bytes.decode()

    def encrypt(self, data: bytes) -> bytes:
        """

        Args:
            data: data to be encrypted

        Returns:
            returns encrypted data

        """
        beginn_pad = self.__beginn_pad[0] + secrets.randbelow(self.__beginn_pad[1] - self.__beginn_pad[0])
        end_pad = self.__end_pad[0] + secrets.randbelow(self.__end_pad[1] - self.__end_pad[0])
        paddad = self.__padding(data, beginn_pad, end_pad)

        return self.__key.encrypt(paddad)

    def decrypt(self, data: bytes) -> bytes:
        """

        Args:
            data: data to be decrypted

        Returns:
            returns dercypted data

        """
        decr = self.__key.decrypt(data)
        return self.__unpad(decr)

    def __padding(self, data: bytes, beginn_pad: int, end_pad: int) -> bytes:
        random_start = os.urandom(beginn_pad)
        random_end = os.urandom(end_pad)
        return b''.join([random_start, b'\x02\x02pad', data, b'\02\x02pad', random_end])

    def __unpad(self, data: bytes):
        s = data.split(b'\x02\x02pad')
        if len(s) != 3:
            raise error.VPadError(f"Could't unpad, found {len(s)} from the padding")
        return s[1]

    @property
    def bytes(self) -> bytes:
        return b''.join([b'b=', str(self.__beginn_pad).encode(), b'||k=', self.__key.key, b'||e=', str(self.__end_pad).encode()])


def import_pad(pad_: bytes) -> Pad:
    """
    Imports a pad from bytes

    Args:
        pad_: pad as bytes

    Returns:
        returns the imported pad

    Raises:
        ValueError: If the Pad can't be imported

    """
    list_ = []
    for element in pad_.split(b'||'):
        list_.append(element[2:])

    if len(list_) != 3:
        raise ValueError("Can't import pad, couldn't find needed information")

    return Pad(Key(list_[1]), tuple(list_[0]), tuple(list_[2]))


def get_vigenere_key(key_length: int = 256, generation_type: str = "secrets") -> Key:
    """
    Creates and returns a Key

    Args:
        key_length: Key length in bits for generation_type 'secrets' or bytes for 'os'
        generation_type: how the bytes are generated

    Returns:
        returns a Key

    """
    if generation_type == "os":
        return Key(os.urandom(key_length))
    elif generation_type == "secrets":
        key = secrets.randbits(key_length)
        return Key(key.to_bytes((key.bit_length() + 7) // 8, 'little'))
    else:
        raise error.GenerationTypeError("The generation_type must be 'secrets' or 'os'")

if __name__ == "__main__":
    autokey = Autokey(os.urandom(8))
    l = (autokey.encrypt(b"TEst this"))
    print(l)
    print(autokey.decrypt(l))
