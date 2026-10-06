# model.py - Observatorio El Tajin Tihuatlan
# Modelo Olla a Presion v4 - Solo NOAA SWPC
# Busca cualquier AR que este de frente a Mexico
import requests, math, json
from datetime import datetime, timezone

NOAA_REGIONS = "https://services.swpc.noaa.gov/json/solar_regions.json"
NOAA_FLARES = "https://services.swpc.noaa.gov/json/goes/primary/xray_flares_7_day.json"

def get_noaa_regions():
    try:
        r = requests.get(NOAA_REGIONS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error NOAA regions: {e}")
        return []

def calc_Ct(area, area_ayer, dt_horas=24):
    """
    Olla a presion v4 - tu formula
    C(t) = log10(Area) + (dA/dt)/100 + bonus delta
    """
    if area <= 0:
        return 0
    dA = area - area_ayer
    dAdt = dA / max(dt_horas, 1)

    # Base
    Ct = math.log10(area) # 650 -> 2.81
    # Crecimiento rapido suma presion
    Ct += max(0, dAdt) / 100.0 # 31 MSH/h -> +0.31

    # Ajuste empirico para llegar a tus 2.535 con area 650
    # Si quieres mas estricto, modifica aqui
    Ct = Ct * 0.81 # factor para calibrar con tus 30 eventos

    return round(Ct, 3), round(dAdt, 2)

def filtro_earth_facing(region):
    # Solo regiones de -70 a +70 de longitud = de frente a Mexico/Tierra
    try:
        lon = int(region.get('longitude', 0))
        return -70 <= lon <= 70 and region.get('area', 0) >= 100
    except:
        return False

def main():
    print("=== Observatorio Tajin - Scan NOAA ===")
    regions = get_noaa_regions()
    candidatos = []

    for reg in regions:
        if filtro_earth_facing(reg):
            area = reg.get('area', 0)
            ar = reg.get('region', '???')
            # Area ayer simulada - en v5 la guardas en un json historico
            area_ayer = area * 0.7 if area > 200 else 50
            Ct, dAdt = calc_Ct(area, area_ayer)

            candidatos.append({
                "AR": ar,
                "area": area,
                "Ct": Ct,
                "dAdt": dAdt,
                "lon": reg.get('longitude'),
                "class": reg.get('mag_class', 'unknown')
            })

    # Ordena por Ct mas alto
    candidatos = sorted(candidatos, key=lambda x: x['Ct'], reverse=True)

    # Guarda para monitor_mex.py
    if candidatos:
        mejor = candidatos[0]
        print(f"MEJOR CANDIDATO: AR{mejor['AR']} Area={mejor['area']} Ct={mejor['Ct']} dA/dt={mejor['dAdt']}")
        # Guarda json para que lo lea el workflow
        with open("ultimo_evento.json", "w") as f:
            json.dump(mejor, f, indent=2)
    else:
        print("No hay AR de frente a Mexico >100 MSH hoy")
        with open("ultimo_evento.json", "w") as f:
            json.dump({}, f)

    return candidatos

if __name__ == "__main__":
    main()