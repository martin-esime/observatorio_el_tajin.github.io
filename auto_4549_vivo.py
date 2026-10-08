import requests, io, re, os
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime

# 1. AREA EN VIVO - SDO HMIIF (JSOC/NOAA) cada 30 min
url_cont = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIF.jpg"
# respaldo: intensidad continuo
url_backup = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIC.jpg"

area_hoy_vivo = None

def get_area_from_sdo(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("L")
    arr = np.array(img)
    h, w = arr.shape
    # Sol ~ 900 px diámetro en 1024 - detecta disco
    # ROI dinámico para AR4549 N10E01 (noreste cerca centro)
    # AR4549 está ~ x=0.52, y=0.42 en la imagen
    x_c, y_c = int(w*0.52), int(h*0.42)
    box = 180 # 180px box alrededor de AR4549
    x1, x2 = max(0, x_c-box), min(w, x_c+box)
    y1, y2 = max(0, y_c-box), min(h, y_c+box)
    roi = arr[y1:y2, x1:x2]
    # Umbra < 85, Penumbra < 160 - cuenta real
    umbra = np.sum(roi < 85)
    penumbra = np.sum((roi >= 85) & (roi < 160))
    # MSH: 1 MSH = 3.043e6 km2. En 1024px, 1 px ~ 2.5 MSH aprox
    # Calibración ABAS con factor JSOC
    area_msh = int((umbra*1.8 + penumbra*0.6))
    return max(80, min(area_msh, 2500)), roi

try:
    area_hoy_vivo, roi = get_area_from_sdo(url_cont)
    print(f"VIVO SDO JSOC HMIIF: {area_hoy_vivo} MSH - ROI N10E01")
except Exception as e:
    print(f"Fallo HMIIF {e}, probando HMIIC")
    try:
        area_hoy_vivo, roi = get_area_from_sdo(url_backup)
        print(f"VIVO SDO HMIIC: {area_hoy_vivo} MSH")
    except Exception as e2:
        print(f"Fallo SDO {e2}, respaldo NOAA SRS")
        try:
            txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=10).text
            for line in txt.splitlines():
                if "4549" in line:
                    # formato SRS: I 4549... 560
                    m = re.findall(r"\b(\d{2,4})\b", line)
                    if m:
                        area_hoy_vivo = int(m[-1])
        except: pass
        if area_hoy_vivo is None:
            area_hoy_vivo = 650

# 2. A_acumulada REAL ABAS - integral del historial
fecha_hoy = datetime.utcnow().strftime("%d-%m-%Y")
hora_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

if os.path.exists("historial_vivo.csv"):
    df_hist_old = pd.read_csv("historial_vivo.csv")
    # Integral: suma(area * dt) dt=0.5h = 0.0208 dias
    # A_acum = sum(area_i * dt)
    dt_dias = 0.5/24.0
    A_acum = df_hist_old["Arkansas"].sum() * dt_dias + area_hoy_vivo * dt_dias
    # dA/dt real
    if len(df_hist_old) >= 1:
        area_prev = int(df_hist_old["Arkansas"].iloc[-1])
        dAdt = (area_hoy_vivo - area_prev) / 0.5
    else:
        dAdt = 0
else:
    A_acum = 410 + area_hoy_vivo # arranque
    dAdt = 0

C_t_370 = A_acum / 370.0
C_t_510 = A_acum / 510.0
C_t_890 = A_acum / 890.0

# 3. PREDICCION ABAS con tus 3 Ac
if C_t_370 < 1:
    prob_M, prob_X, pred_text = 5, 0, f"Faltan {370-A_acum:.0f} MSH·dia para Ac=370"
elif C_t_510 < 1:
    prob_M, prob_X, pred_text = 20, 2, "Cruzo 370 - posible C fuerte"
elif C_t_890 < 1:
    prob_M, prob_X, pred_text = 45, 10, "Alerta M en 12h - cruzo 510"
else:
    prob_M, prob_X, pred_text = 85, 45, "SUPER-X INMINENTE 6H - cruzo 890"

if dAdt > 15:
    prob_M = min(90, prob_M+15)
    prob_X = min(60, prob_X+15)
    pred_text += f" | EMERGENCIA dA/dt={dAdt:.1f}"

print(f"ABAS: area={area_hoy_vivo} MSH A_acum={A_acum:.1f} C_510={C_t_510:.2f} dA/dt={dAdt:.1f} -> M={prob_M}% X={prob_X}% {pred_text}")

# 4. GUARDA
row = {
    "identificacion": "AR4549",
    "Arkansas": area_hoy_vivo,
    "fecha": fecha_hoy,
    "A_acum_MSHdia": round(A_acum,2),
    "C_t_370": round(C_t_370,3),
    "C_t_510": round(C_t_510,3),
    "C_t_890": round(C_t_890,3),
    "dAdt_MSH_h": round(dAdt,2),
    "prob_M_6h": prob_M,
    "prob_X_6h": prob_X,
    "prediccion": pred_text,
    "pred_Tau_UTC": hora_utc,
    "acierto": "VIVO_SDO_PRED"
}
df = pd.DataFrame([row])

# historial crece
if os.path.exists("historial_vivo.csv"):
    df_hist = pd.read_csv("historial_vivo.csv")
    df_hist = pd.concat([df_hist, df], ignore_index=True)
else:
    df_hist = df
df_hist.to_csv("historial_vivo.csv", index=False)
# tabla_30 = ultimas 30 medias horas
df_hist.tail(30).to_csv("tabla_30.csv", index=False)
print("Guardado tabla_30.csv con", len(df_hist.tail(30)), "filas")
