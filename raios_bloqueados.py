# -*- coding: utf-8 -*-
"""Classifica os raios de um volume de Araranguá a 0,5° (ou outra elevação): onde falta eco, e por quê.

Classes por raio (5–80 km):
  - "apagado pelo filtro": há chuva no TH (RhoHV médio ≥ 0,8, TH ≥ 15 dBZ, ≥ 20 gates) e o DBZH tem < 20% dela;
  - "sem eco, vizinhos com chuva": nem o TH nem o DBZH têm eco (< 5 gates), mas os raios a 2–8° de cada lado têm (mediana ≥ 30 gates);
    com bloqueio simulado ≥ 50% no azimute, é bloqueio; senão, sombra de atenuação ou falha;
  - "sombra de atenuação": a chuva termina logo após um núcleo ≥ 45 dBZ, enquanto os vizinhos seguem com eco.
O bloqueio simulado vem de dem/pbb_azimute_mds.npz (gerar_kmz_3d.py: MDS do SIGSC + 6 m de mata).

Uso:  python raios_bloqueados.py cache_vol/ARA/9842SAN-PPIVol-20261119-171651-0000.hdf [--elev 0.5]
Saída: relatorio/figuras/raios_<data>.png, relatorio/raios_<data>.csv, kml/raios_<data>.kml
"""
import argparse
import csv
import math
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from analise_polarimetrica import ler
from leitor_odim import RHOHV_MIN, ZONA_CEGA_KM, _suavizar
from simular_bloqueio import destino

AQUI = Path(__file__).resolve().parent
RADAR = (-28.934548, -49.362490)
CORES = {"apagado pelo filtro": "#d62728", "bloqueado (sem eco; simulado ≥ 50%)": "#000000",
         "sem eco, vizinhos com chuva": "#7f7f7f", "sombra de atenuação": "#9467bd"}
KML_COR = {"apagado pelo filtro": "ff2827d6", "bloqueado (sem eco; simulado ≥ 50%)": "ff000000",
           "sem eco, vizinhos com chuva": "ff7f7f7f", "sombra de atenuação": "ffbd6794"}


def classificar(az, dr, q, pbb_sim, r_max=80.0):
    th, dbzh = q["TH"], q["DBZH"]
    r = (np.arange(th.shape[1]) + 0.5) * dr
    faixa = (r >= 5) & (r <= r_max)
    chuva = (_suavizar(q["RHOHV"], dr) >= RHOHV_MIN) & (th >= 15) & faixa[None, :]
    n_th = chuva.sum(1)
    n_db = (chuva & np.isfinite(dbzh)).sum(1)
    # eco de qualquer tipo: chuva no TH ou algo no DBZH (a máscara de RhoHV tira chuva fraca de baixo SNR)
    eco = chuva | (np.isfinite(dbzh) & (th >= 15) & faixa[None, :])
    n_eco = eco.sum(1)
    ult = np.array([np.flatnonzero(c)[-1] if c.any() else -1 for c in eco])
    n10 = int(10 / dr)
    nr = len(az)
    classe = [""] * nr
    for i in range(nr):
        viz = [(i + k) % nr for k in list(range(-8, -1)) + list(range(2, 9))]
        mviz = np.median(n_eco[viz])
        if n_th[i] >= 20 and n_db[i] < 0.2 * n_th[i]:
            classe[i] = "apagado pelo filtro"
        elif n_eco[i] < 5 and mviz >= 30:
            classe[i] = "bloqueado (sem eco; simulado ≥ 50%)" if pbb_sim[int(az[i]) % 360] >= 0.5 else "sem eco, vizinhos com chuva"
        elif 0 <= ult[i] < th.shape[1] - n10 and r[ult[i]] < r_max - 10:
            nucleo = np.nanmax(th[i, max(0, ult[i] - n10):ult[i] + 1]) >= 45
            if nucleo and np.mean([ult[v] > ult[i] + n10 for v in viz]) >= 0.5:
                classe[i] = "sombra de atenuação"
    return r, chuva, n_th, n_db, classe


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo")
    ap.add_argument("--elev", type=float, default=0.5)
    a = ap.parse_args()
    t = datetime.strptime(Path(a.arquivo).name.split("-PPIVol-")[1][:15], "%Y%m%d-%H%M%S")
    az, dr, q = ler(a.arquivo)[a.elev]
    pbb = np.load(AQUI / "dem" / "pbb_azimute_mds.npz")
    pbb_sim = pbb["atual_05"] if a.elev < 1 else pbb["atual_14"]
    r, chuva, n_th, n_db, classe = classificar(az, dr, q, pbb_sim)
    rot = f"{t:%Y%m%d_%H%M}_{a.elev:.1f}".replace(".", "")

    with open(AQUI / "relatorio" / f"raios_{rot}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["azimute", "gates_chuva_TH", "gates_DBZH", "bloqueio_simulado", "classe"])
        for i in range(len(az)):
            w.writerow([f"{az[i]:.1f}", n_th[i], n_db[i], f"{pbb_sim[int(az[i]) % 360]:.2f}", classe[i]])
    resumo = {c: sum(1 for x in classe if x == c) for c in CORES}
    print(f"{t:%d/%m %H:%M} UTC, {a.elev}°: raios com chuva no TH: {(n_th >= 20).sum()}; " +
          "; ".join(f"{c}: {n}" for c, n in resumo.items()))

    # figura
    lim = r <= 100
    T, R = np.meshgrid(np.radians(az), r[lim], indexing="ij")
    X, Y = R * np.sin(T), R * np.cos(T)
    cmap = ListedColormap(["#00e5e5", "#009de5", "#0000f5", "#00ff00", "#00c400", "#008c00", "#ffff00", "#e5bc00",
                           "#ff9900", "#ff0000", "#d40000", "#bc0000", "#f800fd"])
    norm = BoundaryNorm(np.arange(10, 80, 5), cmap.N)
    th_m = np.where(chuva, q["TH"], np.nan)[:, lim]
    db = q["DBZH"][:, lim]
    fig, eixos = plt.subplots(1, 3, figsize=(20, 7), dpi=90)
    for ax, campo, tit in ((eixos[0], th_m, "TH com máscara de RhoHV ≥ 0,8"),
                           (eixos[1], db, "DBZH (o que o produto mostra)")):
        m = ax.pcolormesh(X, Y, campo, cmap=cmap, norm=norm, shading="auto")
        ax.set_title(tit)
    ax = eixos[2]
    ax.pcolormesh(X, Y, th_m, cmap=cmap, norm=norm, shading="auto", alpha=0.35)
    for i, c in enumerate(classe):
        if c:
            ang = math.radians(az[i])
            ax.plot([5 * math.sin(ang), 80 * math.sin(ang)], [5 * math.cos(ang), 80 * math.cos(ang)], color=CORES[c], lw=1.2)
    for c, cor in CORES.items():
        ax.plot([], [], color=cor, lw=3, label=f"{c} ({resumo[c]})")
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title("Raios classificados")
    for ax in eixos:
        for rr in (20, 40, 60, 80):
            ax.add_patch(plt.Circle((0, 0), rr, fill=False, color="0.6", lw=0.5, ls="--"))
        ax.plot(0, 0, "k+", ms=10); ax.set_aspect("equal"); ax.set_xlim(-100, 100); ax.set_ylim(-100, 100)
        ax.set_xlabel("km a leste")
    eixos[0].set_ylabel("km ao norte")
    fig.colorbar(m, ax=eixos[:2], shrink=0.8, label="dBZ")
    fig.suptitle(f"Araranguá, {a.elev}°, {t:%d/%m/%Y %H:%M} UTC: onde falta eco e por quê")
    fig.savefig(AQUI / "relatorio" / "figuras" / f"raios_{rot}.png", bbox_inches="tight"); plt.close(fig)

    # KML: um segmento por raio classificado, de 2,2 a 80 km
    marcas = []
    for i, c in enumerate(classe):
        if not c:
            continue
        pts = [destino(*RADAR, az[i], d * 1000) for d in (ZONA_CEGA_KM, 20, 40, 60, 80)]
        coords = " ".join(f"{lo:.6f},{la:.6f},0" for la, lo in pts)
        marcas.append(f"<Placemark><name>{az[i]:.0f}° — {c}</name><Style><LineStyle><color>{KML_COR[c]}</color><width>2</width>"
                      f"</LineStyle></Style><LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>")
    (AQUI / "kml" / f"raios_{rot}.kml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
        f"<name>Araranguá {a.elev}° — raios sem eco, {t:%d/%m/%Y %H:%M} UTC</name>{''.join(marcas)}</Document></kml>", encoding="utf-8")
    print("ok")


if __name__ == "__main__":
    main()
