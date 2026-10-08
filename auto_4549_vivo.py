import requests, io, re, os
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime

url = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIF.jpg"
backup = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIC.jpg"

def get_area(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("L")
    arr = np.array(img)
    h,w = arr.shape
    xc, yc = int(w*0.52), int(h*0.42) # N10E01
    b = 180
    roi = arr[yc-b:yc+b, xc-b:xc+b]
    umbra = np.sum(roi < 85)
    pen = np.sum((roi>=85)&(roi<160))
    msh = int(umbra*2.2 + pen*0.7) # calibración real
    return max(100, min(msh, 2500))

try:
    area = get_area(url)
    print(f"SDO HMIIF: {area} MSH")
except:
    try: area = get_area(backup)
    except:
        txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=10).text
        area = 700
        for l in txt.splitlines():
            if "4549" in l:
                nums = re.findall(r"\d{2,4}", l)
                if nums: area = int(nums[-1])

fecha = datetime.utcnow().strftime("%d-%m-%Y")
utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
dt = 0.5/24.0

if os.path.exists("historial_vivo.csv") and os.path.getsize("historial_vivo.csv")>60:
    old = pd.read_csv("historial_vivo.csv")
    area_prev = int(old["Arkansas"].iloc[-1])
    dAdt = (area - area_prev)/0.5
    A_acum = float(old["A_acum_MSHdia"].iloc[-1]) + area*dt
else:
    dAdt = 0
    A_acum = 410 + area # arranque ABAS
    print("Arranque nuevo 410+area")

C370, C510, C890 = A_acum/370, A_acum/510, A_acum/890

if C890 >=1: pM,pX,txt = 85,45,"SUPER-X INMINENTE 6H - cruzo 890"
elif C510 >=1: pM,pX,txt = 45,10,"Alerta M en 12h - cruzo 510"
elif C370 >=1: pM,pX,txt = 20,2,"Cruzo 370 - C fuerte"
else: pM,pX,txt = 5,0,f"Faltan {370-A_acum:.0f} para 370"

if dAdt>15:
    pM=min(90,pM+15); pX=min(60,pX+15)
    txt+=f" | EMERGENCIA dA/dt={dAdt:.1f}"

print(f"ABAS: area={area} A_acum={A_acum:.1f} C510={C510:.2f} -> M={pM}% X={pX}%")

row = {"identificacion":"AR4549","Arkansas":area,"fecha":fecha,"A_acum_MSHdia":round(A_acum,2),
"C_t_370":round(C370,3),"C_t_510":round(C510,3),"C_t_890":round(C890,3),
"dAdt_MSH_h":round(dAdt,2),"prob_M_6h":pM,"prob_X_6h":pX,"prediccion":txt,"pred_Tau_UTC":utc,"acierto":"VIVO_SDO_PRED"}

df = pd.DataFrame([row])
if 'old' in locals() and len(old)>0:
    pd.concat([old,df]).to_csv("historial_vivo.csv", index=False)
    hist = pd.read_csv("historial_vivo.csv")
else:
    hist = df
    hist.to_csv("historial_vivo.csv", index=False)

hist.tail(30).to_csv("tabla_30.csv", index=False)
print(f"tabla_30: {len(hist.tail(30))} filas")
