"""Selector de fecha/hora navegable con flechas del teclado."""

from __future__ import annotations

import calendar
from datetime import datetime

from rich.text import Text
from textual import events
from textual.reactive import reactive
from textual.widget import Widget


class DateTimePicker(Widget):
    """
    Selector segmentado YYYY-MM-DD HH:MM.

    Controles:
    - ← / → : cambiar segmento activo (año, mes, día, hora, minuto)
    - ↑ / ↓ : incrementar / decrementar el segmento activo
    """

    can_focus = True

    DEFAULT_CSS = """
    DateTimePicker {
        width: 100%;
        height: 3;
        border: round #414868;
        background: #1a1b26;
        content-align: center middle;
        margin: 1 0;
    }

    DateTimePicker:focus {
        border: round #7aa2f7;
    }
    """

    value: reactive[datetime] = reactive(datetime.now)
    active_segment: reactive[int] = reactive(0)

    SEGMENT_NAMES = ("año", "mes", "día", "hora", "minuto")

    def __init__(
        self,
        initial: datetime | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        now = datetime.now().replace(second=0, microsecond=0)
        self._initial = initial or now

    def on_mount(self) -> None:
        self.value = self._initial
        self.active_segment = 0

    def get_datetime(self) -> datetime:
        """Devuelve la fecha/hora seleccionada."""
        return self.value

    def _adjust_segment(self, delta: int) -> None:
        year = self.value.year
        month = self.value.month
        day = self.value.day
        hour = self.value.hour
        minute = self.value.minute

        if self.active_segment == 0:
            year = max(1970, min(2100, year + delta))
        elif self.active_segment == 1:
            month = ((month - 1 + delta) % 12) + 1
        elif self.active_segment == 2:
            max_day = calendar.monthrange(year, month)[1]
            day = ((day - 1 + delta) % max_day) + 1
        elif self.active_segment == 3:
            hour = (hour + delta) % 24
        elif self.active_segment == 4:
            minute = (minute + delta) % 60

        max_day = calendar.monthrange(year, month)[1]
        day = min(day, max_day)
        self.value = datetime(year, month, day, hour, minute)

    def _move_segment(self, delta: int) -> None:
        self.active_segment = (self.active_segment + delta) % len(self.SEGMENT_NAMES)

    def render(self) -> Text:
        text = Text()
        active_style = "reverse bold #7aa2f7"
        value_style = "#c0caf5"
        sep_style = "#565f89"

        parts: list[tuple[str, int | None]] = [
            (f"{self.value.year:04d}", 0),
            ("-", None),
            (f"{self.value.month:02d}", 1),
            ("-", None),
            (f"{self.value.day:02d}", 2),
            (" ", None),
            (f"{self.value.hour:02d}", 3),
            (":", None),
            (f"{self.value.minute:02d}", 4),
        ]

        for content, segment in parts:
            if segment is not None and segment == self.active_segment:
                text.append(content, style=active_style)
            elif segment is not None:
                text.append(content, style=value_style)
            else:
                text.append(content, style=sep_style)

        return text

    def on_key(self, event: events.Key) -> None:
        if event.key == "left":
            self._move_segment(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "right":
            self._move_segment(1)
            event.prevent_default()
            event.stop()
        elif event.key == "up":
            self._adjust_segment(1)
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            self._adjust_segment(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "tab":
            event.prevent_default()
            event.stop()
            schedule_btn = self.screen.query_one("#schedule")
            schedule_btn.focus()
