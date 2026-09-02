"""Interfaz TUI con Textual para powerDesktop."""

from __future__ import annotations

from datetime import datetime

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static

from datetime_picker import DateTimePicker

from config import (
    APP_NAME,
    DATETIME_DISPLAY_FORMAT,
    NOTIFY_APP_NAME,
    NOTIFY_ICON,
    QUICK_OPTIONS,
)
from systemd import (
    ScheduledShutdown,
    cancel_shutdown,
    format_remaining,
    get_scheduled_shutdown,
    schedule_at,
    schedule_relative_minutes,
)

# Paleta inspirada en terminales oscuros tipo Omarchy.
THEME_CSS = """
Screen {
    background: #0f0f14;
}

#main-container {
    width: 44;
    height: auto;
    border: round #5b8def;
    background: #16161e;
    padding: 1 2;
}

.title {
    text-align: center;
    text-style: bold;
    color: #7aa2f7;
    width: 100%;
    padding-bottom: 1;
}

.subtitle {
    color: #a9b1d6;
    text-align: center;
    width: 100%;
    padding-bottom: 1;
}

#menu-list {
    height: auto;
    max-height: 14;
    background: #16161e;
    border: none;
    padding: 0;
}

#menu-list > ListItem {
    padding: 0 1;
    height: 1;
}

#menu-list > ListItem:hover,
#menu-list > ListItem.--highlight {
    background: #24283b;
    color: #c0caf5;
}

.info-box {
    border: round #414868;
    background: #1a1b26;
    padding: 1 2;
    margin: 1 0;
    width: 100%;
}

.warning {
    color: #e0af68;
    text-style: bold;
}

.success {
    color: #9ece6a;
}

.error {
    color: #f7768e;
}

.datetime-hint {
    color: #565f89;
    text-align: center;
    width: 100%;
    padding-bottom: 1;
}

#button-row Button {
    margin: 0 1 0 0;
    min-width: 14;
    background: #313244;
    color: #cdd6f4;
    border: round #45475a;
}

#button-row Button.-primary {
    background: #3d59a1;
    color: #ffffff;
    border: round #5b7fd1;
}

#button-row Button:focus {
    background: #1a1b26;
    color: #f9e2af;
    border: round #f9e2af;
    text-style: bold;
}

#button-row Button.-primary:focus {
    background: #1a1b26;
    color: #9ece6a;
    border: round #9ece6a;
    text-style: bold;
}

#modal-box Button {
    margin: 0 1 0 0;
    min-width: 14;
    background: #313244;
    color: #cdd6f4;
    border: round #45475a;
}

#modal-box Button.-primary {
    background: #3d59a1;
    color: #ffffff;
    border: round #5b7fd1;
}

#modal-box Button.-primary:focus {
    background: #1a1b26;
    color: #9ece6a;
    border: round #9ece6a;
    text-style: bold;
}

#modal-box Button.-warning {
    background: #8b6914;
    color: #ffffff;
    border: round #e0af68;
}

#modal-box Button.-warning:focus {
    background: #1a1b26;
    color: #e0af68;
    border: round #e0af68;
    text-style: bold;
}

#modal-box Button:focus {
    background: #1a1b26;
    color: #f9e2af;
    border: round #f9e2af;
    text-style: bold;
}

Button {
    margin: 0 1 0 0;
}

#button-row {
    height: auto;
    margin-top: 1;
    align: center middle;
}

ModalScreen {
    align: center middle;
}

#modal-box {
    width: 50;
    height: auto;
    border: round #5b8def;
    background: #16161e;
    padding: 1 2;
}
"""


def send_notification(title: str, body: str) -> None:
    """Envía notificación gráfica si notify-send está disponible."""
    import shutil
    import subprocess

    if not shutil.which("notify-send"):
        return

    subprocess.run(
        [
            "notify-send",
            "-a",
            NOTIFY_APP_NAME,
            "-i",
            NOTIFY_ICON,
            title,
            body,
        ],
        check=False,
    )


def format_shutdown_info(scheduled: ScheduledShutdown) -> str:
    """Texto informativo del apagado actual."""
    remaining = format_remaining(scheduled.remaining)
    status = "activo" if scheduled.timer_active else "inactivo"
    return (
        f"Apagado:\n"
        f"{scheduled.shutdown_at.strftime(DATETIME_DISPLAY_FORMAT)}\n\n"
        f"Tiempo restante:\n"
        f"{remaining}\n\n"
        f"Estado: {status}"
    )


class ConfirmReplaceScreen(ModalScreen[bool]):
    """Pide confirmación para reemplazar un apagado existente."""

    DEFAULT_CSS = THEME_CSS

    def __init__(self, existing: ScheduledShutdown, action_label: str) -> None:
        super().__init__()
        self.existing = existing
        self.action_label = action_label

    def compose(self) -> ComposeResult:
        with Container(id="modal-box"):
            yield Label("⚠️ Ya existe un apagado programado", classes="warning")
            yield Static(format_shutdown_info(self.existing), classes="info-box")
            yield Label(f"¿Reemplazar con: {self.action_label}?")
            with Horizontal(id="button-row"):
                yield Button("Reemplazar", variant="warning", id="replace")
                yield Button("Cancelar", id="cancel")

    @on(Button.Pressed, "#replace")
    def confirm_replace(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def cancel_replace(self) -> None:
        self.dismiss(False)


class DateTimeScreen(ModalScreen[datetime | None]):
    """Pantalla para ingresar fecha y hora personalizada."""

    DEFAULT_CSS = THEME_CSS

    BINDINGS = [
        Binding("tab", "focus_next", "Siguiente", show=False),
        Binding("shift+tab", "focus_previous", "Anterior", show=False),
    ]

    def compose(self) -> ComposeResult:
        now = datetime.now().replace(second=0, microsecond=0)
        with Container(id="modal-box"):
            yield Label("Elegir fecha y hora", classes="title")
            yield Label(
                "↑↓ cambiar valor   ←→ cambiar campo   Tab botones",
                classes="datetime-hint",
            )
            yield DateTimePicker(initial=now, id="datetime-picker")
            yield Label("", id="datetime-error", classes="error")
            with Horizontal(id="button-row"):
                yield Button("Programar", variant="primary", id="schedule")
                yield Button("Volver", id="back")

    def on_mount(self) -> None:
        self.query_one("#datetime-picker", DateTimePicker).focus()

    def _validate(self, parsed: datetime) -> datetime | str:
        if parsed <= datetime.now():
            return "La fecha y hora deben ser futuras."
        return parsed

    def _submit_schedule(self) -> None:
        picker = self.query_one("#datetime-picker", DateTimePicker)
        error_label = self.query_one("#datetime-error", Label)
        result = self._validate(picker.get_datetime())

        if isinstance(result, str):
            error_label.update(result)
            picker.focus()
            return

        self.dismiss(result)

    @on(Button.Pressed, "#schedule")
    def schedule_pressed(self) -> None:
        self._submit_schedule()

    @on(Button.Pressed, "#back")
    def back_pressed(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        """← → entre botones Programar y Volver cuando tienen el foco."""
        focused = self.focused
        schedule_btn = self.query_one("#schedule", Button)
        back_btn = self.query_one("#back", Button)

        if focused not in (schedule_btn, back_btn):
            return

        if event.key == "left" and focused is back_btn:
            schedule_btn.focus()
            event.prevent_default()
            event.stop()
        elif event.key == "right" and focused is schedule_btn:
            back_btn.focus()
            event.prevent_default()
            event.stop()
        elif event.key == "up":
            self.query_one("#datetime-picker", DateTimePicker).focus()
            event.prevent_default()
            event.stop()

    def action_focus_next(self) -> None:
        focused = self.focused
        picker = self.query_one("#datetime-picker", DateTimePicker)
        schedule_btn = self.query_one("#schedule", Button)
        back_btn = self.query_one("#back", Button)

        if focused is picker:
            schedule_btn.focus()
        elif focused is schedule_btn:
            back_btn.focus()
        else:
            picker.focus()

    def action_focus_previous(self) -> None:
        """Shift+Tab: foco inverso."""
        focused = self.focused
        picker = self.query_one("#datetime-picker", DateTimePicker)
        schedule_btn = self.query_one("#schedule", Button)
        back_btn = self.query_one("#back", Button)

        if focused is picker:
            back_btn.focus()
        elif focused is back_btn:
            schedule_btn.focus()
        else:
            picker.focus()


class InfoScreen(ModalScreen[None]):
    """Pantalla informativa genérica."""

    DEFAULT_CSS = THEME_CSS

    def __init__(self, title: str, body: str, *, is_error: bool = False) -> None:
        super().__init__()
        self.title = title
        self.body = body
        self.is_error = is_error

    def compose(self) -> ComposeResult:
        css_class = "error" if self.is_error else "success"
        with Container(id="modal-box"):
            yield Label(self.title, classes=css_class)
            yield Static(self.body, classes="info-box")
            with Horizontal(id="button-row"):
                yield Button("Cerrar", id="close")

    @on(Button.Pressed, "#close")
    def close_pressed(self) -> None:
        self.dismiss(None)


class PowerDesktopApp(App[None]):
    """TUI principal de powerDesktop."""

    TITLE = APP_NAME
    CSS = THEME_CSS

    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "back", "Volver", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield Label(f"⏰ {APP_NAME}", classes="title")
            yield ListView(id="menu-list")
        yield Footer()

    def on_mount(self) -> None:
        self._build_menu()

    def _build_menu(self) -> None:
        menu = self.query_one("#menu-list", ListView)
        menu.clear()

        items: list[tuple[str, tuple[str, int | None]]] = [
            *[(label, ("quick", minutes)) for label, minutes in QUICK_OPTIONS],
            ("Elegir fecha y hora", ("custom", None)),
            ("Ver apagado programado", ("view", None)),
            ("Cancelar apagado", ("cancel", None)),
            ("Salir", ("quit", None)),
        ]

        for text, _action in items:
            menu.append(ListItem(Label(text)))

        self._menu_actions = [action for _, action in items]

    @on(ListView.Selected)
    def menu_selected(self, event: ListView.Selected) -> None:
        index = event.list_view.index
        if index is None or index >= len(self._menu_actions):
            return

        action_type, value = self._menu_actions[index]

        if action_type == "quick":
            self._schedule_quick(value)  # type: ignore[arg-type]
        elif action_type == "custom":
            self._schedule_custom()
        elif action_type == "view":
            self._view_scheduled()
        elif action_type == "cancel":
            self._cancel_scheduled()
        elif action_type == "quit":
            self.exit()

    @work
    async def _schedule_quick(self, minutes: int) -> None:
        label = next(option_label for option_label, m in QUICK_OPTIONS if m == minutes)
        await self._schedule_with_replace_check(
            action_label=label,
            do_schedule=lambda: schedule_relative_minutes(minutes, label),
            notify_minutes=minutes,
        )

    @work
    async def _schedule_custom(self) -> None:
        chosen = await self.push_screen_wait(DateTimeScreen())
        if chosen is None:
            return

        label = chosen.strftime(DATETIME_DISPLAY_FORMAT)
        minutes_until = max(1, int((chosen - datetime.now()).total_seconds() // 60))

        await self._schedule_with_replace_check(
            action_label=label,
            do_schedule=lambda: schedule_at(chosen, label),
            notify_minutes=minutes_until,
        )

    async def _schedule_with_replace_check(
        self,
        action_label: str,
        do_schedule,
        notify_minutes: int,
    ) -> None:
        existing = get_scheduled_shutdown()
        if existing and not existing.is_past:
            replace = await self.push_screen_wait(
                ConfirmReplaceScreen(existing, action_label)
            )
            if not replace:
                return
            cancel_shutdown()

        try:
            scheduled = do_schedule()
        except Exception as exc:  # noqa: BLE001 — mostramos error al usuario
            await self.push_screen_wait(
                InfoScreen("Error", str(exc), is_error=True)
            )
            return

        send_notification(
            "Apagado programado",
            f"El equipo se apagará en {notify_minutes} minutos",
        )

        remaining = format_remaining(scheduled.remaining)
        await self.push_screen_wait(
            InfoScreen(
                "✅ Apagado programado",
                (
                    f"Fecha: {scheduled.shutdown_at.strftime(DATETIME_DISPLAY_FORMAT)}\n"
                    f"Restante: {remaining}"
                ),
            )
        )

    @work
    async def _view_scheduled(self) -> None:
        scheduled = get_scheduled_shutdown()
        if scheduled is None or scheduled.is_past:
            await self.push_screen_wait(
                InfoScreen("Sin apagado", "No hay ningún apagado programado.")
            )
            return

        body = (
            f"Fecha:\n{scheduled.shutdown_at.strftime(DATETIME_DISPLAY_FORMAT)}\n\n"
            f"Restante:\n{format_remaining(scheduled.remaining)}\n\n"
            f"Estado: {'activo' if scheduled.timer_active else 'inactivo'}"
        )
        await self.push_screen_wait(
            InfoScreen("⏰ Apagado programado", body)
        )

    @work
    async def _cancel_scheduled(self) -> None:
        scheduled = get_scheduled_shutdown()
        if scheduled is None:
            await self.push_screen_wait(
                InfoScreen("Sin apagado", "No hay ningún apagado programado para cancelar.")
            )
            return

        cancelled = cancel_shutdown()
        if cancelled:
            send_notification("Apagado cancelado", "Se eliminó el apagado programado.")
            await self.push_screen_wait(
                InfoScreen("Cancelado", "El apagado programado fue eliminado.")
            )
        else:
            await self.push_screen_wait(
                InfoScreen("Error", "No se pudo cancelar el apagado.", is_error=True)
            )
