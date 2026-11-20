# -*- coding: utf-8 -*-
"""Sensibilidade do bloqueio à refração: raio efetivo k·R com k = 1 (sem refração), 4/3 (padrão),
2 e 4 (super-refração, comum na costa com ar frio e úmido sobre o mar). k → ∞ é o limite do duto.

Mesma configuração da versão 2 do relatório (MDT 1 m do SIGSC + 15 m de mata; antena atual 3 m acima do chão,
torres de 25 m nas posições novas).

Gera:
  relatorio/sensibilidade_refracao.csv
  relatorio/figuras/v2_refracao.png   bloqueio a 40 km por azimute (posição atual) para cada k, x observado
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
MATA = 15.0
KS = {"1 (sem refração)": 1.0, "4/3 (padrão)": 4 / 3, "2 (super-refração)": 2.0, "4 (super-refração forte)": 4.0}
ELEV = (0.5, 1.4, 2.4)


def falta_observada(x):
    env = np.array([np.percentile(np.r_[x[-15:], x, x[:15]][i:i + 31], 80) for i in range(360)])
    return np.where(env >= 0.03, 1 - np.clip(x / np.maximum(env, 1e-3), 0, 1), np.nan)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    srtm = Relevo(*ATUAL, fino_km=4.0, largo_km=100)
    rel = RelevoSIGSC(srtm, posicoes=[ATUAL, CONVENTOS, ANTENAS], raio_fino_km=2.0)
    obs = pickle.load(open(AQUI / "dem" / "observado.pkl", "rb"))

    az = np.arange(0, 360, 1.0)
    oeste = (az >= 240) & (az <= 340)
    serra = (az >= 268) & (az <= 271)
    casos = (("Atual", ATUAL, 3.0), ("Topo do Morro dos Conventos", CONVENTOS, 25.0), ("Morro das Antenas", ANTENAS, 25.0))
    linhas = [["posicao", "k", "elev", "altura_feixe_50km_acima_antena_m", "pbb_30km", "pbb_60km", "oeste_pbb_30km",
               "pbb_janela_268_271_a_58km", "corr_observado_40km"]]
    curvas = {}
    for nome, p, h in casos:
        chao = float(rel(*p))
        pf = perfis(*p, rel, az=az, max_km=60, obst_m=MATA)
        for rot, k in KS.items():
            _, d, r = simular(*p, chao + h, rel, elevacoes=ELEV, perfis_prontos=pf, k=k)
            i30, i40, i58 = (np.searchsorted(d, x) - 1 for x in (30000, 40000, 58000))
            for e in ELEV:
                re_ = k * 6371e3
                h50 = math.sqrt(50e3 ** 2 + re_ ** 2 + 2 * 50e3 * re_ * math.sin(math.radians(e))) - re_
                corr = ""
                if nome == "Atual":
                    f = falta_observada(obs[e]); ok = ~np.isnan(f)
                    corr = f"{np.corrcoef(f[ok], r[e][ok, i40])[0, 1]:.2f}"
                    curvas[(rot, e)] = r[e][:, i40]
                linhas.append([nome, rot, e, f"{h50:.0f}", f"{r[e][:, i30].mean():.2f}", f"{r[e][:, -1].mean():.2f}",
                               f"{r[e][oeste, i30].mean():.2f}", f"{r[e][serra, i58].mean():.2f}", corr])
        print(nome, "ok", flush=True)
    with open(SAIDA / "sensibilidade_refracao.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(linhas)

    fig, eixos = plt.subplots(3, 1, figsize=(12, 9), sharex=True, dpi=100)
    cores = dict(zip(KS, ("#1f77b4", "#d62728", "#ff7f0e", "#7f3c8d")))
    for ax, e in zip(eixos, ELEV):
        ax.bar(az, falta_observada(obs[e]) * 100, width=1, color="#c6dbef", label="falta de eco observada")
        for rot in KS:
            ax.plot(az, curvas[(rot, e)] * 100, color=cores[rot], lw=1.1, label=f"k = {rot}")
        ax.set_ylim(0, 100); ax.set_ylabel(f"{e}° (%)")
    eixos[0].legend(loc="upper left", fontsize=8, ncol=3)
    eixos[-1].set_xlabel("Azimute (°)"); eixos[-1].set_xticks(range(0, 361, 30))
    fig.suptitle("Posição atual: bloqueio simulado a 40 km para cada raio efetivo k·R (MDT + 15 m de mata)")
    fig.tight_layout(); fig.savefig(FIG / "v2_refracao.png"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
