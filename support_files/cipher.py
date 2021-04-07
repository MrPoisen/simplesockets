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

import hashlib
import os

from easy_cryptography.Exceptions import *


def gen_hash(text, predefined_salt=None, hash_type='sha512', iterations=100000, data_type='hex'):
    ''' Generates a hash from a text, standard in type sh512 and returns it with the salt as a prefix in bytes (or in hex)
    :param text: the text that is supposed to be hashed
    :param predefined_salt: (optional) specific salt that should be used
    :param hash_type: (optional) defines what hash algorithm should be used
    :param iterations: (optional) defines the amount of iterations
    :param data_type: (optional) defines the output type
    :return: returns hash
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


def compare_hash(to_compare, hash, hash_type='sha512', iterations=100000):
    ''' Compares a text with a hash
    :param to_compare: the text that should be compared with the hash
    :param hash: the hash that should be compared with the text
    :param hash_type: (optional) defines what hash algorithm should be used
    :param iterations: (optional) defines the amount of iterations
    :return: returns True or False
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
    return hash_text == test
