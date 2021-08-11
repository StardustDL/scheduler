from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Iterable, Iterator, List, Optional
from enum import Enum
from dataclasses import dataclass, field


class PromptResult(Enum):
    Empty = 0
    Unsupported = 1     # Unsupported, skip this and go next
    Resolved = 2        # Resolved, go next
    Finished = 3        # Resolved, stop going next
    Failed = 4          # Failed, stop going next


class PrompterPayload(ABC):
    pass


@dataclass
class CyclePayload(PrompterPayload):
    work: bool
    index: int


@dataclass
class UserPayload(PrompterPayload):
    payload: Any


@dataclass(frozen=True)
class SchedulePayload(PrompterPayload):
    index: int
    message: str
    startTime: datetime
    endTime: datetime
    duration: timedelta = field(init=False)

    def __post_init__(self) -> None:
        self.duration = self.endTime - self.endTime


class PrompterPayloadCollection(PrompterPayload):
    def __init__(self, payloads: Optional[List[PrompterPayload]]) -> None:
        super().__init__()
        self.payloads = payloads if payloads is not None else []

    def withPayload(self, payload: PrompterPayload) -> "PrompterPayloadCollection":
        self.payloads.append(payload)
        return self

    def withPayloads(self, payloads: "PrompterPayloadCollection") -> "PrompterPayloadCollection":
        self.payloads.extend(payloads)
        return self

    def tryGet(self, type: type) -> Iterable[PrompterPayload]:
        for item in self.payloads:
            if isinstance(item, type):
                yield item

    def getSchedule(self) -> Optional[SchedulePayload]:
        return next(self.tryGet(SchedulePayload), None)

    def getCycle(self) -> Optional[CyclePayload]:
        return next(self.tryGet(CyclePayload), None)

    def getUsers(self) -> Iterable[UserPayload]:
        return self.tryGet(UserPayload)

    def __iter__(self) -> Iterator[PrompterPayload]:
        return iter(self.payloads)


class Prompter(ABC):
    def __init__(self, final: bool = False) -> None:
        self.final = final

    def success(self) -> PromptResult:
        return PromptResult.Finished if self.final else PromptResult.Resolved

    @abstractmethod
    def prompt(self, payloads: PrompterPayloadCollection) -> PromptResult:
        pass

    def __repr__(self) -> str:
        return type(self).__name__


class PrompterHub(Prompter, ABC):
    @abstractmethod
    def register(self, prompter: Prompter) -> None:
        pass


def getMessage(payloads: PrompterPayloadCollection, cycle: bool = True) -> None:
    schedule = payloads.getSchedule()
    message = schedule.message

    if cycle:
        cycleP = payloads.getCycle()
        if cycleP:
            message += f" (cycle {cycleP.index} {'' if cycleP.work else 'resting '}starting)"

    return message
