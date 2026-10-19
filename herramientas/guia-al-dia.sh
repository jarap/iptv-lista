#!/bin/bash
# Mantiene al día la guía de la lista de prueba, sola, todos los días.
#
# La usan los revisores de las tiendas (Samsung, Amazon, Play, Roku) para probar
# la app: con la guía vencida ven «sin guía» en todos los canales. Ya pasó una vez
# (venció el 11/10/2026) porque se rearmaba a mano. Corre por cron:
#
#     17 5 * * * /home/piter/proyectos/cti/lista/herramientas/guia-al-dia.sh
#
# Si la fuente viene rota —un canal que se quedó sin programas, o una guía que no
# llega a cubrir el mes— se queda con la anterior y no publica nada: una guía de
# ayer que cubre 29 días es mejor que una de hoy con canales vacíos.
set -uo pipefail

LISTA=/home/piter/proyectos/cti/lista
REGISTRO="$LISTA/herramientas/guia-al-dia.log"
GUIA="$LISTA/prueba.xml"
ANTES=$(mktemp)
trap 'rm -f "$ANTES"' EXIT

anotar() { echo "$(date '+%F %T') $*" >> "$REGISTRO"; }

cd "$LISTA" || exit 1
cp "$GUIA" "$ANTES"

intentos=0
until /usr/bin/python3 -I herramientas/guia_prueba.py >> "$REGISTRO" 2>&1; do
    intentos=$((intentos + 1))
    if [ "$intentos" -ge 3 ]; then
        cp "$ANTES" "$GUIA"
        anotar "ERROR: la fuente no bajó en 3 intentos; queda la guía anterior"
        exit 1
    fi
    sleep 300
done

# Cada canal que tenía programas los sigue teniendo, y la guía llega a 25 días.
if ! /usr/bin/python3 -I - "$ANTES" "$GUIA" >> "$REGISTRO" 2>&1 <<'EOF'
import re, sys
from collections import Counter
from datetime import datetime, timedelta, timezone

def leer(ruta):
    texto = open(ruta, encoding="utf-8").read()
    canales = Counter(re.findall(r'<programme[^>]*channel="([^"]+)"', texto))
    fines = [datetime.strptime(s, "%Y%m%d%H%M%S %z")
             for s in re.findall(r'<programme[^>]*stop="([^"]+)"', texto)]
    return canales, max(fines) if fines else None

antes, _ = leer(sys.argv[1])
ahora, hasta = leer(sys.argv[2])
vacios = [c for c in antes if ahora.get(c, 0) == 0]
if vacios:
    sys.exit(f"ERROR: se quedaron sin programas: {', '.join(vacios)}")
if hasta is None or hasta < datetime.now(timezone.utc) + timedelta(days=25):
    sys.exit(f"ERROR: la guía nueva llega sólo hasta {hasta}")
print(f"guía nueva bien: {sum(ahora.values())} programas hasta {hasta:%d/%m}")
EOF
then
    cp "$ANTES" "$GUIA"
    anotar "ERROR: la guía nueva no pasó el control; queda la anterior"
    exit 1
fi

if git diff --quiet -- prueba.xml; then
    anotar "sin cambios"
    exit 0
fi

hasta=$(grep -o 'stop="[0-9]\{8\}' "$GUIA" | sort | tail -1 | sed -E 's/stop="([0-9]{4})([0-9]{2})([0-9]{2})/\3\/\2/')
git commit -q -m "Guía de la lista de prueba al día (hasta el $hasta)" -- prueba.xml || {
    anotar "ERROR: no se pudo commitear"; exit 1; }

for i in 1 2 3; do
    if git push -q origin main >> "$REGISTRO" 2>&1; then
        anotar "publicada, hasta el $hasta"
        exit 0
    fi
    sleep 120
done
anotar "ERROR: commiteada pero no se pudo publicar (git push falló 3 veces)"
exit 1
