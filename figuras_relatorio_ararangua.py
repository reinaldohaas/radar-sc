# -*- coding: utf-8 -*-
"""Figuras e tabelas do relatório de bloqueio do radar de Araranguá (relatorio/).

Gera:
  relatorio/figuras/pbb_atual_x_proposta.png   bloqueio simulado (0,5° e 1,4°) por azimute e distância
  relatorio/figuras/validacao_azimute.png      simulado x falta de eco observada nos 7 volumes
  relatorio/figuras/mapa_posicoes.png          relevo do Morro dos Conventos, posição atual e proposta
  relatorio/sensibilidade.csv                  PBB para árvores de +10 e +20 m e torres de 10/20/30 m
Requer dem/observado.pkl (feito pela validação) e os tiles em dem/.
"""
import csv
import math
import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from relevo import Relevo
from simular_bloqueio import perfis, simular

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "relatorio"
FIG = SAIDA / "figuras"
ATUAL = (-28.934548, -49.362490)
H_ATUAL = 67.0                      # antena atual, referencial do SRTM
PROPOSTA = (-28.93725, -49.36762)   # topo do morro, 0,58 km a 239° da atual
OUTRAS = {"Morro, 0,50 km a 307°": (-28.93185, -49.36660), "Região, 14 km a 32°": (-28.82657, -49.28551)}
FAROL = (-28.934662, -49.362405)
COLINA = (-28.925236, -49.370698)


def pbb_de(rel, ponto, h, obst, az=np.arange(0, 360, 1.0), elev=(0.5, 1.4, 2.4), max_km=80):
    pf = perfis(*ponto, rel, az=az, max_km=max_km, obst_m=obst)
    return simular(*ponto, h, rel, elevacoes=elev, perfis_prontos=pf)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    rel = Relevo(*ATUAL, fino_km=4.0, largo_km=100)
    t_prop = float(rel(*PROPOSTA, 0))

    # Sensibilidade
    linhas = [["posicao", "lat", "lon", "terreno_srtm_m", "torre_m", "arvores_m", "pbb05_60km", "pbb14_60km", "pbb24_60km",
               "azimutes_limpos_05"]]
    casos = [("Atual", ATUAL, None)] + [("Proposta (topo do morro)", PROPOSTA, None)] + [(n, p, None) for n, p in OUTRAS.items()]
    for nome, p, _ in casos:
        ter = float(rel(*p, 0))
        torres = [None] if nome == "Atual" else [10, 20, 30]
        for t in torres:
            h = H_ATUAL if t is None else ter + t
            for obst in (10, 20):
                az, d, pbb = pbb_de(rel, p, h, obst, az=np.arange(0, 360, 2.0), max_km=60)
                i = len(d) - 1
                linhas.append([nome, f"{p[0]:.5f}", f"{p[1]:.5f}", f"{ter:.0f}", "atual" if t is None else t, obst,
                               f"{pbb[0.5][:, i].mean():.2f}", f"{pbb[1.4][:, i].mean():.2f}", f"{pbb[2.4][:, i].mean():.2f}",
                               f"{np.mean(pbb[0.5][:, i] < 0.1):.2f}"])
    with open(SAIDA / "sensibilidade.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)

    # Figura 1: PBB atual x proposta (torre de 15 m), árvores +10 m
    resultados = {"Atual (antena 67 m SRTM)": pbb_de(rel, ATUAL, H_ATUAL, 10),
                  f"Proposta (torre de 15 m, antena {t_prop + 15:.0f} m)": pbb_de(rel, PROPOSTA, t_prop + 15, 10)}
    fig, eixos = plt.subplots(2, 2, figsize=(12, 11), subplot_kw={"projection": "polar"}, dpi=100)
    for col, (nome, (az, d, pbb)) in enumerate(resultados.items()):
        for lin, e in enumerate((0.5, 1.4)):
            ax = eixos[lin, col]
            sel = d <= 60000
            T, Rr = np.meshgrid(np.radians(az), d[sel] / 1000, indexing="ij")
            m = ax.pcolormesh(T, Rr, pbb[e][:, sel] * 100, cmap="magma_r", vmin=0, vmax=100, shading="auto")
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
            ax.set_rlim(0, 60); ax.set_rticks([20, 40, 60]); ax.set_title(f"{nome}\nelevação {e}°", fontsize=10)
    fig.colorbar(m, ax=eixos, shrink=0.6, label="Potência do feixe bloqueada (%)")
    fig.suptitle("Bloqueio simulado pelo relevo (SRTM + 10 m de árvores e casas), até 60 km", fontsize=12)
    fig.savefig(FIG / "pbb_atual_x_proposta.png", bbox_inches="tight")
    plt.close(fig)

    # Figura 2: validação por azimute
    obs = pickle.load(open(AQUI / "dem" / "observado.pkl", "rb"))
    az, d, pbb = pbb_de(rel, ATUAL, H_ATUAL, 10)
    i40 = np.searchsorted(d, 40000) - 1
    fig, eixos = plt.subplots(3, 1, figsize=(12, 9), sharex=True, dpi=100)
    for ax, e in zip(eixos, (0.5, 1.4, 2.4)):
        x = obs[e]
        env = np.array([np.percentile(np.r_[x[-15:], x, x[:15]][i:i + 31], 80) for i in range(360)])
        falta = np.where(env >= 0.03, 1 - np.clip(x / np.maximum(env, 1e-3), 0, 1), np.nan)
        ax.bar(np.arange(360), falta * 100, width=1, color="#6baed6", label="falta de eco observada (7 volumes)")
        ax.plot(az, pbb[e][:, i40] * 100, color="#d62728", lw=1.2, label="bloqueio simulado a 40 km")
        for a, txt in ((146.8, "farol"), (322.7, "colina"), (354.9, "vila")):
            ax.axvline(a, color="k", lw=0.6, ls="--"); ax.text(a + 1, 92, txt, fontsize=8)
        ax.set_ylim(0, 100); ax.set_ylabel(f"{e}° (%)")
    eixos[0].legend(loc="upper left", fontsize=8, ncol=2)
    eixos[-1].set_xlabel("Azimute (°)"); eixos[-1].set_xticks(range(0, 361, 30))
    fig.suptitle("Posição atual: bloqueio simulado x falta de eco observada (5–40 km)")
    fig.tight_layout()
    fig.savefig(FIG / "validacao_azimute.png")
    plt.close(fig)

    # Figura 3: mapa do relevo fino
    lat = np.linspace(ATUAL[0] - 0.025, ATUAL[0] + 0.02, 400)
    lon = np.linspace(ATUAL[1] - 0.03, ATUAL[1] + 0.02, 450)
    LO, LA = np.meshgrid(lon, lat)
    Z = rel.fino(LA, LO)
    fig, ax = plt.subplots(figsize=(10, 9), dpi=100)
    m = ax.pcolormesh(LO, LA, Z, cmap="terrain", vmin=-5, vmax=90, shading="auto")
    ax.contour(LO, LA, Z, levels=[20, 40, 60, 70, 80], colors="k", linewidths=0.4)
    for p, txt, cor in ((ATUAL, "Radar atual", "red"), (PROPOSTA, "Proposta", "blue"), (FAROL, "Farol", "orange"),
                        (COLINA, "Colina 57 m", "purple"), (OUTRAS["Morro, 0,50 km a 307°"], "Alternativa", "cyan")):
        dy = -0.0018 if txt == "Farol" else 0.0006
        ax.plot(p[1], p[0], "o", color=cor, ms=8, mec="k"); ax.text(p[1] + 0.0008, p[0] + dy, txt, fontsize=9, weight="bold")
    for a0, a1, cor in ((321, 324, "red"), (352, 356, "orange")):
        for a in (a0, a1):
            ax.plot([ATUAL[1], ATUAL[1] + 0.03 * math.sin(math.radians(a)) / math.cos(math.radians(ATUAL[0]))],
                    [ATUAL[0], ATUAL[0] + 0.03 * math.cos(math.radians(a))], color=cor, lw=0.8)
    ax.set_xlim(lon[0], lon[-1]); ax.set_ylim(lat[0], lat[-1]); ax.set_aspect(1 / math.cos(math.radians(ATUAL[0])))
    fig.colorbar(m, ax=ax, shrink=0.7, label="Altitude SRTM (m; inclui parte da copa)")
    ax.set_title("Morro dos Conventos: relevo (SRTM 30 m interpolado) e posições do radar")
    fig.savefig(FIG / "mapa_posicoes.png", bbox_inches="tight")
    plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
