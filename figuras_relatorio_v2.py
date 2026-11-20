# -*- coding: utf-8 -*-
"""Figuras da versão 2 do relatório de Araranguá: relevo do MDT de 1 m do SIGSC + mata.

Gera em relatorio/:
  figuras/v2_pbb_posicoes.png      bloqueio simulado (0,5° e 1,4°): atual, topo do Morro dos Conventos, Morro das Antenas
  figuras/v2_validacao_azimute.png simulado (MDT + mata) x falta de eco observada nos 7 volumes
  figuras/v2_mapa_mdt.png          MDT 1 m em volta do radar, posições, setores e a "janela" a oeste
  sensibilidade_v2.csv             torres de 15/25/35 m e mata de 10/15/20 m nas duas posições novas
Requer o acervo do SIGSC (relevo_sigsc.ACERVO), os tiles do SRTM em dem/ e dem/observado.pkl.
"""
import csv
import math
import pickle
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
ATUAL = PONTOS["radar (antena 49 m)"]
CONVENTOS = PONTOS["proposta (topo Conventos)"]
ANTENAS = PONTOS["Morro das Antenas"]
H_ANTENA_ATUAL = 3.0   # acima do chão do MDT (melhor ajuste aos volumes)
MATA = 15.0            # altura média da mata/casas sobre o terreno (melhor ajuste)
TORRE = 25.0           # torre nas posições novas (antena >= 5 m acima de mata de 20 m)


def pbb(rel, p, h_solo, mata, az=np.arange(0, 360, 1.0), max_km=80, elev=(0.5, 1.4, 2.4)):
    chao = float(rel(*p))
    pf = perfis(*p, rel, az=az, max_km=max_km, obst_m=mata)
    az, d, out = simular(*p, chao + h_solo, rel, elevacoes=elev, perfis_prontos=pf)
    return az, d, out, chao


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    srtm = Relevo(*ATUAL, fino_km=4.0, largo_km=100)
    rel = RelevoSIGSC(srtm, posicoes=[ATUAL, CONVENTOS, ANTENAS], raio_fino_km=2.0)

    # Sensibilidade
    linhas = [["posicao", "lat", "lon", "chao_mdt_m", "antena_acima_do_chao_m", "mata_m",
               "pbb05_30km", "pbb14_30km", "pbb05_60km", "pbb14_60km", "pbb24_60km", "oeste_pbb05_30km", "oeste_pbb14_30km"]]
    a2 = np.arange(0, 360, 2.0); oeste = (a2 >= 240) & (a2 <= 340)
    casos = [("Atual", ATUAL, [H_ANTENA_ATUAL])] + [(n, p, [15, 25, 35]) for n, p in
                                                    (("Topo do Morro dos Conventos", CONVENTOS), ("Morro das Antenas", ANTENAS))]
    for nome, p, alturas in casos:
        for h in alturas:
            for mata in (10, 15, 20):
                az, d, r, chao = pbb(rel, p, h, mata, az=a2, max_km=60)
                i30, i60 = np.searchsorted(d, 30000) - 1, len(d) - 1
                linhas.append([nome, f"{p[0]:.5f}", f"{p[1]:.5f}", f"{chao:.1f}", h, mata,
                               *(f"{x:.2f}" for x in (r[0.5][:, i30].mean(), r[1.4][:, i30].mean(), r[0.5][:, i60].mean(),
                                                      r[1.4][:, i60].mean(), r[2.4][:, i60].mean(),
                                                      r[0.5][oeste, i30].mean(), r[1.4][oeste, i30].mean()))])
    with open(SAIDA / "sensibilidade_v2.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)

    # Figura: três posições
    res = {"Atual (antena 3 m acima do chão)": pbb(rel, ATUAL, H_ANTENA_ATUAL, MATA),
           f"Topo do Morro dos Conventos (torre {TORRE:.0f} m)": pbb(rel, CONVENTOS, TORRE, MATA),
           f"Morro das Antenas (torre {TORRE:.0f} m)": pbb(rel, ANTENAS, TORRE, MATA)}
    fig, eixos = plt.subplots(2, 3, figsize=(17, 11), subplot_kw={"projection": "polar"}, dpi=95)
    for col, (nome, (az, d, r, chao)) in enumerate(res.items()):
        for lin, e in enumerate((0.5, 1.4)):
            ax = eixos[lin, col]; sel = d <= 60000
            T, Rr = np.meshgrid(np.radians(az), d[sel] / 1000, indexing="ij")
            m = ax.pcolormesh(T, Rr, r[e][:, sel] * 100, cmap="magma_r", vmin=0, vmax=100, shading="auto")
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
            ax.set_rlim(0, 60); ax.set_rticks([20, 40, 60]); ax.set_title(f"{nome}\nelevação {e}°", fontsize=10)
    fig.colorbar(m, ax=eixos, shrink=0.6, label="Potência do feixe bloqueada (%)")
    fig.suptitle(f"Bloqueio simulado: MDT 1 m do SIGSC + {MATA:.0f} m de mata e casas, até 60 km", fontsize=12)
    fig.savefig(FIG / "v2_pbb_posicoes.png", bbox_inches="tight"); plt.close(fig)

    # Figura: validação
    obs = pickle.load(open(AQUI / "dem" / "observado.pkl", "rb"))
    az, d, r, _ = res["Atual (antena 3 m acima do chão)"]
    i40 = np.searchsorted(d, 40000) - 1
    fig, eixos = plt.subplots(3, 1, figsize=(12, 9), sharex=True, dpi=100)
    for ax, e in zip(eixos, (0.5, 1.4, 2.4)):
        x = obs[e]
        env = np.array([np.percentile(np.r_[x[-15:], x, x[:15]][i:i + 31], 80) for i in range(360)])
        falta = np.where(env >= 0.03, 1 - np.clip(x / np.maximum(env, 1e-3), 0, 1), np.nan)
        ax.bar(np.arange(360), falta * 100, width=1, color="#6baed6", label="falta de eco observada (7 volumes)")
        ax.plot(az, r[e][:, i40] * 100, color="#d62728", lw=1.2, label="bloqueio simulado a 40 km (MDT + mata)")
        for a, txt in ((146.8, "farol"), (269.5, "janela"), (322.7, "colina"), (354.9, "vila")):
            ax.axvline(a, color="k", lw=0.6, ls="--"); ax.text(a + 1, 92, txt, fontsize=8)
        ax.set_ylim(0, 100); ax.set_ylabel(f"{e}° (%)")
    eixos[0].legend(loc="upper left", fontsize=8, ncol=2)
    eixos[-1].set_xlabel("Azimute (°)"); eixos[-1].set_xticks(range(0, 361, 30))
    fig.suptitle("Posição atual: bloqueio simulado (MDT + 15 m de mata) x falta de eco observada (5–40 km)")
    fig.tight_layout(); fig.savefig(FIG / "v2_validacao_azimute.png"); plt.close(fig)

    # Figura: mapa do MDT
    lat = np.linspace(ATUAL[0] - 0.012, ATUAL[0] + 0.014, 520)
    lon = np.linspace(ATUAL[1] - 0.02, ATUAL[1] + 0.008, 560)
    LO, LA = np.meshgrid(lon, lat)
    Z = rel(LA, LO)
    fig, ax = plt.subplots(figsize=(10, 9), dpi=100)
    m = ax.pcolormesh(LO, LA, Z, cmap="terrain", vmin=-5, vmax=80, shading="auto")
    ax.contour(LO, LA, Z, levels=[10, 30, 50, 60, 65], colors="k", linewidths=0.4)
    for p, txt, cor in ((ATUAL, "Radar atual", "red"), (CONVENTOS, "Topo do morro", "blue"),
                        (PONTOS["farol (topo 57 m)"], "Farol", "orange"), (PONTOS["colina (57 m)"], "Colina", "purple"),
                        (PONTOS["vila (~10 m)"], "Vila", "brown")):
        dy = -0.0012 if txt == "Farol" else 0.0005
        ax.plot(p[1], p[0], "o", color=cor, ms=8, mec="k"); ax.text(p[1] + 0.0006, p[0] + dy, txt, fontsize=9, weight="bold")
    c = 1 / math.cos(math.radians(ATUAL[0]))
    for a0, a1, cor, rotulo in ((321, 324, "red", "321–324°"), (352, 356, "orange", "352–356°"), (268, 271, "cyan", "janela 268–271°")):
        for a in (a0, a1):
            ax.plot([ATUAL[1], ATUAL[1] + 0.03 * math.sin(math.radians(a)) * c], [ATUAL[0], ATUAL[0] + 0.03 * math.cos(math.radians(a))],
                    color=cor, lw=0.9)
    ax.set_xlim(lon[0], lon[-1]); ax.set_ylim(lat[0], lat[-1]); ax.set_aspect(c)
    fig.colorbar(m, ax=ax, shrink=0.7, label="Altitude do terreno, MDT SIGSC 1 m (m)")
    ax.set_title("Morro dos Conventos no MDT de 1 m (sem mata nem prédios)")
    fig.savefig(FIG / "v2_mapa_mdt.png", bbox_inches="tight"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
