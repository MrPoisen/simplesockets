from Crypto.Cipher import PKCS1_OAEP, Salsa20
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

from easy_cryptography.Exceptions import *


def gen_asym_keys(length=2048):
    ''' Generates RSA keys

    :param length: (optional) length of the keys
    :return: returns private key, public key
    '''
    prkey = RSA.generate(length)
    pubkey = prkey.publickey()
    return prkey, pubkey


def encrypt_asym(text, pubkey):
    ''' Asymmetrical encryption

    :param text: data that is supposed to be encrypted in bytes
    :param pubkey: public key
    :return: decrypted text
    '''
    if type(text) == hex:  # Checks type
        text = bytearray.fromhex(text)
    elif type(text) == str:
        text = text.encode('utf-8')
    elif type(text) == bytes or type(text) == bytearray:
        pass
    else:
        raise WrongTypeError(text, "It should be str, hex or bytes.")
    cypher = PKCS1_OAEP.new(pubkey)
    encrmsg = cypher.encrypt(text)
    return encrmsg


def decrypt_asym(text, prkey):
    ''' Asymmetrical decryption

    :param text: data that is supposed to be decrypted in bytes
    :param prkey: privat key
    :return: decrypted text
    '''
    if type(text) == hex or type(text) == str:  # Checks type
        text = bytearray.fromhex(text)
    elif type(text) == bytes:
        pass
    else:
        raise WrongTypeError(text, "Type is not suported for decryption. It should be str, hex or bytes.")
    cypher = PKCS1_OAEP.new(prkey)
    decrmsg = cypher.decrypt(text)
    return decrmsg


def get_sym_keys(bytes=32):
    ''' Generates random bytes used as key

    :param bytes: (optional) length of the key
    :return: key
    '''
    key = get_random_bytes(bytes)
    return key


def encrypt_sym(text, key):
    ''' Symmetrical encryption

    :param text: data that is supposed to be encrypted
    :param key: the key
    :return: returns decrypted data as bytes
    '''
    if type(text) == hex:
        text = bytearray.fromhex(text)
    elif type(text) == str:
        text = text.encode('utf-8')
    elif type(text) == bytes or type(text) == bytearray:
        pass
    else:
        raise WrongTypeError(text, "It should be str, hex or bytes.")
    cipher = Salsa20.new(key=key)
    ciphertext = cipher.encrypt(text)
    msg = cipher.nonce + ciphertext
    return msg


def decrypt_sym(text, key):
    ''' Symmetrical decryption

    :param text: data that is supposed to be decrypted
    :param key: the key (is the same one as the one used to encrypt)
    :return: returns decrypted data as bytes
    '''
    if type(text) == hex or type(text) == str:
        text = bytearray.fromhex(text)
    elif type(text) == bytes:
        pass
    else:
        raise WrongTypeError(text, "It should be str, hex or bytes.")
    cipher = Salsa20.new(key=key, nonce=text[:8])
    pl = cipher.decrypt(text[8:])
    return pl


def encr_data(data, pubkey, bytes=32, output="bytes"):
    ''' Encrypts data symmetrical and the key for the data assymetrical
    :param data: the data that is supposed to be decrypted
    :param pubkey: public_key
    :param bytes: (optional) number of bytes of the symmetric key
    :param output: (optional) type of the output
    >>> encr_data(data,pubkey,output="hex")
    :return: returns enrcypted data normally in bytes
    '''
    key = get_sym_keys(bytes)
    d = encrypt_sym(data, key)
    k = encrypt_asym(key, pubkey)
    space = b'$$$$'
    all = k + space + d
    if output == "hex":
        all = all.hex()
    elif output == "bytes":
        pass
    else:
        raise WrongTypeError(output, "The requested outputtype was invalid", "s")
    return all


def decr_data(data, prkey, output="str"):
    ''' Decrypts data with a private key

    :param data: the data that is supposed to be decrypted
    :param prkey: private_key
    :param output: (optional) type of the output
    >>> decr_data(data,prkey,output="bytes")
    :return: encrypted msg
    '''
    if type(data) == hex or type(data) == str:
        data = bytearray.fromhex(data)
    elif type(data) == bytes:
        pass
    else:
        raise WrongTypeError(data, "It should be str, hex or bytes.")
    key, da = data.split(b'$$$$')
    key = decrypt_asym(key, prkey)
    msg = decrypt_sym(da, key)
    if output == "bytes":
        pass
    elif output == "str":
        msg = msg.decode('utf-8')
    else:
        raise WrongTypeError(output, "The requested outputtype was invalid", "s")
    return msg

def import_asym_key(key):
    return RSA.import_key(key)

def export_asym_key(key):
    return key.export_key()
