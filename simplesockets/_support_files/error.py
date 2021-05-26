class error(Exception):
    pass


class RSAError(error):
    pass


class RSAImportKeyError(RSAError): pass


class RSACalcKeyError(RSAError): pass


class VeginerError(error):
    pass


class VPadError(VeginerError): pass

class GenerationTypeError(VeginerError): pass


class TranspositionError(error):
    pass

class NotEncryptedError(TranspositionError): pass

class InvalidKeyError(TranspositionError): pass

class RepeatingValueError(InvalidKeyError): pass

class NoEffectError(InvalidKeyError): pass


class SocketError(error):
    pass

class SetupError(SocketError): pass