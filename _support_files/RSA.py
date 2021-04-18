import secrets
import random
import os


class RSA_Public_Key:
    def __init__(self, n, e):
        self.__n = n
        self.__e = e

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

        if padding is 0:
            data: bytes = b''.join([b'\x00\x02', data])
        elif padding is 1:
            data = self.__padding(data, padding_length)
        int_: int = self.__int_from_bytes(data)

        if int_ > self.__n:
            raise ValueError("The to encrypting data can't be larger than the key")

        encr = pow(int_, self.__e, self.__n)
        return self.__int_to_bytes(encr)

    def __padding(self, data: bytes, length: int = 16) -> bytes:
        padding = b''
        padding_length = len(data) % length

        while len(padding) < padding_length:
            nedded = padding_length - len(padding)

            to_use = os.urandom(nedded)
            to_use = to_use.replace(b'\x00', b'')
            padding += to_use[:nedded]

        return b''.join([b"\x00\x02", padding, b"\x00", data])

    @property
    def bytes(self):
        import base64
        s = f'n={self.__n}|e={self.__e}'.encode()
        return base64.b64encode(s)

    def unofficial_export(self):
        b = self.bytes
        s = f'-----BEGIN RSA PUBLIC KEY-----\n{b}\n-----END RSA PUBLIC KEY-----'
        return s


class RSA_Private_Key:
    def __init__(self, p, q, n, d, e):
        self.__p = p
        self.__q = q
        self.__n = n
        self.__d = d
        self.__e = e

    def __str__(self):
        return f'Private RSA Key:\nn:{self.__n}\nd:{self.__d}\n'

    def __int_from_bytes(self, xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')

    def __int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    def decrypt(self, data: bytes, padding: int = 0) -> bytes:
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
            raise Exception("Error")

    def __unpad(self, data: bytes):
        pad, data = data.split(b'\x00')
        return data

    def public_key(self) -> RSA_Public_Key:
        return RSA_Public_Key(self.__n, self.__e)

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
        return self.d

    def unofficial_export(self):
        import base64
        b = f'p={self.__p}|q={self.__q}|n={self.__n}|d={self.__d}|e={self.__d}'.encode()
        b = base64.b64encode(b)
        s = f'-----BEGIN RSA PRIVATE KEY-----\n{b}\n-----END RSA PRIVATE KEY-----'
        return s


def import_public_bytes(key_info: bytes):
    import base64
    s = base64.b64decode(key_info)

    n, e = s.split(b'|')
    n = n.strip(b'n=')
    e = e.strip(b'e=')
    return RSA_Public_Key(n.decode(), e.decode())


def get_private_key(key_length: int = 4096) -> RSA_Private_Key:
    primes_list = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101,
                   103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199,
                   211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317,
                   331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443,
                   449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577,
                   587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701,
                   709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839,
                   853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977, 983,
                   991, 997, 1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051, 1061, 1063, 1069, 1087, 1091, 1093,
                   1097, 1103, 1109, 1117, 1123, 1129, 1151, 1153, 1163, 1171, 1181, 1187, 1193, 1201, 1213, 1217, 1223,
                   1229, 1231, 1237, 1249, 1259, 1277, 1279, 1283, 1289, 1291, 1297, 1301, 1303, 1307, 1319, 1321, 1327,
                   1361, 1367, 1373, 1381, 1399, 1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451, 1453, 1459, 1471, 1481,
                   1483, 1487, 1489, 1493, 1499, 1511, 1523, 1531, 1543, 1549, 1553, 1559, 1567, 1571, 1579, 1583, 1597,
                   1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657, 1663, 1667, 1669, 1693, 1697, 1699, 1709, 1721,
                   1723, 1733, 1741, 1747, 1753, 1759, 1777, 1783, 1787, 1789, 1801, 1811, 1823, 1831, 1847, 1861, 1867,
                   1871, 1873, 1877, 1879, 1889, 1901, 1907, 1913, 1931, 1933, 1949, 1951, 1973, 1979, 1987, 1993, 1997,
                   1999, 2003, 2011, 2017, 2027, 2029, 2039, 2053, 2063, 2069, 2081, 2083, 2087, 2089, 2099, 2111, 2113,
                   2129, 2131, 2137, 2141, 2143, 2153, 2161, 2179, 2203, 2207, 2213, 2221, 2237, 2239, 2243, 2251, 2267,
                   2269, 2273, 2281, 2287, 2293, 2297, 2309, 2311, 2333, 2339, 2341, 2347, 2351, 2357, 2371, 2377, 2381,
                   2383, 2389, 2393, 2399, 2411, 2417, 2423, 2437, 2441, 2447, 2459, 2467, 2473, 2477, 2503, 2521, 2531,
                   2539, 2543, 2549, 2551, 2557, 2579, 2591, 2593, 2609, 2617, 2621, 2633, 2647, 2657, 2659, 2663, 2671,
                   2677, 2683, 2687, 2689, 2693, 2699, 2707, 2711, 2713, 2719, 2729, 2731, 2741, 2749, 2753, 2767, 2777,
                   2789, 2791, 2797, 2801, 2803, 2819, 2833, 2837, 2843, 2851, 2857, 2861, 2879, 2887, 2897, 2903, 2909,
                   2917, 2927, 2939, 2953, 2957, 2963, 2969, 2971, 2999, 3001, 3011, 3019, 3023, 3037, 3041, 3049, 3061,
                   3067, 3079, 3083, 3089, 3109, 3119, 3121, 3137, 3163, 3167, 3169, 3181, 3187, 3191, 3203, 3209, 3217,
                   3221, 3229, 3251, 3253, 3257, 3259, 3271, 3299, 3301, 3307, 3313, 3319, 3323, 3329, 3331, 3343, 3347,
                   3359, 3361, 3371, 3373, 3389, 3391, 3407, 3413, 3433, 3449, 3457, 3461, 3463, 3467, 3469, 3491, 3499,
                   3511, 3517, 3527, 3529, 3533, 3539, 3541, 3547, 3557, 3559, 3571]

    if key_length % 2 != 0:
        raise ValueError("key length must be even")

    def get_single_key(length: int = 2048):
        def random_bit_number_odd(size: int = 4096):
            l = secrets.randbits(size)
            while l % 2 == 0:
                l = secrets.randbits(size)
            return l

        def check_first_primes(n: int):
            return n not in primes_list

        def fermit_test(n: int, k: int = 10):
            for _ in range(k):
                a = random.randint(2, n - 2)
                pow_ = pow(a, n - 1, n)
                if pow_ != 1:
                    return False
            return True

        def Miller_Rabin_test(n: int, k: int):
            r, s = 0, n - 1
            while s % 2 == 0:
                r += 1
                s //= 2
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
            if fermit_test(number, 5) is False:
                continue
            if Miller_Rabin_test(number, 5) is False:
                continue
            prime = True

        return number

    def get_e(phi_: int):
        e = 65537
        while phi_ % e == 0:
            e += 1
        return e

    def check_d(phi__: int, d: int, e: int):
        return e * d % phi__ == 1

    def get_d(phi___, e):
        top1, top2 = phi___, phi___
        c1, c2 = e, 1  # set collum 1 and 2
        while True:
            temp = top1 // c1
            lower_c1, lower_c2 = top1 - (c1 * temp), top2 - (c2 * temp)
            if lower_c1 < 0:
                lower_c1 = lower_c1 % phi___
            if lower_c2 < 0:
                lower_c2 = lower_c2 % phi___
            top1, top2 = c1, c2
            c1, c2 = lower_c1, lower_c2
            if c1 == 1:
                return c2

    p = get_single_key(key_length // 2)
    q = get_single_key(key_length // 2)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = get_e(phi)
    d = get_d(phi, e)

    if check_d(phi, d, e) is False:
        raise Exception("Calculating d resulted in an Error")

    return RSA_Private_Key(p, q, n, d, e)


def import_key(key: bytes):
    import base64
    dec_ = base64.b64decode(key)

    if b'-----BEGIN RSA PRIVATE KEY-----' in dec_:
        dec_ = dec_.strip(b'-----BEGIN RSA PRIVATE KEY-----')
        dec_ = dec_.strip(b'-----END RSA PRIVATE KEY-----')

        info = []

        for part in dec_.split(b'|'):
            info.append(part[2:])

        return RSA_Private_Key(info[0], info[1], info[2], info[3], info[4])

    elif b'-----BEGIN RSA PUBLIC KEY-----' in dec_:
        dec_ = dec_.strip(b'-----BEGIN RSA PUBLIC KEY-----')
        dec_ = dec_.strip(b'-----END RSA PUBLIC KEY-----')

        info = []

        for part in dec_.split(b'|'):
            info.append(part[2:])

        return RSA_Public_Key(info[0], info[1])
    else:
        raise Exception("Couldn't identify key")
