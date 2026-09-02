#!/usr/bin/env python3
"""
powerDesktop — Programador de apagado con systemd y TUI.

Ejecutá: Desktop shutdown alarm
"""

from __future__ import annotations

import shutil
import sys


def check_dependencies() -> list[str]:
    """Verifica dependencias del sistema y de Python."""
    missing: list[str] = []

    if not shutil.which("systemctl"):
        missing.append("systemctl (systemd)")

    try:
        import textual  # noqa: F401
    except ImportError:
        missing.append("textual (pip install textual)")

    return missing


def main() -> int:
    """Punto de entrada principal."""
    missing = check_dependencies()
    if missing:
        print("❌ Faltan dependencias para powerDesktop:\n", file=sys.stderr)
        for item in missing:
            print(f"  • {item}", file=sys.stderr)
        print(
            "\nInstalá con: pip install --user -r requirements.txt",
            file=sys.stderr,
        )
        print("O ejecutá: ./install.sh", file=sys.stderr)
        return 1

    if not shutil.which("notify-send"):
        print(
            "ℹ️  notify-send no encontrado; las notificaciones gráficas estarán deshabilitadas.",
            file=sys.stderr,
        )

    from tui import PowerDesktopApp

    app = PowerDesktopApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
