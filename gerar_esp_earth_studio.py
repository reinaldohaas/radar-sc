# -*- coding: utf-8 -*-
"""Projeto do Google Earth Studio (.esp) com um voo em volta do radar de Araranguá.

Parte de um projeto exportado pelo próprio Earth Studio (modelo), que já traz o KML dos feixes importado do Google
Drive do usuário, e acrescenta:
  - quadros-chave de posição da câmera (longitude, latitude, altitude): aproximação pelo mar, volta completa em
    torno da antena e afastamento;
  - o efeito "Camera Target" ligado e apontado para a antena, para a câmera olhar sempre para o radar.

No .esp os valores são relativos à faixa de cada atributo:
  longitude = −180 + 360·r; latitude = −90 + 180·r; altitude = mín + r·(máx − mín).
O tempo dos quadros-chave é a fração da duração da cena (0 a 1).

Uso:
  python gerar_esp_earth_studio.py "C:\\Users\\...\\Downloads\\Radar Ararangua.esp"
Saída: kml/radar_ararangua_voo.esp (não vai para o git: contém o endereço do KML no Google Drive do usuário).
"""
import copy
import json
import math
import sys
from pathlib import Path

from simular_bloqueio import destino

AQUI = Path(__file__).resolve().parent
RADAR = (-28.934548, -49.362490)
ALT_ANTENA = 70.8 - 12.0          # mesma referência do KMZ com --offset -12 (terreno do Google)
SEGUNDOS = 60
FPS = 30


def rel_lon(x):
    return (x + 180) / 360


def rel_lat(y):
    return (y + 90) / 180


def quadro(t, v):
    tr = {"x": 0, "y": 0, "influence": 0, "type": "auto"}
    return {"time": t, "value": v, "transitionIn": dict(tr), "transitionOut": dict(tr), "transitionLinked": True}


def trajeto():
    """[(t, lat, lon, alt)] com t em fração da duração."""
    p = [(0.00, -28.985, -49.300, 2500), (0.15, -28.955, -49.335, 900)]
    n = 16
    for k in range(n + 1):                        # volta completa, raio de 900 m, 220 m de altitude
        az = (135 + 360 * k / n) % 360
        la, lo = destino(*RADAR, az, 900.0)
        p.append((0.22 + 0.63 * k / n, float(la), float(lo), 220))
    p.append((1.00, -28.975, -49.320, 2200))
    return p


def main():
    modelo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "Radar Ararangua.esp"
    esp = json.loads(modelo.read_text(encoding="utf-8"))
    quadros = SEGUNDOS * FPS
    esp["settings"]["duration"] = quadros
    esp["settings"]["name"] = "Radar Ararangua - voo"
    esp["playbackManager"]["range"] = {"start": 0, "end": quadros}
    cena = esp["scenes"][0]
    cena["duration"] = quadros

    cam = next(a for a in cena["attributes"] if a["type"] == "cameraGroup")
    pos = next(a for a in cam["attributes"] if a["type"] == "cameraPositionGroup")
    pos = next(a for a in pos["attributes"] if a["type"] == "position")
    pts = trajeto()
    for at in pos["attributes"]:
        if at["type"] == "longitude":
            at["keyframes"] = [quadro(t, rel_lon(lo)) for t, la, lo, h in pts]
        elif at["type"] == "latitude":
            at["keyframes"] = [quadro(t, rel_lat(la)) for t, la, lo, h in pts]
        elif at["type"] == "altitude":
            mn, mx = at["value"]["minValueRange"], at["value"]["maxValueRange"]
            at["keyframes"] = [quadro(t, (h - mn) / (mx - mn)) for t, la, lo, h in pts]
        at["value"].pop("relative", None)

    alvo = next(a for a in cam["attributes"] if a["type"] == "cameraTargetEffect")
    for at in alvo["attributes"]:
        if at["type"] == "enabled":
            at["value"] = {"relative": 1}
        elif at["type"] == "influence":
            at["value"] = {"relative": 1}
        elif at["type"] == "poi":
            for p in at["attributes"]:
                if p["type"] == "longitudePOI":
                    p["value"] = {"relative": rel_lon(RADAR[1])}
                elif p["type"] == "latitudePOI":
                    p["value"] = {"relative": rel_lat(RADAR[0])}
                elif p["type"] == "altitudePOI":
                    mn, mx = p["value"]["minValueRange"], p["value"]["maxValueRange"]
                    p["value"]["relative"] = (ALT_ANTENA - mn) / (mx - mn)
    alvo["inTimeline"] = True

    saida = AQUI / "kml" / "radar_ararangua_voo.esp"
    saida.write_text(json.dumps(esp, separators=(",", ":")), encoding="utf-8")
    print(saida, f"{len(pts)} quadros-chave, {SEGUNDOS} s")


if __name__ == "__main__":
    main()
