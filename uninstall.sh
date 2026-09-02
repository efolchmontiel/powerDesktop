#!/usr/bin/env bash
# Desinstala powerDesktop
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
STATE_DIR="${HOME}/.local/share/powerDesktop"
SYSTEMD_DIR="${HOME}/.config/systemd/user"

echo "🗑️  Desinstalando powerDesktop..."

if [[ -f "${SYSTEMD_DIR}/power-scheduler-shutdown.timer" ]]; then
  systemctl --user disable --now power-scheduler-shutdown.timer 2>/dev/null || true
  systemctl --user stop power-scheduler-shutdown.service 2>/dev/null || true
  rm -f "${SYSTEMD_DIR}/power-scheduler-shutdown.timer"
  rm -f "${SYSTEMD_DIR}/power-scheduler-shutdown.service"
  systemctl --user daemon-reload 2>/dev/null || true
  echo "✅ Timer systemd eliminado"
fi

for cmd in Desktop powerDesktop offDesktooErickFm; do
  if [[ -f "${BIN_DIR}/${cmd}" ]]; then
    rm -f "${BIN_DIR}/${cmd}"
    echo "✅ Eliminado: ${BIN_DIR}/${cmd}"
  fi
done

if [[ -d "${STATE_DIR}" ]]; then
  rm -rf "${STATE_DIR}"
  echo "✅ Estado eliminado: ${STATE_DIR}"
fi

echo ""
echo "🎉 Desinstalación completa."
echo "   El código fuente en $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) no fue borrado."
echo "   Borralo manualmente si ya no lo necesitás."
