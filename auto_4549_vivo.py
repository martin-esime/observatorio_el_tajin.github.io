import os, glob, requests, re
import pandas as pd

# AREA REAL DE HOY - SRS NOAA
area_hoy = 720
try:
    txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=15).text
    m = re.search(r"4549.*?(\d+)\s*$", txt, re.MULTILINE)
    if m:
        area_hoy = int(m.group(1))
        print(f"SRS NOAA area 4549: {area_hoy}")
except Exception as e:
    print(f"SRS fail {e}, usando {area_hoy}")

# ACUMULADA
# Hasta ayer traias 410, hoy + area_hoy
A_acum = 410 + area_hoy
C_t = A_acum / 267.0

print(f"Area hoy: {area_hoy} MSH")
print(f"A_acum: {A_acum} C(t): {C_t:.2f}")

# Actualiza tabla_30.csv si existe
if os.path.exists("tabla_30.csv"):
    df = pd.read_csv("tabla_30.csv")
    # busca fila 4549, si no existe la crea
    if 'id' in df.columns:
        mask = df['id'].astype(str) == '4549'
        if mask.any():
            df.loc[mask, 'area_hoy'] = area_hoy
            if 'A_acum' in df.columns:
                df.loc[mask, 'A_acum'] = A_acum
            if 'C_t' in df.columns:
                df.loc[mask, 'C_t'] = C_t
    df.to_csv("tabla_30.csv", index=False)
    print("tabla_30.csv actualizada")
else:
    print("No hay tabla_30.csv, solo print")
