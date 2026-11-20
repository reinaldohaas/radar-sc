# -*- coding: utf-8 -*-
"""Versão 3 do estudo de Araranguá: bloqueio com o MDS de 1 m do SIGSC (terreno + mata + prédios, 2010–2012).

Superfície usada na simulação:
  - dentro das folhas do MDS (SH-22-X-B-IV-3 e B-IV-1): o próprio MDS, com filtro mediano 3x3 contra picos isolados,
    mais `crescimento` metros onde há vegetação ou construção (MDS − MDT > 2 m), para testar a mata que cresceu desde 2012;
  - fora delas: MDT + 15 m de mata em terra firme (como na versão 2); fora do MDT, SRTM + 15 m.

Gera em relatorio/:
  figuras/v3_altura_superficie_bruta.png  MDS − MDT sem correção das falésias (a versão corrigida é de mapa_altura_superficie.py)
  figuras/v3_validacao_azimute.png  simulado (MDS) x falta de eco observada
  figuras/v3_pbb_posicoes.png       torre de 25 m: atual, colina, Conventos, Morro das Antenas
  mds_calibracao.csv                altura da antena atual e crescimento da mata x observado
  mds_setores.csv                   o que bloqueia cada setor problemático (distância, altura do objeto)
  mds_posicoes.csv                  torres de 15/25/35 m nas quatro posições
  mds_cidade.csv                    prédios de Araranguá no caminho do feixe
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
from relevo_sigsc import ACERVO_MDS, PADRAO_MDS, PONTOS, RelevoSIGSC
from simular_bloqueio import destino, perfis, simular

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "relatorio"
FIG = SAIDA / "figuras"
ATUAL = PONTOS["radar (antena 49 m)"]
POS = {"Atual": ATUAL, "Topo da colina a NW": PONTOS["colina (57 m)"],
       "Topo do Morro dos Conventos": PONTOS["proposta (topo Conventos)"], "Morro das Antenas": PONTOS["Morro das Antenas"]}
MATA_FORA = 15.0


class Nada:
    def __call__(self, lat, lon, d=None):
        return np.full(np.shape(lat), np.nan)


class Superficie:
    def __init__(self, mds, mdt, crescimento=0.0):
        self.mds, self.mdt, self.cresc = mds, mdt, crescimento

    def __call__(self, lat, lon, d=None):
        zt = self.mdt(lat, lon, d)
        zs = self.mds(lat, lon)
        fora = np.where(zt > 1, zt + MATA_FORA, zt)
        dentro = zs + np.where(zs - zt > 2, self.cresc, 0.0)
        return np.where(np.isnan(zs), fora, dentro)


def falta_observada(x):
    env = np.array([np.percentile(np.r_[x[-15:], x, x[:15]][i:i + 31], 80) for i in range(360)])
    return np.where(env >= 0.03, 1 - np.clip(x / np.maximum(env, 1e-3), 0, 1), np.nan)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    srtm = Relevo(*ATUAL, fino_km=4.0, largo_km=100)
    mdt = RelevoSIGSC(srtm, posicoes=list(POS.values()), raio_fino_km=2.0)
    mds = RelevoSIGSC(Nada(), posicoes=list(POS.values()), raio_fino_km=2.0, padrao=PADRAO_MDS, acervo=ACERVO_MDS,
                      mediana=True)
    print("mosaicos prontos", flush=True)
    obs = pickle.load(open(AQUI / "dem" / "observado.pkl", "rb"))
    falta = {e: falta_observada(obs[e]) for e in (0.5, 1.4, 2.4)}
    chao = {n: float(mdt(*p)) for n, p in POS.items()}
    az = np.arange(0, 360, 1.0)
    oeste = (az >= 240) & (az <= 340)

    # 1. Calibração: altura da antena atual e crescimento da mata desde 2012
    lin = [["antena_acima_do_chao_m", "crescimento_mata_m", "d_min_m", "oeste_pbb05_30km", "oeste_pbb14_30km",
            "oeste_pbb24_30km", "corr05", "corr14", "corr24"]]
    melhor = None
    for cresc in (0.0, 3.0, 6.0):
        sup = Superficie(mds, mdt, cresc)
        for dmin in (100.0, 50.0):
            pf = perfis(*ATUAL, sup, az=az, max_km=40, d_min=dmin)
            for h in (3.0, 6.0, 10.0, 15.0):
                _, d, r = simular(*ATUAL, chao["Atual"] + h, sup, perfis_prontos=pf)
                i30, i40 = np.searchsorted(d, 30000) - 1, len(d) - 1
                cs = []
                for e in (0.5, 1.4, 2.4):
                    ok = ~np.isnan(falta[e])
                    cs.append(np.corrcoef(falta[e][ok], r[e][ok, i40])[0, 1])
                lin.append([h, cresc, dmin, *(f"{r[e][oeste, i30].mean():.2f}" for e in (0.5, 1.4, 2.4)), *(f"{c:.2f}" for c in cs)])
                if melhor is None or np.nanmean(cs) > melhor[0]:
                    melhor = (np.nanmean(cs), h, cresc, dmin)
        print("crescimento", cresc, "ok", flush=True)
    with open(SAIDA / "mds_calibracao.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(lin)
    _, H, CRESC, DMIN = melhor
    print(f"melhor ajuste: antena {H} m acima do chão, crescimento {CRESC} m, d_min {DMIN} m (corr média {melhor[0]:.2f})")
    sup = Superficie(mds, mdt, CRESC)

    # 2. Validação com o melhor ajuste
    pf = perfis(*ATUAL, sup, az=az, max_km=60, d_min=DMIN)
    _, d, r_atual = simular(*ATUAL, chao["Atual"] + H, sup, perfis_prontos=pf)
    i40 = np.searchsorted(d, 40000) - 1
    fig, eixos = plt.subplots(3, 1, figsize=(12, 9), sharex=True, dpi=100)
    for ax, e in zip(eixos, (0.5, 1.4, 2.4)):
        ax.bar(az, falta[e] * 100, width=1, color="#6baed6", label="falta de eco observada (7 volumes)")
        ax.plot(az, r_atual[e][:, i40] * 100, color="#d62728", lw=1.2, label="bloqueio simulado a 40 km (MDS)")
        for a, txt in ((146.8, "farol"), (269.5, "janela"), (322.7, "colina"), (354.9, "vila")):
            ax.axvline(a, color="k", lw=0.6, ls="--"); ax.text(a + 1, 92, txt, fontsize=8)
        ax.set_ylim(0, 100); ax.set_ylabel(f"{e}° (%)")
    eixos[0].legend(loc="upper left", fontsize=8, ncol=2)
    eixos[-1].set_xlabel("Azimute (°)"); eixos[-1].set_xticks(range(0, 361, 30))
    fig.suptitle(f"Posição atual com o MDS do SIGSC: antena {H:.0f} m acima do chão, mata +{CRESC:.0f} m desde 2012")
    fig.tight_layout(); fig.savefig(FIG / "v3_validacao_azimute.png"); plt.close(fig)

    # 3. Setores: onde o feixe é bloqueado e por quê (passo de 0,25°)
    lin = [["setor", "azimute", "elev", "pbb_40km", "dist_bloqueio_50pct_m", "altura_objeto_acima_do_terreno_m",
            "altitude_superficie_m", "lat", "lon"]]
    for nome, a0, a1 in (("janela", 266, 273), ("colina", 319, 326), ("vila", 350, 358), ("vizinho_N", 0, 5)):
        azs = np.arange(a0, a1 + 0.01, 0.25)
        _, dd, zz = perfis(*ATUAL, sup, az=azs, max_km=40, d_min=DMIN)
        _, _, rr = simular(*ATUAL, chao["Atual"] + H, sup, perfis_prontos=(azs, dd, zz))
        for e in (0.5, 1.4):
            for k, a in enumerate(azs):
                j = np.argmax(rr[e][k] >= 0.5) if (rr[e][k] >= 0.5).any() else None
                if j is None:
                    lin.append([nome, a, e, f"{rr[e][k, -1]:.2f}", "", "", "", "", ""]); continue
                la, lo = destino(*ATUAL, a, dd[j])
                ht = float(zz[k, j] - mdt(la, lo))
                lin.append([nome, a, e, f"{rr[e][k, -1]:.2f}", f"{dd[j]:.0f}", f"{ht:.1f}", f"{zz[k, j]:.1f}", f"{la:.6f}", f"{lo:.6f}"])
    with open(SAIDA / "mds_setores.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(lin)

    # 4. Prédios de Araranguá: superfície − terreno ao longo dos raios 255–285°, 9–15 km
    azs = np.arange(255, 285.01, 0.25)
    dd = np.arange(9000, 15001, 5.0)
    A, D = np.meshgrid(azs, dd, indexing="ij")
    la, lo = destino(*ATUAL, A, D)
    zs, zt = mds(la, lo), mdt(la, lo, D / 1000)
    alt = zs - zt
    lin = [["azimute", "predio_mais_alto_m", "dist_m", "altitude_topo_m", "lat", "lon", "pbb05_15km_atual", "pbb14_15km_atual"]]
    _, d15, r15 = simular(*ATUAL, chao["Atual"] + H, sup, az=azs, max_km=15.5)
    i15 = np.searchsorted(d15, 15000) - 1
    for k, a in enumerate(azs):
        j = int(np.nanargmax(alt[k]))
        lin.append([a, f"{alt[k, j]:.1f}", f"{dd[j]:.0f}", f"{zs[k, j]:.1f}", f"{la[k, j]:.6f}", f"{lo[k, j]:.6f}",
                    f"{r15[0.5][k, i15]:.2f}", f"{r15[1.4][k, i15]:.2f}"])
    with open(SAIDA / "mds_cidade.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(lin)
    print("cidade ok", flush=True)

    # 5. Posições com torre
    lin = [["posicao", "chao_mdt_m", "superficie_mds_no_local_m", "torre_m", "pbb05_30km", "pbb14_30km", "pbb05_60km",
            "pbb14_60km", "oeste_pbb05_30km", "oeste_pbb14_30km"]]
    figres = {}
    for nome, p in POS.items():
        pf = perfis(*p, sup, az=az, max_km=60, d_min=DMIN)
        for t in (15.0, 25.0, 35.0):
            _, d, r = simular(*p, chao[nome] + t, sup, perfis_prontos=pf)
            i30 = np.searchsorted(d, 30000) - 1
            lin.append([nome, f"{chao[nome]:.1f}", f"{float(mds(*p)):.1f}", t,
                        *(f"{x:.2f}" for x in (r[0.5][:, i30].mean(), r[1.4][:, i30].mean(), r[0.5][:, -1].mean(),
                                               r[1.4][:, -1].mean(), r[0.5][oeste, i30].mean(), r[1.4][oeste, i30].mean()))])
            if t == 25.0:
                figres[nome] = (d, r)
        print(nome, "ok", flush=True)
    lin.append(["Atual (antena como está)", f"{chao['Atual']:.1f}", f"{float(mds(*ATUAL)):.1f}", H,
                *(f"{x:.2f}" for x in (r_atual[0.5][:, np.searchsorted(d, 30000) - 1].mean(),
                                       r_atual[1.4][:, np.searchsorted(d, 30000) - 1].mean(),
                                       r_atual[0.5][:, -1].mean(), r_atual[1.4][:, -1].mean(),
                                       r_atual[0.5][oeste, np.searchsorted(d, 30000) - 1].mean(),
                                       r_atual[1.4][oeste, np.searchsorted(d, 30000) - 1].mean()))])
    with open(SAIDA / "mds_posicoes.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(lin)

    fig, eixos = plt.subplots(2, 4, figsize=(22, 11), subplot_kw={"projection": "polar"}, dpi=90)
    for col, (nome, (d, r)) in enumerate(figres.items()):
        for row, e in enumerate((0.5, 1.4)):
            ax = eixos[row, col]
            T, Rr = np.meshgrid(np.radians(az), d / 1000, indexing="ij")
            m = ax.pcolormesh(T, Rr, r[e] * 100, cmap="magma_r", vmin=0, vmax=100, shading="auto")
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1); ax.set_rlim(0, 60); ax.set_rticks([20, 40, 60])
            ax.set_title(f"{nome}\nlat {POS[nome][0]:.5f}, lon {POS[nome][1]:.5f}\ntorre 25 m, elevação {e}°", fontsize=10)
    fig.colorbar(m, ax=eixos, shrink=0.6, label="Potência do feixe bloqueada (%)")
    fig.suptitle(f"Torre de 25 m em cada posição: MDS 1 m do SIGSC (mata +{CRESC:.0f} m desde 2012), até 60 km", fontsize=12)
    fig.savefig(FIG / "v3_pbb_posicoes.png", bbox_inches="tight"); plt.close(fig)

    # 6. Mapa da altura da superfície (MDS − MDT)
    lat = np.linspace(ATUAL[0] - 0.012, ATUAL[0] + 0.014, 520)
    lon = np.linspace(ATUAL[1] - 0.02, ATUAL[1] + 0.008, 560)
    LO, LA = np.meshgrid(lon, lat)
    Hs = mds(LA, LO) - mdt(LA, LO)
    fig, ax = plt.subplots(figsize=(10, 9), dpi=100)
    m = ax.pcolormesh(LO, LA, np.clip(Hs, 0, None), cmap="YlGn", vmin=0, vmax=30, shading="auto")
    ax.contour(LO, LA, mdt(LA, LO), levels=[10, 30, 50, 65], colors="k", linewidths=0.4)
    for p, txt, cor in ((ATUAL, "Radar atual", "red"), (POS["Topo do Morro dos Conventos"], "Topo do morro", "blue"),
                        (POS["Topo da colina a NW"], "Colina", "purple"), (PONTOS["vila (~10 m)"], "Vila", "brown")):
        ax.plot(p[1], p[0], "o", color=cor, ms=8, mec="k"); ax.text(p[1] + 0.0006, p[0] + 0.0005, txt, fontsize=9, weight="bold")
    c = 1 / math.cos(math.radians(ATUAL[0]))
    for a0, a1, cor in ((321, 324, "red"), (352, 356, "orange"), (268, 271, "cyan")):
        for a in (a0, a1):
            ax.plot([ATUAL[1], ATUAL[1] + 0.03 * math.sin(math.radians(a)) * c], [ATUAL[0], ATUAL[0] + 0.03 * math.cos(math.radians(a))],
                    color=cor, lw=0.9)
    ax.set_xlim(lon[0], lon[-1]); ax.set_ylim(lat[0], lat[-1]); ax.set_aspect(c)
    fig.colorbar(m, ax=ax, shrink=0.7, label="MDS − MDT: altura da mata e das construções (m, 2010–2012)")
    ax.set_title("Morro dos Conventos: altura da superfície acima do terreno (SIGSC 1 m)")
    fig.savefig(FIG / "v3_altura_superficie_bruta.png", bbox_inches="tight"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
