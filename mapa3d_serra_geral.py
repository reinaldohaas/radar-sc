# -*- coding: utf-8 -*-
"""Mapa 3D regional, do litoral à Serra Geral, com cores hipsométricas e as posições do radar.

Relevo: SRTM (tiles Terrarium, zoom 11, ~67 m) na região; o MDS de 1 m do SIGSC não cobre a Serra Geral.
Marca a posição atual, as duas propostas, cidades e a escarpa da Serra Geral, com coordenadas.
Também desenha, sobre o relevo, a linha do centro do feixe de 0,5° da posição atual para alguns azimutes,
mostrando onde ela encontra a Serra.

Saída: relatorio/figuras/v3_mapa3d_serra_geral.png
"""
import math
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, LinearSegmentedColormap

from relevo import Relevo
from simular_bloqueio import destino

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
ATUAL = (-28.934548, -49.362490)
POS = [("Radar atual", -28.934548, -49.362490, "red"),
       ("P1: topo do Morro dos Conventos", -28.937250, -49.367620, "blue"),
       ("P2: Morro das Antenas", -28.843869, -49.398756, "blue")]
CIDADES = {"Araranguá": (-28.935, -49.486), "Criciúma": (-28.678, -49.370), "Tubarão": (-28.467, -49.007),
           "Laguna": (-28.483, -48.781), "Sombrio": (-29.106, -49.629), "Turvo": (-28.926, -49.679),
           "Timbé do Sul": (-28.828, -49.843), "Praia Grande": (-29.197, -49.952), "Jacinto Machado": (-28.997, -49.763),
           "Urussanga": (-28.518, -49.320), "Orleans": (-28.359, -49.291), "Lauro Müller": (-28.393, -49.397)}
LON = (-50.20, -48.75)
LAT = (-29.35, -28.30)
# cores hipsométricas: mar, planície, morros, serra, planalto
HIPSO = LinearSegmentedColormap.from_list("hipso", [
    (0.00, "#3a7d2a"), (0.02, "#6aa84f"), (0.08, "#a8c97f"), (0.18, "#e3d98f"), (0.32, "#d6a55a"),
    (0.50, "#b0743c"), (0.70, "#8a5a3a"), (0.85, "#9e8f86"), (1.00, "#f2f2f2")])


def main():
    rel = Relevo(*ATUAL, fino_km=1.0, largo_km=110)
    passo = 0.004
    lo = np.arange(LON[0], LON[1], passo)
    la = np.arange(LAT[1], LAT[0], -passo)
    LO, LA = np.meshgrid(lo, la)
    D = np.full(LO.shape, 999.0)
    Z = rel(LA, LO, D)
    agua = ~np.isfinite(Z) | (Z < 1.0)
    Z = np.clip(np.nan_to_num(Z, nan=0.0), 0, None)
    ls = LightSource(azdeg=300, altdeg=35)
    rgb = ls.shade(Z, cmap=HIPSO, vert_exag=0.02, blend_mode="soft", vmin=0, vmax=1700)[..., :3]
    rgb[agua] = (0.55, 0.72, 0.90)
    EX = 2.2
    fig = plt.figure(figsize=(19, 13), dpi=100)
    ax = fig.add_subplot(projection="3d", computed_zorder=False)
    ax.plot_surface(LO, LA, Z * EX, facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)

    # centro do feixe de 0,5° da posição atual (antena ~71 m): onde encontra o relevo, até 60 km
    Re = 8495e3
    for az in (240, 255, 270, 285, 300, 315, 330):
        ds = np.arange(200, 60001, 400.0)
        h = np.sqrt(ds ** 2 + Re ** 2 + 2 * ds * Re * math.sin(math.radians(0.5))) - Re + 70.8
        pla, plo = destino(*ATUAL, az, ds)
        zt = rel(pla, plo, ds / 1000)
        bate = np.flatnonzero(zt >= h)
        k = bate[0] if len(bate) else len(ds) - 1
        ax.plot(plo[:k + 1], pla[:k + 1], h[:k + 1] * EX, color="yellow", lw=1.4)
        if len(bate):
            ax.scatter([plo[k]], [pla[k]], [h[k] * EX], color="yellow", edgecolor="k", s=25)

    for nome, (cla, clo) in CIDADES.items():
        z = float(np.nan_to_num(rel(np.array([cla]), np.array([clo]), np.array([999.0]))[0])) * EX
        ax.scatter([clo], [cla], [z + 30], color="k", s=10)
        ax.text(clo, cla, z + 120, nome, fontsize=8, color="k")
    topo = 1700 * EX
    desl = {"Radar atual": (0.06, -0.06), "P1: topo do Morro dos Conventos": (0.02, -0.13), "P2: Morro das Antenas": (0.06, 0.05)}
    for nome, pla, plo, cor in POS:
        z = float(np.nan_to_num(rel(np.array([pla]), np.array([plo]), np.array([999.0]))[0])) * EX
        ax.plot([plo, plo], [pla, pla], [z, topo], color=cor, lw=2.2)
        dx, dy = desl[nome]
        ax.plot([plo, plo + dx], [pla, pla + dy], [topo, topo], color=cor, lw=0.8)
        ax.text(plo + dx, pla + dy, topo, f"{nome}\n{pla:.5f}, {plo:.5f}", color=cor, fontsize=9.5, weight="bold",
                bbox=dict(fc="white", ec=cor, alpha=0.9, pad=1.5))
    ax.text(-50.05, -28.80, 2300 * EX, "SERRA GERAL\n(escarpa, 1.000–1.400 m)", color="saddlebrown", fontsize=11, weight="bold")
    ax.text(-48.95, -29.05, 50, "Oceano Atlântico", color="navy", fontsize=10, style="italic")
    ax.set_box_aspect((np.ptp(lo) * math.cos(math.radians(-28.8)), np.ptp(la), 0.20))
    ax.view_init(42, -100)
    ax.set_xlabel("Longitude (°)", labelpad=12); ax.set_ylabel("Latitude (°)", labelpad=12); ax.set_zticks([])
    ax.ticklabel_format(useOffset=False)
    sm = plt.cm.ScalarMappable(cmap=HIPSO, norm=plt.Normalize(0, 1700))
    fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.02, label="Altitude (m)")
    ax.set_title("Do litoral à Serra Geral (SRTM, exagero vertical 2,2×): posições do radar e, em amarelo, o centro do feixe "
                 "de 0,5° da posição atual até tocar o relevo", fontsize=12)
    saida = AQUI / "relatorio" / "figuras" / "v3_mapa3d_serra_geral.png"
    fig.savefig(saida, bbox_inches="tight"); plt.close(fig)
    print(saida)


if __name__ == "__main__":
    main()
