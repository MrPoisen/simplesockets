from .simple_sockets import TCPServer, TCPClient
from .securesockets.SelfmadeCipher_Socket import SecureClient as PySecureClient, SecureServer as PySecureServer
from .securesockets.PyCryptodome_Socket import SecureClient, SecureServer

try:
    from Crypto.PublicKey.RSA import RsaKey
    PYCRYPTODOME = TRUE
except ImportError:
    PYRCYPTODOME = FALSE
