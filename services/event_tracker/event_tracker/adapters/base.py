"""Контракт источника данных о боях.

Любой источник (симулятор, ESPN, новостные каналы) — это async-итератор
нормализованных FightEvent. event_tracker ничего не знает о деталях источника.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from ufc_common.events import FightEvent


class SourceAdapter(ABC):
    @abstractmethod
    def stream(self) -> AsyncIterator[FightEvent]:
        """Поток событий жизненного цикла ивента, в хронологическом порядке."""
        ...
