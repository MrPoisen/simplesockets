import datetime


class error(Exception):
    pass


class SocketError(error):
    pass

class SetupError(SocketError): pass


class Better_Exception:
    def __init__(self, exception, traceback=None):
        self._exception = exception
        self._traceback = traceback

    def __eq__(self, other):
        if isinstance(other, self.__class__) is False:
            raise TypeError()

        return (self._exception, self._traceback) == (other.exception, other.traceback)

    def __str__(self):
        return f'{self._exception.__class__.__name__}: {self._exception.__str__()}\nTraceback:\n{self._traceback}'

    def __repr__(self):
        return self.__str__()

    @property
    def exception(self):
        return self._exception

    @property
    def traceback(self):
        return self._traceback

class Exception_Collection:
    def __init__(self):
        self._exceptions = {}

    @property
    def exceptions(self):
        return self._exceptions.copy()

    def _get_time(self):
        return datetime.datetime.now().strftime("%H:%M:%S|%d.%m.%Y")

    def add(self, *args):
        if len(args) not in (1, 2):
            return
            # raise ValueError("You have to give an Better_Exception or exception (and traceback")

        if isinstance(args[0], Better_Exception):
            self._exceptions[self._get_time()] = args[0]
        elif issubclass(args[0].__class__, Exception) or isinstance(args[0], Exception):
            if len(args) == 2:
                self._exceptions[self._get_time()] = Better_Exception(args[0], args[1])
            else:
                self._exceptions[self._get_time()] = Better_Exception(args[0])
        else:
            return
            # raise TypeError("Given Exception is not valid")

    def clear(self):
        self._exceptions.clear()

    def get(self, time: str):
        return self._exceptions.get(time)

    def __bool__(self):
        return len(self._exceptions) == 0

    def __len__(self):
        return len(self._exceptions)

    def __str__(self):
        return str(self._exceptions)

    def __repr__(self):
        return self.__str__()
