import csv, requests, datetime, os, time
from io import BytesIO
import numpy as np
from PIL import Image

ZENODO_TOKEN = os.getenv("ZENODO_TOKEN")
AR = "AR4549"
CSV = "tabla_30.csv"

THRESH = 60
AC_CRIT = 510
FACTOR = 1.36

def get_prev_mh():
    try:
        with open(CSV, "r") as f:
            rows = list(csv.reader(f))
            # busca de abajo hacia arriba un número válido
            for r in reversed(rows):
                try:
                    # intenta columna 2 (formato viejo) y columna 3 (formato Arkansas)
                    val = int(r[2])
                    if val > 50 and val < 5000:
                        return val
                except:
                    try:
                        val = int(r[3])
                        if val > 50 and val < 5000:
                            return val
                    except:
                        continue
    except:
        pass
    return 400

def get_MH_ahora():
    url = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIC.jpg"
    r = requests.get(url, timeout=30)
    img = Image.open(BytesIO(r.content)).convert("L")
    arr = np.array(img)
    y1, y2 = 450, 900
    x1, x2 = 500, 950
    roi = arr[y1:y2, x1:x2]
    dark = np.sum(roi < THRESH)
    MH = int(dark * FACTOR)

    prev = get_prev_mh()
    if MH < 100 and prev > 250:
        print(f"[FIX ABAS] caida {MH} -> {int(prev*0.95)}")
        MH = int(prev * 0.95)
    if MH < 50:
        MH = prev
    return max(MH, 50)

def main():
    mh = get_MH_ahora()
    ahora = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    existe = os.path.exists(CSV) and os.path.getsize(CSV) > 0

    with open(CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["tiempo", "AR", "MH", "C(t)"])
        ct = mh / AC_CRIT
        writer.writerow([ahora, AR, mh, f"{ct:.2f}"])

    print(f"OK {ahora} MH={mh} C(t)={mh/AC_CRIT:.2f} FACTOR={FACTOR}")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"ERROR {e}")
            time.sleep(300)
            continue
        print("Durmiendo 30 min...")
        time.sleep(1800)
