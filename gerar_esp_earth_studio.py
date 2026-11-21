# -*- coding: utf-8 -*-
"""Projeto do Google Earth Studio (.esp): demonstração do radar de Araranguá e das duas posições propostas.

Parte de um projeto exportado pelo próprio Earth Studio (modelo) e grava quadros-chave de:
  - posição da câmera (longitude, latitude, altitude);
  - ponto de interesse do efeito "Camera Target" (a câmera olha sempre para ele).
Roteiro (130 s): chegada pelo mar → volta em torno do radar atual (feixes batendo na mata e no farol) →
proposta 1, topo do Morro dos Conventos → proposta 2, Morro das Antenas → visadas do feixe de 0,5° até a
Serra Geral (a câmera sobe atrás do radar, percorre a visada de 270° e varre os pontos onde o feixe toca o relevo,
de 250° a 330°) → vista geral.

No .esp os valores são relativos à faixa de cada atributo:
  longitude = −180 + 360·r; latitude = −90 + 180·r; altitude = mín + r·(máx − mín).
O tempo dos quadros-chave é a fração da duração da cena (0 a 1).

O KML dos feixes (kml/feixes_radar_ararangua.kml) não vai embutido: o Earth Studio guarda os KMLs no Google Drive.
Depois de importar o projeto, use Overlays → Import KML.

Uso:
  python gerar_esp_earth_studio.py "C:\\Users\\...\\Downloads\\Radar Ararangua.esp"
Saída: kml/radar_ararangua_voo.esp (fora do git).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

from simular_bloqueio import destino

AQUI = Path(__file__).resolve().parent
OFFSET = -12.0                     # mesma referência do KMZ (terreno do Google ~12 m abaixo do SIGSC)
ATUAL = (-28.934548, -49.362490, 67.8 + 3 + OFFSET)
P1 = (-28.93725, -49.36762, 69.2 + 25 + OFFSET)
P2 = (-28.843869, -49.398756, 255.1 + 25 + OFFSET)
GERAL = (-28.885, -49.385, 150.0)
SEGUNDOS = 130
FPS = 30


def rel_lon(x):
    return (x + 180) / 360


def rel_lat(y):
    return (y + 90) / 180


def quadro(t, v):
    tr = {"x": 0, "y": 0, "influence": 0, "type": "auto"}
    return {"time": round(t, 5), "value": v, "transitionIn": dict(tr), "transitionOut": dict(tr), "transitionLinked": True}


def volta(centro, raio, alt, t0, t1, az0, graus, n):
    """Pontos de uma volta (ou arco) em torno de `centro`, com a câmera olhando para ele."""
    pts = []
    for k in range(n + 1):
        az = (az0 + graus * k / n) % 360
        la, lo = destino(centro[0], centro[1], az, raio)
        pts.append((t0 + (t1 - t0) * k / n, float(la), float(lo), alt, centro))
    return pts


def toque(az, rel):
    """Ponto onde o centro do feixe de 0,5° da posição atual (antena a 70,8 m) toca o relevo SRTM."""
    Re = 8495e3
    ds = np.arange(200, 80001, 250.0)
    h = np.sqrt(ds ** 2 + Re ** 2 + 2 * ds * Re * math.sin(math.radians(0.5))) - Re + 70.8
    la, lo = destino(ATUAL[0], ATUAL[1], float(az), ds)
    zt = rel(la, lo, ds / 1000)
    bate = np.flatnonzero(zt >= h)
    k = int(bate[0]) if len(bate) else len(ds) - 1
    return float(la[k]), float(lo[k]), float(h[k]) + OFFSET


def roteiro():
    """[(t, lat, lon, alt_camera, alvo)], t em segundos."""
    from relevo import Relevo
    rel = Relevo(ATUAL[0], ATUAL[1], fino_km=1.0, largo_km=110)
    p = [(0, -28.990, -49.290, 2500, ATUAL),
         (7, -28.950, -49.340, 700, ATUAL)]
    p += volta(ATUAL, 900, 220, 11, 36, 135, 360, 12)                # radar atual: volta completa
    p += volta(P1, 700, 230, 41, 54, 120, 180, 6)                    # proposta 1: meia volta
    p += [(59, -28.875, -49.360, 900, P2)]                           # a caminho da proposta 2
    p += volta(P2, 1500, 650, 65, 81, 160, 240, 8)                  # proposta 2: 2/3 de volta
    # visadas até a Serra Geral
    s270 = toque(270, rel)
    p += [(88, -28.950, -49.250, 3500, s270)]                        # atrás do radar, sobre o mar, olhando para oeste
    la, lo = destino(ATUAL[0], ATUAL[1], 270.0, 30000.0)
    p += [(96, float(la), float(lo), 1800, s270)]                    # ao longo da visada de 270°
    la, lo = destino(ATUAL[0], ATUAL[1], 90.0, 4000.0)
    for k, az in enumerate(range(250, 331, 10)):                     # varredura dos pontos de toque
        p.append((101 + 2.5 * k, float(la), float(lo), 2500, toque(az, rel)))
    p += [(130, -29.060, -49.150, 14000, (-28.88, -49.62, 300.0))]
    return [(t / SEGUNDOS, la, lo, h, a) for t, la, lo, h, a in p]


def main():
    modelo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "Radar Ararangua.esp"
    esp = json.loads(modelo.read_text(encoding="utf-8"))
    quadros = SEGUNDOS * FPS
    esp["settings"]["duration"] = quadros
    esp["settings"]["name"] = "Radar Ararangua - posicoes e visadas da Serra Geral"
    esp["playbackManager"]["range"] = {"start": 0, "end": quadros}
    cena = esp["scenes"][0]
    cena["duration"] = quadros
    cena["world"]["kmls"] = []      # o KML novo é importado no próprio Earth Studio

    pts = roteiro()
    cam = next(a for a in cena["attributes"] if a["type"] == "cameraGroup")
    pos = next(a for a in cam["attributes"] if a["type"] == "cameraPositionGroup")
    pos = next(a for a in pos["attributes"] if a["type"] == "position")
    for at in pos["attributes"]:
        if at["type"] == "longitude":
            at["keyframes"] = [quadro(t, rel_lon(lo)) for t, la, lo, h, _ in pts]
        elif at["type"] == "latitude":
            at["keyframes"] = [quadro(t, rel_lat(la)) for t, la, lo, h, _ in pts]
        elif at["type"] == "altitude":
            mn, mx = at["value"]["minValueRange"], at["value"]["maxValueRange"]
            at["keyframes"] = [quadro(t, (h - mn) / (mx - mn)) for t, la, lo, h, _ in pts]
        at["value"].pop("relative", None)

    alvo = next(a for a in cam["attributes"] if a["type"] == "cameraTargetEffect")
    alvo["inTimeline"] = True
    for at in alvo["attributes"]:
        if at["type"] in ("enabled", "influence"):
            at["value"] = {"relative": 1}
        elif at["type"] == "poi":
            at["inTimeline"] = True
            for p in at["attributes"]:
                p["inTimeline"] = True
                if p["type"] == "longitudePOI":
                    p["keyframes"] = [quadro(t, rel_lon(a[1])) for t, *_, a in pts]
                elif p["type"] == "latitudePOI":
                    p["keyframes"] = [quadro(t, rel_lat(a[0])) for t, *_, a in pts]
                elif p["type"] == "altitudePOI":
                    mn, mx = p["value"]["minValueRange"], p["value"]["maxValueRange"]
                    p["keyframes"] = [quadro(t, (a[2] - mn) / (mx - mn)) for t, *_, a in pts]
                p["value"].pop("relative", None)

    saida = AQUI / "kml" / "radar_ararangua_voo.esp"
    saida.write_text(json.dumps(esp, separators=(",", ":")), encoding="utf-8")
    print(saida, f"{len(pts)} quadros-chave, {SEGUNDOS} s")


if __name__ == "__main__":
    main()
