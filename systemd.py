"""Gestión de timers systemd de usuario para apagado programado."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from config import (
    SERVICE_UNIT,
    STATE_DIR,
    STATE_FILE,
    SYSTEMD_USER_DIR,
    TIMER_UNIT,
)

ScheduleKind = Literal["quick", "custom"]


@dataclass(frozen=True)
class ScheduledShutdown:
    """Estado persistido de un apagado programado."""

    shutdown_at: datetime
    kind: ScheduleKind
    label: str
    timer_active: bool
    service_state: str

    @property
    def remaining(self) -> timedelta:
        return self.shutdown_at - datetime.now()

    @property
    def is_past(self) -> bool:
        return self.remaining.total_seconds() <= 0


class SystemdError(RuntimeError):
    """Error al interactuar con systemd."""


def _run_systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["systemctl", "--user", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise SystemdError(stderr or f"systemctl falló: {' '.join(cmd)}")
    return result


def ensure_directories() -> None:
    """Crea directorios necesarios para unidades y estado."""
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _service_content() -> str:
    """Unidad de servicio que ejecuta apagado limpio vía systemctl."""
    return """[Unit]
Description=Alarma de Apagado - Apagado programado
Documentation=man:systemd.special(7)

[Service]
Type=oneshot
ExecStart=/usr/bin/systemctl poweroff
"""


def _timer_content_absolute(shutdown_at: datetime) -> str:
    """Timer con fecha/hora absoluta (OnCalendar)."""
    calendar = shutdown_at.strftime("%Y-%m-%d %H:%M:%S")
    return f"""[Unit]
Description=Alarma de Apagado - Timer de apagado
Documentation=man:systemd.timer(7)

[Timer]
OnCalendar={calendar}
AccuracySec=1s
Persistent=true
Unit={SERVICE_UNIT}

[Install]
WantedBy=timers.target
"""


def _timer_content_relative(minutes: int) -> str:
    """Timer relativo desde la activación (OnActiveSec)."""
    seconds = minutes * 60
    return f"""[Unit]
Description=Alarma de Apagado - Timer de apagado
Documentation=man:systemd.timer(7)

[Timer]
OnActiveSec={seconds}
AccuracySec=1s
Unit={SERVICE_UNIT}

[Install]
WantedBy=timers.target
"""


def _write_unit_files(timer_body: str) -> None:
    """Escribe service + timer y recarga systemd --user."""
    ensure_directories()
    service_path = SYSTEMD_USER_DIR / SERVICE_UNIT
    timer_path = SYSTEMD_USER_DIR / TIMER_UNIT

    service_path.write_text(_service_content(), encoding="utf-8")
    timer_path.write_text(timer_body, encoding="utf-8")

    _run_systemctl("daemon-reload")
    _run_systemctl("enable", "--now", TIMER_UNIT)


def _save_state(
    shutdown_at: datetime,
    kind: ScheduleKind,
    label: str,
) -> None:
    ensure_directories()
    payload = {
        "shutdown_at": shutdown_at.isoformat(timespec="seconds"),
        "kind": kind,
        "label": label,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _clear_state() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def timer_exists() -> bool:
    """True si el timer de esta app está cargado en systemd --user."""
    result = _run_systemctl("list-unit-files", TIMER_UNIT, check=False)
    if result.returncode != 0:
        return False
    return "power-scheduler" in result.stdout


def timer_is_active() -> bool:
    """True si el timer está activo ahora mismo."""
    result = _run_systemctl("is-active", TIMER_UNIT, check=False)
    return result.stdout.strip() == "active"


def get_timer_status() -> tuple[bool, str]:
    """Devuelve (activo, estado legible del timer)."""
    active = timer_is_active()
    result = _run_systemctl("show", TIMER_UNIT, "-p", "ActiveState,SubState", check=False)
    state = result.stdout.strip().replace("\n", " | ") if result.returncode == 0 else "desconocido"
    return active, state


def get_scheduled_shutdown() -> ScheduledShutdown | None:
    """
    Lee el apagado programado desde el estado persistido y valida contra systemd.
    Si el timer ya no existe en systemd, limpia estado huérfano.
    """
    state = _load_state()
    if state is None:
        return None

    if not timer_exists():
        _clear_state()
        return None

    try:
        shutdown_at = datetime.fromisoformat(state["shutdown_at"])
    except (KeyError, ValueError):
        _clear_state()
        return None

    active, service_state = get_timer_status()
    return ScheduledShutdown(
        shutdown_at=shutdown_at,
        kind=state.get("kind", "custom"),
        label=state.get("label", "Apagado programado"),
        timer_active=active,
        service_state=service_state,
    )


def schedule_relative_minutes(minutes: int, label: str) -> ScheduledShutdown:
    """Programa apagado en N minutos desde ahora."""
    shutdown_at = datetime.now() + timedelta(minutes=minutes)
    _write_unit_files(_timer_content_relative(minutes))
    _save_state(shutdown_at, "quick", label)
    active, service_state = get_timer_status()
    return ScheduledShutdown(
        shutdown_at=shutdown_at,
        kind="quick",
        label=label,
        timer_active=active,
        service_state=service_state,
    )


def schedule_at(shutdown_at: datetime, label: str | None = None) -> ScheduledShutdown:
    """Programa apagado en fecha/hora absoluta futura."""
    if shutdown_at <= datetime.now():
        raise ValueError("La fecha y hora deben ser futuras.")

    display = label or shutdown_at.strftime("%d/%m/%Y %H:%M")
    _write_unit_files(_timer_content_absolute(shutdown_at))
    _save_state(shutdown_at, "custom", display)
    active, service_state = get_timer_status()
    return ScheduledShutdown(
        shutdown_at=shutdown_at,
        kind="custom",
        label=display,
        timer_active=active,
        service_state=service_state,
    )


def cancel_shutdown() -> bool:
    """
    Cancela solo el apagado creado por powerDesktop.
    No toca otros timers del sistema.
    """
    had_timer = timer_exists()

    if had_timer:
        _run_systemctl("disable", "--now", TIMER_UNIT, check=False)
        _run_systemctl("stop", SERVICE_UNIT, check=False)
        _run_systemctl("reset-failed", SERVICE_UNIT, check=False)

    for unit in (TIMER_UNIT, SERVICE_UNIT):
        path = SYSTEMD_USER_DIR / unit
        if path.exists():
            path.unlink()

    _clear_state()

    if had_timer:
        _run_systemctl("daemon-reload", check=False)

    return had_timer


def format_remaining(delta: timedelta) -> str:
    """Formatea tiempo restante como HH:MM:SS o 'X minutos'."""
    total = int(delta.total_seconds())
    if total <= 0:
        return "00:00:00"

    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours == 0 and minutes < 60:
        if minutes == 0:
            return f"{seconds} segundos"
        return f"{minutes} minutos"

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
