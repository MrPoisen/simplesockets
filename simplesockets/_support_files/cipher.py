try:
    from Crypto.Cipher import PKCS1_OAEP, Salsa20
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    pass

import hmac

def gen_asym_keys(length: int = 2048):
    ''' Generates RSA keys

    Args:
        length: length of the keys

    Returns:
        RsaKey, RsaKey: returns private key, public key
    '''
    prkey = RSA.generate(length)
    pubkey = prkey.publickey()
    return prkey, pubkey


def encrypt_asym(text: bytes, pubkey: RSA.RsaKey) -> bytes:
    ''' Asymmetrical encryption

    Args:
        text: data that is supposed to be encrypted in bytes
        pubkey: public key

    Returns:
        bytes: decrypted text
    '''
    if type(text) == hex:  # Checks type
        text = bytearray.fromhex(text)
    elif type(text) == str:
        text = text.encode('utf-8')
    elif type(text) == bytes or type(text) == bytearray:
        pass
    else:
        raise TypeError("text should be str, hex or bytes.")
    cypher = PKCS1_OAEP.new(pubkey)
    encrmsg = cypher.encrypt(text)
    return encrmsg


def decrypt_asym(text: bytes, prkey: RSA.RsaKey) -> bytes:
    ''' Asymmetrical decryption

    Args:
        text: data that is supposed to be decrypted in bytes
        prkey: privat key

    Returns:
        bytes: decrypted text
    '''
    if type(text) == hex or type(text) == str:  # Checks type
        text = bytearray.fromhex(text)
    elif type(text) == bytes:
        pass
    else:
        raise TypeError("Text type is not supported for decryption. It should be str, hex or bytes.")
    cypher = PKCS1_OAEP.new(prkey)
    decrmsg = cypher.decrypt(text)
    return decrmsg


def get_sym_keys(bytes_: int = 32) -> bytes:
    ''' Generates random bytes used as key

    Args:
        bytes_ (:obj:`int`, optional): length of the key

    Returns:
        bytes: key
    '''
    key = get_random_bytes(bytes_)
    return key


def encrypt_sym(text: bytes, key: bytes) -> bytes:
    ''' Symmetrical encryption

    Args:
        text: data that is supposed to be encrypted
        key: the key

    Returns:
        returns decrypted data as bytes

    '''
    if type(text) == hex:
        text = bytearray.fromhex(text)
    elif type(text) == str:
        text = text.encode('utf-8')
    elif type(text) == bytes or type(text) == bytearray:
        pass
    else:
        raise TypeError("Text should be str, hex or bytes.")
    cipher = Salsa20.new(key=key)
    ciphertext = cipher.encrypt(text)
    msg = cipher.nonce + ciphertext
    return msg


def decrypt_sym(text: bytes, key: bytes) -> bytes:
    ''' Symmetrical decryption

    Args:
        text: data that is supposed to be decrypted
        key: the key (is the same one as the one used to encrypt)

    Returns:
        returns decrypted data as bytes
    '''
    if type(text) == hex or type(text) == str:
        text = bytearray.fromhex(text)
    elif type(text) == bytes:
        pass
    else:
        raise TypeError("Text should be str, hex or bytes.")
    cipher = Salsa20.new(key=key, nonce=text[:8])
    pl = cipher.decrypt(text[8:])
    return pl


def encr_data(data: bytes, pubkey: RSA.RsaKey, bytes_: bytes = 32, output: str = "bytes"):
    ''' Encrypts data symmetrical and the key for the data assymetrical

    Args:
        data: the data that is supposed to be encrypted
        pubkey: public_key
        bytes_: number of bytes of the symmetric key
        output: type of the output

    Returns:
        returns enrcypted data normally in bytes

    Raises:
        TypeError: If the value of output is invalid
    '''
    key = get_sym_keys(bytes_)
    d = encrypt_sym(data, key)
    k = encrypt_asym(key, pubkey)
    space = b'$$%%$$'
    all = k + space + d
    if output == "hex":
        all = all.hex()
    elif output == "bytes":
        pass
    else:
        raise TypeError("The requested output type was invalid")
    return all


def decr_data(data: bytes, prkey: RSA.RsaKey, output: str = "bytes"):
    ''' Decrypts data with a private key

    Args:
        data: the data that is supposed to be decrypted
        prkey: private key
        output: type of the output

    Returns:
        decrypted msg

    Raises:
        TypeError: if the type of data or the value of output is invalid
    '''
    if type(data) == hex or type(data) == str:
        data = bytearray.fromhex(data)
    elif type(data) == bytes:
        pass
    else:
        raise TypeError("data should be str, hex or bytes.")
    key, da = data.split(b'$$%%$$')
    key = decrypt_asym(key, prkey)
    msg = decrypt_sym(da, key)
    if output == "bytes":
        pass
    elif output == "str":
        msg = msg.decode('utf-8')
    else:
        raise TypeError("The requested output type was invalid")
    return msg

def import_asym_key(key: bytes):
    return RSA.import_key(key)

def export_asym_key(key: RSA.RsaKey):
    return key.export_key()

import hashlib
import os


def gen_hash(text: bytes, predefined_salt: bytes = None, hash_type: str = 'sha512', iterations: int = 100_000,
             data_type: int = 'hex'):
    ''' Generates a hash from a text, standard in type sh512 and returns it with the salt as a prefix in bytes (or in hex)

    Args:
        text: the text that is supposed to be hashed
        predefined_salt: If given, specific salt that should be used, normally None
        hash_type: defines what hash algorithm should be used, normally sha512
        iterations: defines the amount of iterations, normally 100000
        data_type: defines the output type, normally hex

    Returns:
        hex: returns hash

    Raises:
        TypeError: If the predefined salt has the wrong type
    '''
    if predefined_salt == None:
        salt = os.urandom(32)  # Generates random bytes
    else:
        if type(predefined_salt) == bytes or type(predefined_salt) == bytearray or type(predefined_salt) == str or type(
                predefined_salt) == hex:  # Checks if it is a valid data typ
            if type(predefined_salt) == str or type(predefined_salt) == hex:
                predefined_salt = bytearray.fromhex(predefined_salt)  # Trys to convert  to binary
            salt = predefined_salt
        else:
            raise TypeError("predefined_salt should be bytes, bytearray, str or hex.")  # Raises Error
    if type(text) != bytes:
        text = text.encode('utf-8')  # Trys to convert text
    h = hashlib.pbkdf2_hmac(hash_type, text, salt, iterations)  # Generates hash
    if data_type == 'hex':  # Converts to hex
        salt = salt.hex()
        h = h.hex()
    if data_type == 'bytes':
        # Standard output type is bytes
        pass
    allbytes = salt + h  # Adds it up
    return allbytes


def compare_hash(to_compare: bytes, hash: bytes, hash_type: str = 'sha512', iterations: int = 100_000) -> bool:
    ''' Compares a text with a hash

    Args:
        to_compare: the text that should be compared with the hash
        hash: the hash that should be compared with the text
        hash_type: defines what hash algorithm should be used
        iterations: defines the amount of iterations

    Returns:
        returns True or False
    '''
    if type(hash) == bytes or type(hash) == bytearray:  # Checks type of hash
        hash = hash.hex()
    elif type(hash) == hex or type(hash) == str:
        pass
    else:
        raise TypeError("The hash should be bytes, bytearray, str or hex.")
    salt = hash[:64]  # 64 is the length of the salt in hex
    hash_text = hash[64:]
    testhash = gen_hash(to_compare, salt, hash_type=hash_type, iterations=iterations)
    test = testhash[64:]
    return hmac.compare_digest(bytearray.fromhex(hash_text), bytearray.fromhex(test))
