# -*- coding: utf-8 -*-
"""Altura da superfície acima do terreno (MDS − MDT) em volta do radar, com e sem a correção das encostas.

MDS e MDT do SIGSC vêm de processamentos diferentes e têm pequenos deslocamentos horizontais entre si. Numa encosta
íngreme, 1–3 m de deslocamento viram 10–30 m de "altura" falsa no MDS − MDT (a falésia leste do Morro dos Conventos
aparece como uma faixa verde-escura). A correção compara o MDS com o terreno mais alto num raio de `R_CORR` metros:
  altura = MDS − máx(MDT num disco de R_CORR m)
o que remove o efeito de deslocamentos até R_CORR m e mantém árvores e construções em terreno plano ou suave.
Nas falésias (declividade do MDT > 30°) o MDT suaviza a parede numa rampa, enquanto o MDS a mostra quase vertical:
a diferença chega a 40 m e não é mata. Perto delas o raio passa a R_FALESIA m.

Gera relatorio/figuras/v3_altura_superficie.png (sem e com correção) e relatorio/mds_altura_pontos.csv.
"""
import csv
import math
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer
from scipy.ndimage import maximum_filter, median_filter

from relevo_sigsc import ACERVO_MDS, PADRAO, PADRAO_MDS, PONTOS, Mosaico, folhas

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
ATUAL = PONTOS["radar (antena 49 m)"]
R_CORR = 3
R_FALESIA = 15


def main():
    t = Transformer.from_crs("EPSG:4326", "EPSG:31982", always_xy=True)
    x, y = t.transform(ATUAL[1], ATUAL[0])
    lim = (x - 2000, y - 1400, x + 800, y + 1600)
    mds = Mosaico(folhas(PADRAO_MDS, ACERVO_MDS), 1.0, lim)
    mdt = Mosaico(folhas(PADRAO), 1.0, lim)
    assert mds.alt.shape == mdt.alt.shape
    s = median_filter(mds.alt, size=3)
    bruto = s - mdt.alt
    disco = np.hypot(*np.mgrid[-R_CORR:R_CORR + 1, -R_CORR:R_CORR + 1]) <= R_CORR
    corr = s - maximum_filter(mdt.alt, footprint=disco)
    # declividade do terreno
    gy, gx = np.gradient(mdt.alt)
    decl = np.degrees(np.arctan(np.hypot(gx, gy)))
    # Falésias: o MDT suaviza a parede em rampa e o MDS a mostra quase vertical; a diferença não é mata.
    # Perto de encostas > 30° compara com o terreno mais alto num raio de R_FALESIA m.
    disco_f = np.hypot(*np.mgrid[-R_FALESIA:R_FALESIA + 1, -R_FALESIA:R_FALESIA + 1]) <= R_FALESIA
    perto_falesia = maximum_filter(decl > 30, footprint=disco_f)
    corr = np.where(perto_falesia, s - maximum_filter(mdt.alt, footprint=disco_f), corr)

    linhas = [["ponto", "mdt_m", "mds_m", "altura_bruta_m", "altura_corrigida_m", "max_bruta_raio40m", "max_corrigida_raio40m"]]
    for n, (la, lo) in PONTOS.items():
        px, py = t.transform(lo, la)
        c, l = ~mds.transform * (px, py)
        c, l = int(c), int(l)
        if not (40 <= l < s.shape[0] - 40 and 40 <= c < s.shape[1] - 40):
            continue
        yy, xx = np.mgrid[-40:41, -40:41]
        m = np.hypot(yy, xx) <= 40
        jb, jc = bruto[l - 40:l + 41, c - 40:c + 41][m], corr[l - 40:l + 41, c - 40:c + 41][m]
        linhas.append([n, f"{mdt.alt[l, c]:.1f}", f"{s[l, c]:.1f}", f"{bruto[l, c]:.1f}", f"{corr[l, c]:.1f}",
                       f"{np.nanmax(jb):.1f}", f"{np.nanmax(jc):.1f}"])
    with open(AQUI / "relatorio" / "mds_altura_pontos.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)
    for l in linhas:
        print(l)
    ingreme = decl > 30
    print(f"encostas > 30°: altura bruta mediana {np.nanmedian(bruto[ingreme]):.1f} m, corrigida {np.nanmedian(corr[ingreme]):.1f} m; "
          f"p95 {np.nanpercentile(bruto[ingreme], 95):.1f} -> {np.nanpercentile(corr[ingreme], 95):.1f} m")

    # figura
    ny, nx = s.shape
    E = lim[0] + np.arange(nx) + 0.5
    N = lim[3] - np.arange(ny) - 0.5
    para_geo = Transformer.from_crs("EPSG:31982", "EPSG:4326", always_xy=True)
    pts = {k: t.transform(v[1], v[0]) for k, v in PONTOS.items()}
    fig, eixos = plt.subplots(1, 2, figsize=(17, 8.5), dpi=90, sharey=True)
    for ax, arr, titulo in ((eixos[0], bruto, "MDS − MDT, sem correção (faixas falsas nas encostas)"),
                            (eixos[1], corr, f"Corrigido: terreno mais alto num raio de {R_CORR} m ({R_FALESIA} m perto de falésias)")):
        m = ax.imshow(np.clip(arr, 0, None)[::2, ::2], extent=(E[0], E[-1], N[-1], N[0]), cmap="YlGn", vmin=0, vmax=30)
        ax.contour(E[::4], N[::4], mdt.alt[::4, ::4], levels=[10, 30, 50, 65], colors="k", linewidths=0.4)
        for k, cor, rot in (("radar (antena 49 m)", "red", "Radar"), ("proposta (topo Conventos)", "blue", "Topo do morro"),
                            ("colina (57 m)", "purple", "Colina"), ("vila (~10 m)", "brown", "Vila")):
            px, py = pts[k]
            ax.plot(px, py, "o", color=cor, mec="k", ms=8); ax.text(px + 40, py + 30, rot, fontsize=9, weight="bold")
        for a0, a1, cor in ((321, 324, "red"), (352, 356, "orange"), (268, 271, "cyan")):
            for a in (a0, a1):
                ax.plot([pts["radar (antena 49 m)"][0], pts["radar (antena 49 m)"][0] + 3000 * math.sin(math.radians(a))],
                        [pts["radar (antena 49 m)"][1], pts["radar (antena 49 m)"][1] + 3000 * math.cos(math.radians(a))], color=cor, lw=0.9)
        ax.set_xlim(E[0], E[-1]); ax.set_ylim(N[-1], N[0]); ax.set_aspect("equal")
        ax.set_title(titulo, fontsize=11); ax.set_xlabel("UTM 22S, E (m)")
    eixos[0].set_ylabel("UTM 22S, N (m)")
    fig.colorbar(m, ax=eixos, shrink=0.8, label="Altura acima do terreno (m, SIGSC 2010–2012)")
    fig.suptitle("Morro dos Conventos: altura da mata e das construções (MDS − MDT, SIGSC 1 m)")
    fig.savefig(AQUI / "relatorio" / "figuras" / "v3_altura_superficie.png", bbox_inches="tight"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
