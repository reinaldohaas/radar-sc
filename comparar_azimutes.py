# -*- coding: utf-8 -*-
"""Bloqueio do feixe ou chuva? Compara, entre vários volumes ODIM, os azimutes com falta de eco.

Bloqueio por obstáculo fixo apaga sempre os mesmos azimutes, chova onde chover. Chuva muda de lugar.
Em cada volume e elevação: fração de gates com eco (TH >= 20 dBZ e RhoHV >= 0,8) por raio, entre 10 e 60 km,
dividida pela média dos raios vizinhos (±5°). Raio "em falta": razão < 0,3 onde os vizinhos têm eco.

Uso:
  python comparar_azimutes.py amostras/ARA/*.hdf
"""
import sys
from pathlib import Path

import h5py
import numpy as np

from diagnostico_odim import campos

R0, R1, MIN_VIZ = 10.0, 60.0, 0.05


def perfil(ds):
    c = campos(ds)
    w = ds["where"].attrs
    rs = float(w["rscale"]) / 1000
    sel = slice(int(R0 / rs), int(R1 / rs))
    eco = (c["TH"][:, sel] >= 20) & (c["RHOHV"][:, sel] >= 0.8)
    az = np.asarray(ds["how"].attrs["startazA"], float)
    fr = np.zeros(360)
    np.add.at(fr, np.round(az).astype(int) % 360, eco.mean(axis=1))  # um valor por grau
    viz = np.convolve(np.r_[fr[-5:], fr, fr[:5]], np.r_[np.ones(5), 0, np.ones(5)] / 10, "valid")
    return fr, viz


def main():
    arquivos = sorted(Path(p) for a in sys.argv[1:] for p in (Path().glob(a) if "*" in a else [a]))
    if len(arquivos) < 2:
        print("Aviso: com um só horário não dá para separar bloqueio de chuva.")
    elevs = {}
    for f in arquivos:
        with h5py.File(f) as h:
            for k in sorted((k for k in h if k.startswith("dataset")), key=lambda k: int(k[7:]))[:3]:
                ele = round(float(h[k]["where"].attrs["elangle"]), 1)
                fr, viz = perfil(h[k])
                elevs.setdefault(ele, []).append((f.name.split("-")[2] + " " + f.name.split("-")[3], fr, viz))
    for ele, lista in sorted(elevs.items()):
        print(f"\nElevação {ele}°")
        falta = []
        for nome, fr, viz in lista:
            ok = viz >= MIN_VIZ                       # só onde há eco em volta
            f_ = ok & (fr < 0.3 * viz)
            falta.append((ok, f_))
            print(f"  {nome}: graus avaliáveis {ok.sum():3d}, em falta {f_.sum():3d}")
        if len(lista) < 2:
            continue
        # Para cada grau: em quantos horários avaliáveis ele estava em falta
        aval = np.sum([ok for ok, _ in falta], axis=0)
        em_falta = np.sum([f_ for _, f_ in falta], axis=0)
        fixos = np.flatnonzero((aval >= 2) & (em_falta >= 0.8 * aval))
        print(f"  graus em falta em >= 80% dos horários em que havia eco em volta (avaliados em >= 2): {len(fixos)}")
        if len(fixos):
            print("   ", ", ".join(f"{a}°" for a in fixos))
        # Concordância esperada ao acaso
        pares = [(i, j) for i in range(len(falta)) for j in range(i + 1, len(falta))]
        for i, j in pares[:10]:
            ambos = falta[i][0] & falta[j][0]
            if ambos.sum() < 10:
                continue
            a, b = falta[i][1] & ambos, falta[j][1] & ambos
            obs = (a & b).sum()
            esp = a.sum() * b.sum() / ambos.sum()
            print(f"  {lista[i][0]} x {lista[j][0]}: graus em falta nos dois = {obs} (ao acaso ~{esp:.1f}, de {ambos.sum()} comuns)")


if __name__ == "__main__":
    main()
