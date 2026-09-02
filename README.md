# powerDesktop

Programador de apagado automático para CachyOS / Omarchy usando **systemd user timers** y una TUI con **Python + Textual**.

Ejecuta `systemctl poweroff` de forma limpia en el momento programado.

## Requisitos

- CachyOS / Linux con systemd
- Python 3.10+
- `systemctl --user` habilitado
- `notify-send` (opcional, para notificaciones gráficas)

## Instalación

```bash
cd ~/Projects/powerDesktop
chmod +x install.sh uninstall.sh
./install.sh
```

Esto:

1. Crea un venv en `.venv/` e instala `textual`
2. Crea el comando global `Desktop` (dispatcher para `Desktop shutdown alarm`)
3. Agrega `~/.local/bin` al PATH en fish si hace falta

Reabrí la terminal o ejecutá:

```fish
fish_add_path ~/.local/bin
```

## Uso

```bash
Desktop shutdown alarm
```

### Menú principal

| Opción | Acción |
|--------|--------|
| 30 minutos / 1 hora / 2 horas | Apagado rápido con timer relativo |
| Elegir fecha y hora | Formato `YYYY-MM-DD HH:MM` |
| Ver apagado programado | Muestra fecha, restante y estado |
| Cancelar apagado | Elimina solo los timers de esta app |
| Salir | Cierra la TUI |

### Navegación

- **↑ / ↓** — moverse en el menú
- **Enter** — seleccionar
- **q** — salir

## Cómo funciona (systemd)

Crea unidades de usuario en `~/.config/systemd/user/`:

- `power-scheduler-shutdown.service` → ejecuta `/usr/bin/systemctl poweroff`
- `power-scheduler-shutdown.timer` → dispara el servicio

El estado (fecha programada, tiempo restante) se guarda en:

`~/.local/share/powerDesktop/scheduled.json`

Solo puede existir **un** apagado programado a la vez. Si intentás crear otro, la app te avisa y permite reemplazar.

## Probar

```bash
# 1. Abrir la TUI
Desktop shutdown alarm

# 2. Programar apagado de prueba (ej. 30 min) y verificar timer
systemctl --user list-timers | grep power-scheduler

# 3. Ver estado persistido
cat ~/.local/share/powerDesktop/scheduled.json

# 4. Cancelar desde la TUI o manualmente
systemctl --user disable --now power-scheduler-shutdown.timer
```

### Prueba rápida sin apagar (2 minutos)

1. Abrí con `Desktop shutdown alarm`
2. Elegí una hora 2 minutos en el futuro con "Elegir fecha y hora"
3. Verificá con "Ver apagado programado"
4. Cancelá antes de que expire

## Desinstalar

```bash
cd ~/Projects/powerDesktop
./uninstall.sh
rm -rf .venv   # opcional: eliminar entorno virtual
```

Opcional: borrar el directorio del proyecto.

```bash
rm -rf ~/Projects/powerDesktop
```

## Estructura

```
powerDesktop/
├── main.py           # Entry point y chequeo de dependencias
├── systemd.py        # Creación/gestión de timers systemd
├── tui.py            # Interfaz Textual
├── config.py         # Constantes y rutas
├── requirements.txt
├── install.sh
├── uninstall.sh
└── README.md
```

## Notas

- `systemctl poweroff` requiere permisos de apagado (polkit). En sesión gráfica local de Omarchy suele funcionar sin sudo.
- Para timers sin sesión activa: `sudo loginctl enable-linger $USER`
- Las notificaciones usan `notify-send` al programar o cancelar.
- El instalador usa un venv local (`.venv/`) para evitar conflictos con PEP 668 / Homebrew Python.
