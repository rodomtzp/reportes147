#!/usr/bin/env bash
# Restaura un respaldo. ¡Reemplaza TODOS los datos actuales!
# Uso:  scripts/restaurar.sh respaldos/bd-AAAAMMDD-HHMMSS.dump [respaldos/uploads-AAAAMMDD-HHMMSS.tar.gz]
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "Uso: $0 <bd.dump> [uploads.tar.gz]" >&2; exit 1; }
[ -f .env ] && set -a && . ./.env && set +a
read -r -p "Esto BORRA los datos actuales y los reemplaza por el respaldo. Escribe RESTAURAR para continuar: " ok
[ "$ok" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }

echo "→ Base de datos…"
docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner < "$1"
if [ $# -ge 2 ]; then
  echo "→ Evidencias…"
  docker compose exec -T backend sh -c 'rm -rf /data/uploads/* /data/uploads/.[!.]* 2>/dev/null; tar -C /data/uploads -xzf -' < "$2"
fi
docker compose restart backend
echo "Restauración terminada."
