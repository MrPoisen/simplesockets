class error(Exception):
    pass


class RSAError(error):
    pass


class RSAImportKeyError(RSAError): pass


class RSACalcKeyError(RSAError): pass


class VeginerError(error):
    pass


class VPadError(VeginerError): pass

