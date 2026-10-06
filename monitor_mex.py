import csv, requests, datetime, os
from io import BytesIO
import numpy as np
from PIL import Image

ZENODO_TOKEN = os.getenv("ZENODO_TOKEN")
AR = "AR4549"

def get_MH_ahora():
    url = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIC.jpg"
    r = requests.get(url, timeout=30)
    img = Image.open(BytesIO(r.content)).convert("L")
    arr = np.array(img)
    dark = np.sum(arr < 50)
    total_sun = np.pi * (512**2)
    MH = int((dark / total_sun) * 1000000)
    return max(MH, 50)

def main():
    mh = get_MH_ahora()
    ahora = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    with open("tabla_30.csv", "a", newline="") as f:
        csv.writer(f).writerow([ahora, AR, mh])
    print(f"OK {ahora} MH={mh}")

if __name__ == "__main__":
    main()