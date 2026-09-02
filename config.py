"""Constantes y rutas de powerDesktop."""

from __future__ import annotations

from pathlib import Path

# Nombre de las unidades systemd (solo las creadas por esta app).
UNIT_NAME = "power-scheduler-shutdown"
SERVICE_UNIT = f"{UNIT_NAME}.service"
TIMER_UNIT = f"{UNIT_NAME}.timer"

# Directorios del usuario.
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
STATE_DIR = Path.home() / ".local" / "share" / "powerDesktop"
STATE_FILE = STATE_DIR / "scheduled.json"

# Comando global: se invoca como "Desktop shutdown alarm"
COMMAND_DISPATCHER = "Desktop"
COMMAND_ARGS = ("shutdown", "alarm")
COMMAND_INVOCATION = "Desktop shutdown alarm"

# Opciones de apagado rápido (etiqueta visible, minutos).
QUICK_OPTIONS: list[tuple[str, int]] = [
    ("30 minutos", 30),
    ("1 hora", 60),
    ("2 horas", 120),
]

# Formato de entrada para fecha/hora personalizada.
DATETIME_INPUT_FORMAT = "%Y-%m-%d %H:%M"
DATETIME_DISPLAY_FORMAT = "%d/%m/%Y %H:%M"

# Nombre visible de la aplicación (TUI y notificaciones).
APP_NAME = "Alarma de Apagado"

# Notificaciones desktop.
NOTIFY_ICON = "system-shutdown"
NOTIFY_APP_NAME = APP_NAME
