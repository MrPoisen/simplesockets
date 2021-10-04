from dataclasses import dataclass, field
from datetime import datetime
from threading import Event as Event_
from typing import Union


def _time():
    return datetime.now()

@dataclass(frozen=True)
class Event:
    name: str = field(init=True, compare=True)
    time_: datetime = field(init=True, default_factory=_time, compare=False)

    def copy(self, new_time: bool = True):
        """
        makes a copy of the event

        Args:
            new_time: if not the time of the original event should be used

        Returns:
            Event: Event

        """
        return Event(self.name, _time() if new_time else self.time_ )


@dataclass(frozen=False)
class Event_System:
    events: list = field(init=False, default_factory=list)
    _lock: Event_ = field(init=False, default_factory=Event_, repr=False)

    def __bool__(self):
        return len(self.events) > 0

    def __len__(self):
        return len(self.events)

    def __contains__(self, item):
        return item in self.events

    def __iter__(self):
        for ev in self.events:
            yield ev

    def happened(self, event: Event):
        """
        adds an event to the event queue/list

        Args:
            event: the event

        Raises:
            TypeError: If event isn't a Event
        """
        if isinstance(event, Event):
            self.events.append(event)
            self._lock.set()
        else:
            raise TypeError(f"Type should be Event not {type(event)}")

    def clear(self):
        """
        clears the event_system

        Returns:

        """
        self.events.clear()
        self._lock.clear()

    def first_event(self, pop: bool = True) -> Union[Event, None]:
        """
        returns the first event

        Args:
            pop: if True will remove the first element

        Returns:
            Returns an event if one was collected else None

        """
        if self:
            if pop:
                pop_ = self.events.pop(0)
                if self is False:
                    self._lock.clear()
                return pop_
            else:
                return self.events[0]
        else:
            return

    def remove(self, event: Event):
        """
        will remove an event

        Args:
            event: event to be removed

        Returns:

        """
        self.events.remove(event)
        if self is False:
            self._lock.clear()

    def pop(self, index: int) -> Event:
        """
        pops an event at a specific index in the event queue/list

        Args:
            index: index

        Returns:
            returns the event at the given index

        """
        pop = self.events.pop(index)
        if self is False:
            self._lock.clear()
        return pop

    def await_event(self, timeout: Union[int, float] = None) -> bool:
        """
        waits till an event occurs

        Args:
            timeout: timeout in milliseconds

        Returns:
            Returns True if an event occurred

        """
        while True:
            if timeout is None:
                r = self._lock.wait()
            else:
                r = self._lock.wait(timeout / 1000)
            if self and r:
                break
            elif r is not True:
                break
            else:
                self._lock.clear()
        if r:
            return True
        else:
            return False

    def clear_name(self, name: str):
        """
        removes every event with the given name

        Args:
            name: name
        """
        events = self.events.copy()
        for ev in events:
            if ev.name == name:
                self.remove(ev)
        self.events = events
