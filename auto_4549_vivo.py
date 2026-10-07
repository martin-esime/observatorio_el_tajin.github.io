import re, requests, pandas as pd
from datetime import datetime

# 1. Lee area real de NOAA SRS
area_hoy = 650
try:
    txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=15).text
    for line in txt.splitlines():
        if "4549" in line:
            if "Region 4549" in line or line.strip().startswith("4549"):
                print(f"LINEA: {line}")
                nums = re.findall(r"\d+", line)
                if nums:
                    area_hoy = int(nums[-1])
except Exception as e:
    print(f"Error SRS {e}, uso {area_hoy}")

# 2. Tu formula
fecha_hoy = datetime.utcnow().strftime("%d-%m-%Y")
hora_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
A_acum = 410 + area_hoy
C_t = round(A_acum / 267.0, 3)

print(f"Area hoy {area_hoy} - A_acum {A_acum} - C_t {C_t}")

# 3. Tabla limpia sin Arkansas
df = pd.DataFrame([{
    "fecha": fecha_hoy,
    "region": 4549,
    "area_hoy_MSH": area_hoy,
    "A_acum": A_acum,
    "C_t": C_t,
    "actualizado_UTC": hora_utc,
    "fuente": "NOAA SRS"
}])
df.to_csv("tabla_30.csv", index=False)
