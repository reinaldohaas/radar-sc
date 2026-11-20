# -*- coding: utf-8 -*-
"""Procura posições para o radar de Araranguá com menos bloqueio do feixe.

Para cada ponto candidato e altura de torre, simula o bloqueio (simular_bloqueio.py) com árvores e casas somadas ao
relevo em terra firme, e mede:
  - PBB médio a 60 km nas elevações 0,5° e 1,4° (fração média da potência perdida);
  - fração dos azimutes com PBB < 10% a 0,5° (horizonte "limpo").
A torre é contada acima do terreno do SRTM no ponto (o SRTM já inclui parte da copa).

Uso:
  python buscar_posicao.py            # grava dem/candidatos.csv
"""
import csv
import math
import sys
import time

import numpy as np

from relevo import Relevo
from simular_bloqueio import perfis, simular

ATUAL = (-28.934548, -49.362490)
H_ATUAL_SRTM = 67.0          # antena atual no referencial do SRTM (calibrada com os volumes observados)
OBST_M = 10.0                # árvores e casas sobre o terreno (cenário base); 20 m no pessimista
TORRES = (10.0, 20.0, 30.0)
AZ = np.arange(0, 360, 2.0)
MAX_KM = 60.0


def avaliar(lat, lon, h_antena, rel, obst=OBST_M):
    pf = perfis(lat, lon, rel, az=AZ, max_km=MAX_KM, obst_m=obst)
    _, d, pbb = simular(lat, lon, h_antena, rel, elevacoes=(0.5, 1.4), perfis_prontos=pf)
    i = len(d) - 1
    return {"pbb05": float(pbb[0.5][:, i].mean()), "pbb14": float(pbb[1.4][:, i].mean()),
            "limpo05": float(np.mean(pbb[0.5][:, i] < 0.1))}


def grade(centro, raio_km, passo_m):
    k = 111320 * math.cos(math.radians(centro[0]))
    n = int(raio_km * 1000 / passo_m)
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            if math.hypot(i, j) * passo_m <= raio_km * 1000:
                yield centro[0] + j * passo_m / 111130, centro[1] + i * passo_m / k


def main():
    rel = Relevo(*ATUAL, fino_km=4.0, largo_km=MAX_KM + 20)
    linhas = []
    base = avaliar(*ATUAL, H_ATUAL_SRTM, rel)
    linhas.append(["atual", *ATUAL, float(rel(ATUAL[0], ATUAL[1], 0)), H_ATUAL_SRTM - float(rel(ATUAL[0], ATUAL[1], 0)),
                   base["pbb05"], base["pbb14"], base["limpo05"]])
    print(f"Atual: PBB 0,5° {base['pbb05']:.2f}, 1,4° {base['pbb14']:.2f}, azimutes limpos a 0,5° {base['limpo05']:.0%}")
    buscas = [("morro", 2.0, 100), ("regiao", 15.0, 500)]
    for nome, raio, passo in buscas:
        pts = list(grade(ATUAL, raio, passo))
        alt = np.array([float(rel(la, lo, 0 if nome == "morro" else 99)) for la, lo in pts])
        # Na região, só os 8% mais altos (topos de morro); no morro, tudo acima de 20 m
        corte = np.percentile(alt, 92) if nome == "regiao" else 20.0
        sel = [(p, a) for p, a in zip(pts, alt) if a >= corte]
        print(f"{nome}: {len(sel)} candidatos (terreno >= {corte:.0f} m)", flush=True)
        t0 = time.time()
        for n, ((la, lo), a) in enumerate(sel):
            for t in TORRES:
                r = avaliar(la, lo, a + t, rel)
                linhas.append([nome, la, lo, a, t, r["pbb05"], r["pbb14"], r["limpo05"]])
            if n % 25 == 0:
                print(f"  {n}/{len(sel)} ({time.time() - t0:.0f} s)", flush=True)
    with open("dem/candidatos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["busca", "lat", "lon", "terreno_m", "torre_m", "pbb05", "pbb14", "limpo05"])
        w.writerows(linhas)
    print("dem/candidatos.csv")


if __name__ == "__main__":
    main()
