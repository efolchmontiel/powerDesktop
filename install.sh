#!/usr/bin/env bash
# Instala powerDesktop como comando global: Desktop shutdown alarm
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
VENV_DIR="${PROJECT_DIR}/.venv"
CMD_DISPATCHER="Desktop"
PYTHON="${PYTHON:-python3}"

# Comandos viejos a eliminar si existen.
LEGACY_COMMANDS=("powerDesktop" "offDesktooErickFm")

echo "⏰ Instalando powerDesktop..."
echo "   Proyecto: ${PROJECT_DIR}"

missing=()
command -v systemctl >/dev/null 2>&1 || missing+=("systemctl")
command -v "${PYTHON}" >/dev/null 2>&1 || missing+=("python3")

if ((${#missing[@]} > 0)); then
  echo "❌ Faltan dependencias del sistema:"
  printf '   • %s\n' "${missing[@]}"
  exit 1
fi

echo "📦 Creando entorno virtual..."
if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON}" -m venv "${VENV_DIR}"
fi

echo "📦 Instalando dependencias Python..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${PROJECT_DIR}/requirements.txt"

VENV_PYTHON="${VENV_DIR}/bin/python"
mkdir -p "${BIN_DIR}"

# Eliminar wrappers viejos.
for legacy in "${LEGACY_COMMANDS[@]}"; do
  if [[ -f "${BIN_DIR}/${legacy}" ]]; then
    rm -f "${BIN_DIR}/${legacy}"
    echo "🗑️  Eliminado comando viejo: ${legacy}"
  fi
done

# Dispatcher: se ejecuta como "Desktop shutdown alarm"
DISPATCHER="${BIN_DIR}/${CMD_DISPATCHER}"
cat > "${DISPATCHER}" <<EOF
#!/usr/bin/env bash
# powerDesktop — generado por install.sh
# Uso: Desktop shutdown alarm
if [[ "\${1:-}" == "shutdown" && "\${2:-}" == "alarm" ]]; then
  exec "${VENV_PYTHON}" "${PROJECT_DIR}/main.py"
fi

echo "Uso: Desktop shutdown alarm" >&2
exit 1
EOF
chmod +x "${DISPATCHER}"
echo "✅ Comando creado: ${DISPATCHER}"
echo "   Ejecutá: Desktop shutdown alarm"

if [[ -d "${HOME}/.config/fish" ]]; then
  FISH_CONF="${HOME}/.config/fish/config.fish"
  if ! grep -q '.local/bin' "${FISH_CONF}" 2>/dev/null; then
    echo "" >> "${FISH_CONF}"
    echo "# powerDesktop — PATH local" >> "${FISH_CONF}"
    echo 'fish_add_path ~/.local/bin' >> "${FISH_CONF}"
    echo "ℹ️  Agregado ~/.local/bin al PATH en config.fish"
  fi
fi

if command -v loginctl >/dev/null 2>&1; then
  linger_status="$(loginctl show-user "${USER}" -p Linger --value 2>/dev/null || true)"
  if [[ "${linger_status}" != "yes" ]]; then
    echo ""
    echo "ℹ️  Para que los timers funcionen sin sesión gráfica activa,"
    echo "   podés habilitar linger (requiere sudo):"
    echo "   sudo loginctl enable-linger ${USER}"
  fi
fi

echo ""
echo "🎉 Instalación completa."
echo "   Ejecutá: Desktop shutdown alarm"
