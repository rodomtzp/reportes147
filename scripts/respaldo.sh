#!/usr/bin/env bash
# Respaldo de la base de datos (pg_dump) y de las evidencias (volumen uploads).
# Uso:  scripts/respaldo.sh                       (desarrollo)
#       COMPOSE_FILE=docker-compose.yml scripts/respaldo.sh
# Variables: BACKUP_DIR (por defecto ./respaldos) y CONSERVAR (cuántos respaldos guardar, 14).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
DESTINO="${BACKUP_DIR:-./respaldos}"
CONSERVAR="${CONSERVAR:-14}"
SELLO="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DESTINO"
chmod 700 "$DESTINO"          # contiene datos personales de menores
umask 077

echo "→ Base de datos…"
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$DESTINO/bd-$SELLO.dump"

echo "→ Evidencias…"
docker compose exec -T backend tar -C /data/uploads -czf - . > "$DESTINO/uploads-$SELLO.tar.gz"

# Verifica que los archivos no estén vacíos ni dañados.
[ -s "$DESTINO/bd-$SELLO.dump" ] || { echo "El respaldo de la BD quedó vacío" >&2; exit 1; }
gzip -t "$DESTINO/uploads-$SELLO.tar.gz"

# Rotación: conserva solo los últimos N de cada tipo.
for tipo in bd uploads; do
  ls -1t "$DESTINO"/"$tipo"-* 2>/dev/null | tail -n +"$((CONSERVAR + 1))" | xargs -r rm --
done
echo "Listo: $DESTINO/bd-$SELLO.dump y $DESTINO/uploads-$SELLO.tar.gz"
echo "Recuerda copiar los respaldos fuera del servidor."
