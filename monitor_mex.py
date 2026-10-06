# monitor_mex.py - Observatorio El Tajin Tihuatlan
# Bitacora automatica de 30 eventos - filtro Mexico
import csv, os, json, requests
from datetime import datetime, timezone

CSV_FILE = "tabla_30.csv"
AR_ACTUAL = "4549" # cambia esto cuando salga nueva region
AREA = 650
CT = 2.535 # este lo va a calcular tu model.py despues, ahorita manual
TAU_PRED = "2026-10-07T04:00:00Z" # tu ventana
DOI = os.getenv("DOI_URL", "por_publicar")

# 1. Asegura que existe tabla_30.csv
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","AR","fecha","area","C_t","pred_Tau_UTC","flare_real","Tau_real_UTC","error_min","acierto","DOI"])

# 2. Lee cuantos van
with open(CSV_FILE, "r", encoding="utf-8") as f:
    rows = list(csv.reader(f))
    next_id = len(rows) # porque fila 1 es header

# 3. Checa si ya existe AR4549 hoy para no duplicar
fecha_hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
ya_existe = any(AR_ACTUAL in r[1] and fecha_hoy in r[2] for r in rows[1:])

if not ya_existe and next_id <= 30:
    print(f"Agregando evento {next_id} AR{AR_ACTUAL}")
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            next_id, # id
            AR_ACTUAL, # AR
            fecha_hoy, # fecha
            AREA, # area
            CT, # C(t)
            TAU_PRED, # pred_Tau_UTC
            "", # flare_real (se llena despues)
            "", # Tau_real_UTC
            "", # error_min
            "", # acierto
            DOI
        ])
else:
    print("Ya existe hoy o ya llegamos a 30")

# 4. Opcional: consulta ultimo flare de NOAA para auto-llenar error
try:
    # API simple de GOES
    r = requests.get("https://api.nasa.gov/DONKI/FLR?startDate=2026-10-05&endDate=2026-10-07&api_key=DEMO_KEY", timeout=10)
    if r.status_code == 200:
        print("DONKI consultado, listo para calcular error en fase 2")
except:
    print("Sin internet, solo se agrego prediccion")