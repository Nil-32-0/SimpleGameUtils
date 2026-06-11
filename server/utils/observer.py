from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from events import Event
    
    from typing import Union


class Observer():
    def __init__(self):
        pass


    def update(self, event: Event) -> Union[Event, int]:
        pass
 

class Observable():
    def __init__(self):
        self._observers: list[tuple[Observer, int]] = []
        

    def attach(self, observer: Observer, priority: int):
        for i in range(len(self._observers)):
            if priority > self._observers[i][1]:
                self._observers.insert(i, (observer, priority))
                return
        self._observers.append((observer, priority))

    def resolve(self, event: Event) -> Union[Event, int]:
        for observer in [x[0] for x in self._observers]:
            event = observer.update(event)
            if event is int:
                return event
        return event