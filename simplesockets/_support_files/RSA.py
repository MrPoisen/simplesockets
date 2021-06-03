import secrets
import random
import os
from typing import Union
import json
import pkgutil

from simplesockets._support_files import error


class RSA_PUBLIC_KEY:
    """
    This class allows the encryption of data with RSA

    Attributes:
        self.n (int): n
        self.e (int): e
        self.bytes (bytes): represents the key, encoded with base64
    """
    def __init__(self, n: int, e: int):
        self.__n: int = n
        self.__e: int = e

    def __str__(self):
        return f'Public RSA Key:\nn:{self.__n}\ne:{self.__e}'

    def __repr__(self):
        return f'n={self.__n}, e={self.__e}'

    @property
    def n(self):
        return self.__n

    @property
    def e(self):
        return self.__e

    def __int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    def __int_from_bytes(self, xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')

    def encrypt(self, data: bytes, padding: int = 0, padding_length: int = 16) -> bytes:
        """

        Args:
            data: data to be encrypted
            padding: 0 for False, 1 for True
            padding_length: padding length

        Returns:
            returns the encrypted data

        Raises:
            ValueError: if padding isn't 0 or 1 or the data is to large for the key

        """

        if padding is 0:
            data: bytes = b''.join([b'\x00\x02', data])
        elif padding is 1:
            data = self.__padding(data, padding_length)
        else:
            ValueError("padding must be 0 for False or 1 for True")
        int_: int = self.__int_from_bytes(data)

        if int_ > self.__n:
            raise ValueError("The to encrypting data can't be larger than the key")

        encr = pow(int_, self.__e, self.__n)
        return self.__int_to_bytes(encr)

    def __padding(self, data: bytes, length: int = 16) -> bytes:
        padding = b''
        padding_length = len(data) % length

        if padding_length + len(data) >= self.__n:
            padding_length = padding_length+len(data) - self.__n

        while len(padding) < padding_length:
            nedded = padding_length - len(padding)

            to_use = os.urandom(nedded)
            to_use = to_use.replace(b'\x00', b'')
            padding += to_use[:nedded]

        return b''.join([b"\x00\x02", padding, b"\x00\x02", data])

    @property
    def bytes(self):
        import base64
        s = f'n={self.__n}|e={self.__e}'.encode()
        return base64.b64encode(s)

    def unofficial_export(self):
        """
        Exports the key but doesn't follows any conventions

        Returns:
            returns bytes object containing information about the class

        """
        b = self.bytes
        s = f'-----BEGIN RSA PUBLIC KEY-----\n{b}\n-----END RSA PUBLIC KEY-----'
        return s.encode()


class RSA_PRIVATE_KEY:
    """
        This class allows the decryption of data with RSA

        Attributes:
            self.p (int): p
            self.q (int): q
            self.n (int): n
            self.d (int): d
            self.e (int): e
        """
    def __init__(self, p, q, n, d, e):
        self.__p = p
        self.__q = q
        self.__n = n
        self.__d = d
        self.__e = e

    def __str__(self):
        return f'Private RSA Key:\nn:{self.__n}\nd:{self.__d}'

    def __int_from_bytes(self, xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')

    def __int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    def decrypt(self, data: bytes, padding: int = 0) -> bytes:
        """

        Args:
            data: data to be decrypted
            padding: 0 for False, 1 for True

        Returns:
            returns dercypted bytes object

        Raises:
            ValueError: If the data is larger then the key can decrypt or If the padding Value isn't 0 or 1

        """
        data = self.__int_from_bytes(data)

        if data > self.__n:
            raise ValueError("The to encrypting data can't be larger than the key")

        decr = pow(data, self.__d, self.__n)
        bytes_ = self.__int_to_bytes(decr)
        if padding is 0:
            return bytes_[1:]
        elif padding is 1:
            return self.__unpad(bytes_)
        else:
            raise ValueError("Error")

    def __unpad(self, data: bytes):
        pad, data = data.split(b'\x00\x02')
        return data

    def public_key(self) -> RSA_PUBLIC_KEY:
        """
        creates and returns a RSA Public Key

        Returns:
            returns a RSA Public Key

        """
        return RSA_PUBLIC_KEY(self.__n, self.__e)

    @property
    def p(self):
        return self.__p

    @property
    def q(self):
        return self.__q

    @property
    def n(self):
        return self.__n

    @property
    def e(self):
        return self.__e

    @property
    def d(self):
        return self.__d

    def unofficial_export(self):
        """
        Exports the key but doesn't follows any conventions

        Returns:
            returns bytes object containing information about the class

        """
        import base64
        b = f'p={self.__p}|q={self.__q}|n={self.__n}|d={self.__d}|e={self.__d}'.encode()
        b = base64.b64encode(b)
        s = f'-----BEGIN RSA PRIVATE KEY-----\n{b}\n-----END RSA PRIVATE KEY-----'
        return s.encode()


def import_public_bytes(key_info: bytes):
    import base64
    s = base64.b64decode(key_info)

    n, e = s.split(b'|')
    n = n.strip(b'n=')
    e = e.strip(b'e=')
    return RSA_PUBLIC_KEY(int(n), int(e))

def get_prime_list():
    #print(os.listdir(os.getcwd()))
    #return [2, 3, 5, 7, 9]
    #data = pkgutil.get_data(__name__, "primes.json")
    #return json.loads(data)
    from simplesockets._support_files import PRIMES
    return PRIMES.copy()

def get_single_key(primes_list, length: int = 1024):
    """
    generates a prime number

    Args:
        primes_list: list of primes
        length: the size of the prime in bits

    Returns:
        returns an prime int

    """
    def random_bit_number_odd(size: int = 2048):
        l = secrets.randbits(size)
        while pow(l, 1, 2) == 0:
            l += 1
        return l

    def check_first_primes(n: int):
        for prime_ in primes_list:
            if pow(n, 1, prime_) == 0:
                return False
        return True

    def fermit_test(n: int, k: int = 10):
        for _ in range(k):
            a = random.randint(2, n - 2)
            pow_ = pow(a, n - 1, n)
            if pow_ != 1:
                return False
        return True

    def Miller_Rabin_test(n: int, k: int):
        r, s = 0, n - 1
        while pow(s, 1, 2) == 0:
            r += 1
            s = divmod(s, 2)[0]
            #s //= 2
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, s, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    prime = False

    while not prime:
        number = random_bit_number_odd(length)
        if check_first_primes(number) is False:
            continue

        """if fermit_test(number, 5) is False:
            print("fermit test", number)
            #number += 2
            continue"""

        if Miller_Rabin_test(number, 10) is False:
            continue
        prime = True

    return number

def get_private_key(key_length: int = 2048, p: int = None, q: int = None) -> RSA_PRIVATE_KEY:
    """
    Creates and Returns a RSA Public Key

    Args:
        key_length: bit length of the key, it should be even
        p: when given, p will be used as p in calculating the RSA Key
        q: when given, q will be used as q in calculating the RSA Key

    Returns:
        returns a RSA Private Key

    Raises:
        ValueError: If the key_length is odd | If the given Values of p and q are the same
        RSACalcKeyError: If calculating d of the RSA Key resulted in an invalid d value

    """

    if isinstance(q, int) and p == q:
        raise ValueError("p and q can't have the same Value")

    primes_list = get_prime_list()

    if key_length % 2 != 0:
        raise ValueError("key length must be even")

    def get_e(phi_: int):
        e = 65537
        while pow(phi_, 1, e) == 0:
            e += 1
        return e

    def check_d(phi__: int, d: int, e: int):
        return pow(e * d, 1, phi__) == 1

    def get_d(phi___, e):
        top1, top2 = phi___, phi___
        c1, c2 = e, 1  # set collum 1 and 2
        while True:
            temp = top1 // c1
            lower_c1, lower_c2 = top1 - (c1 * temp), top2 - (c2 * temp)
            if lower_c1 < 0:
                lower_c1 = pow(lower_c1, 1, phi___) #lower_c1 % phi___
            if lower_c2 < 0:
                lower_c2 = pow(lower_c2, 1, phi___) #lower_c2 % phi___
            top1, top2 = c1, c2
            c1, c2 = lower_c1, lower_c2
            if c1 == 1:
                return c2

    if isinstance(p, int) is False:
        p = get_single_key(primes_list, key_length // 2)
    if isinstance(q, int) is False:
        q = get_single_key(primes_list, key_length // 2)

    if p == q:
        while p == q:
            q = get_single_key(primes_list, key_length//2)

    n = p * q
    phi = (p - 1) * (q - 1)
    e = get_e(phi)
    d = get_d(phi, e)

    if check_d(phi, d, e) is False:
        raise error.RSACalcKeyError("Calculating d resulted in an Error")

    return RSA_PRIVATE_KEY(p, q, n, d, e)


def import_key(key: bytes) -> Union[RSA_PUBLIC_KEY, RSA_PRIVATE_KEY]:
    """
    Imports an exported RSA Key

    Args:
        key: the key as an bytes object

    Returns:
        returns an RSA Public or Private Key

    Raises:
        RSAImportKeyError: If the key type couldn't be identified

    """

    if '-----BEGIN RSA PRIVATE KEY-----' in key.decode():
        import base64
        key = key.strip(b'-----BEGIN RSA PRIVATE KEY-----\nb')
        key = key.strip(b"\n'-----END RSA PRIVATE KEY-----")
        dec_ = base64.b64decode(key)

        info = []

        for part in dec_.split(b'|'):
            info.append(part[2:])

        return RSA_PRIVATE_KEY(int(info[0]), int(info[1]), int(info[2]), int(info[3]), int(info[4]))

    elif '-----BEGIN RSA PUBLIC KEY-----' in key.decode():
        import base64
        key = key.strip(b'-----BEGIN RSA PUBLIC KEY-----\nb')
        key = key.strip(b"\n'-----END RSA PUBLIC KEY-----")
        dec_ = base64.b64decode(key)
        info = []

        for part in dec_.split(b'|'):
            info.append(part[2:])
        return RSA_PUBLIC_KEY(int(info[0]), int(info[1]))
    else:
        raise error.RSAImportKeyError("Couldn't identify key")


if __name__ == "__main__":
    import time
    start_time = time.time()
    key = get_private_key(2024)
    end_time = time.time() - start_time

    print(key)
    print("p:", key.p)
    print("q:", key.q)
    print(f"time taken: {end_time} seconds, {end_time*1000} milliseconds, {end_time/60} minutes")
