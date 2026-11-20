# -*- coding: utf-8 -*-
"""Torre no topo da colina de 57 m (o obstáculo principal a NW, 1,2 km a 323° do radar) e torre na posição atual,
comparadas com o topo do Morro dos Conventos e o Morro das Antenas.

Mesma configuração da versão 2 (MDT 1 m do SIGSC + mata, Terra 4/3). Torres de 15, 25 e 35 m; mata de 10, 15 e 20 m.

Gera:
  relatorio/sensibilidade_colina.csv
  relatorio/figuras/v2_pbb_colina.png   bloqueio (0,5° e 1,4°) com torre de 25 m: atual, colina, Conventos, Antenas
"""
import csv
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from relevo import Relevo
from relevo_sigsc import PONTOS, RelevoSIGSC
from simular_bloqueio import perfis, simular

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "relatorio"
FIG = SAIDA / "figuras"
POS = {"Atual": PONTOS["radar (antena 49 m)"], "Colina (obstáculo a NW)": PONTOS["colina (57 m)"],
       "Topo do Morro dos Conventos": PONTOS["proposta (topo Conventos)"], "Morro das Antenas": PONTOS["Morro das Antenas"]}
TORRES = (15, 25, 35)
MATAS = (10, 15, 20)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    atual = POS["Atual"]
    srtm = Relevo(*atual, fino_km=4.0, largo_km=100)
    rel = RelevoSIGSC(srtm, posicoes=list(POS.values()), raio_fino_km=2.0)

    az = np.arange(0, 360, 1.0)
    oeste = (az >= 240) & (az <= 340)
    norte = (az >= 300) | (az <= 30)
    linhas = [["posicao", "lat", "lon", "chao_mdt_m", "torre_m", "mata_m", "pbb05_30km", "pbb14_30km", "pbb05_60km",
               "pbb14_60km", "oeste_pbb05_30km", "oeste_pbb14_30km", "norte_pbb05_30km", "norte_pbb14_30km"]]
    fig_res = {}
    for nome, p in POS.items():
        chao = float(rel(*p))
        for mata in MATAS:
            pf = perfis(*p, rel, az=az, max_km=60, obst_m=mata)
            for t in TORRES:
                _, d, r = simular(*p, chao + t, rel, elevacoes=(0.5, 1.4), perfis_prontos=pf)
                i30 = np.searchsorted(d, 30000) - 1
                linhas.append([nome, f"{p[0]:.5f}", f"{p[1]:.5f}", f"{chao:.1f}", t, mata,
                               *(f"{x:.2f}" for x in (r[0.5][:, i30].mean(), r[1.4][:, i30].mean(), r[0.5][:, -1].mean(),
                                                      r[1.4][:, -1].mean(), r[0.5][oeste, i30].mean(), r[1.4][oeste, i30].mean(),
                                                      r[0.5][norte, i30].mean(), r[1.4][norte, i30].mean()))])
                if t == 25 and mata == 15:
                    fig_res[nome] = (d, r, chao)
        print(nome, f"chão {chao:.1f} m", flush=True)
    with open(SAIDA / "sensibilidade_colina.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(linhas)

    fig, eixos = plt.subplots(2, 4, figsize=(22, 11), subplot_kw={"projection": "polar"}, dpi=90)
    for col, (nome, (d, r, chao)) in enumerate(fig_res.items()):
        for lin, e in enumerate((0.5, 1.4)):
            ax = eixos[lin, col]
            T, Rr = np.meshgrid(np.radians(az), d / 1000, indexing="ij")
            m = ax.pcolormesh(T, Rr, r[e] * 100, cmap="magma_r", vmin=0, vmax=100, shading="auto")
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
            ax.set_rlim(0, 60); ax.set_rticks([20, 40, 60])
            ax.set_title(f"{nome}\nchão {chao:.0f} m, torre 25 m, elevação {e}°", fontsize=10)
    fig.colorbar(m, ax=eixos, shrink=0.6, label="Potência do feixe bloqueada (%)")
    fig.suptitle("Torre de 25 m em cada posição: MDT 1 m do SIGSC + 15 m de mata, até 60 km", fontsize=12)
    fig.savefig(FIG / "v2_pbb_colina.png", bbox_inches="tight"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
