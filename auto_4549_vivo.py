import re, requests, pandas as pd
from datetime import datetime

area_hoy = 650
try:
    txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=15).text
    for line in txt.splitlines():
        if line.strip().startswith("4549"):
            nums = re.findall(r"\d+", line)
            if nums:
                area_hoy = int(nums[-1])
except:
    pass

fecha_hoy = datetime.utcnow().strftime("%d-%m-%Y")
hora_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
A_acum = 410 + area_hoy
C_t = round(A_acum / 267.0, 3)

df = pd.DataFrame([{
    "identificacion": "AR4549",
    "Arkansas": area_hoy,
    "fecha": fecha_hoy,
    "area": A_acum,
    "Connecticut": C_t,
    "pred_Tau_UTC": hora_utc,
    "bengala_real": "",
    "Tau_real_UTC": "",
    "error_min": "",
    "acierto": "por_publicar"
}])
df.to_csv("tabla_30.csv", index=False)
print(f"OK Arkansas={area_hoy} Connecticut={C_t}")
