import csv, requests, datetime, os
from io import BytesIO
import numpy as np
from PIL import Image

ZENODO_TOKEN = os.getenv("ZENODO_TOKEN")
AR = "AR4549"

def get_MH_ahora():
    # 1. Jala continuum HMI del SDO (última imagen)
    url = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIC.jpg"
    # En producción usa JSOC 4K: http://jsoc.stanford.edu/data/hmi/images/
    r = requests.get(url, timeout=20)
    img = Image.open(BytesIO(r.content)).convert("L")
    arr = np.array(img)

    # 2. Región AR4549 - la sacas del SRS, aprox centro del disco ahorita
    # Por ahora threshold simple para demo: pixeles muy oscuros = mancha
    # Tú ajustas el crop a las coordenadas reales de AR4549
    dark_pixels = np.sum(arr < 50) # ajusta este 50 según HMI
    total_sun_pixels = np.pi * (512**2) # para 1024 img

    MH = int((dark_pixels / total_sun_pixels) * 1_000_000)
    return max(MH, 10) # evita 0

def predecir_flare(historial):
    # historial = lista de [timestamp, MH] últimos 30 días
    if len(historial) < 4:
        return None

    mh_ahora = historial[-1][1]
    mh_1h = historial[-3][1] if len(historial)>=3 else mh_ahora
    dMH_dt = mh_ahora - mh_1h # crecimiento por hora

    # Lógica de predicción para El Tajín
    prob_M, prob_X, prob_sX = 0.2, 0.05, 0.01
    if dMH_dt > 40: prob_M = 0.75
    if dMH_dt > 40 and mh_ahora > 450: prob_X = 0.65
    if mh_ahora > 600 and dMH_dt > 60: prob_sX = 0.4

    hora_pred = datetime.datetime.utcnow() + datetime.timedelta(hours=6)

    if prob_X > 0.6:
        return {"clase": "X", "prob": prob_X, "hora": hora_pred, "dMH": dMH_dt}
    if prob_M > 0.6:
        return {"clase": "M", "prob": prob_M, "hora": hora_pred, "dMH": dMH_dt}
    return None

def guardar_y_avisar():
    mh = get_MH_ahora()
    ahora = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M")

    # Guarda cada 30 min
    with open("tabla_30.csv", "a", newline="") as f:
        csv.writer(f).writerow([ahora, AR, mh])

    # Lee historial
    historial = []
    try:
        with open("tabla_30.csv") as f:
            for row in csv.reader(f):
                historial.append([row[0], int(row[2])])
    except: pass
    historial.append([ahora, mh])

    pred = predecir_flare(historial)
    if pred:
        print(f"ALERTA {pred['clase']} prob {pred['prob']} a las {pred['hora']} MH={mh} dMH={pred['dMH']}")
        # Aviso a Zenodo
        if ZENODO_TOKEN:
            requests.post("https://zenodo.org/api/deposit/depositions",
                params={"access_token": ZENODO_TOKEN},
                json={"metadata": {"title": f"Alerta {AR} {pred['clase']} {pred['hora']}",
                                   "upload_type": "dataset",
                                   "description": f"MH={mh} dMH/dt={pred['dMH']} pred {pred['clase']}",
                                   "creators": [{"name": "El Tajin Monitor"}]}},
                timeout=20
            )

if __name__ == "__main__":
    guardar_y_avisar()
