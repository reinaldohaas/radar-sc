# -*- coding: utf-8 -*-
"""Posições do radar, dos obstáculos e das duas posições propostas; teste do bloqueio em cada posição; mapa 3D.

Gera:
  relatorio/posicoes_obstaculos.csv           lat/lon, altitude (MDT e MDS do SIGSC), distância e azimute a partir da antena
  dem/pbb_posicoes_mds.npz                    bloqueio por azimute (0,5° e 1,4°, a 10, 30 e 60 km) nas três posições
  relatorio/figuras/v3_mapa3d_posicoes_simples.png  vista 3D simples (a principal é de figuras_posicoes_latlon.py)
Bloqueio: MDS de 1 m do SIGSC + 6 m de mata desde 2012 (melhor ajuste da seção 4.1), Terra 4/3, feixe de 2,2°.
"""
import csv
import math
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, colors
from pyproj import Geod, Transformer

from relevo_sigsc import ACERVO_MDS, PADRAO, PADRAO_MDS, PONTOS, Mosaico, folhas
from simular_bloqueio import destino

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
G = Geod(ellps="WGS84")

POSICOES = {   # nome: (lat, lon, antena acima do chão)
    "Atual (reboque, antena ~3 m)": (-28.934548, -49.362490, 3.0),
    "Proposta 1: topo do Morro dos Conventos (torre 25 m)": (-28.93725, -49.36762, 25.0),
    "Proposta 2: Morro das Antenas (torre 25 m)": (-28.843869, -49.398756, 25.0),
}
OBSTACULOS = [  # nome, lat, lon, altura do objeto acima do chão (m, estimada), observação
    ("Farol do Morro dos Conventos", -28.934662, -49.362405, 15, "a 15 m da antena; bloqueia ~141–153° em todas as elevações"),
    ("Poste e fios da rede elétrica", None, None, None, "ao lado do radome (foto); posição a medir"),
    ("Crista com mata (setor 321–324°)", *destino(-28.934548, -49.362490, 322.0, 700.0), 15, "mata de 10–17 m a 640–750 m"),
    ("Colina a NW, com mata", -28.925236, -49.370698, 15, "topo 67 m + mata de 8–15 m"),
    ("Vila (setor 352–356°)", -28.922000, -49.363759, 12, "casas e árvores até ~12 m; abaixo do feixe"),
    ("Mata do topo do Morro dos Conventos", -28.93725, -49.36762, 10, "500–700 m a SW e W da antena"),
    ("Morro com mata a W (266–268°)", -28.939924, -49.471553, 15, "topo ~82 m a 10,6 km; tapa ~20–30% do feixe de 0,5°"),
    ("Prédio mais alto, Araranguá (271°)", -28.932546, -49.489633, 38, "topo a 41 m, a 12,4 km"),
    ("Prédio mais alto, Araranguá (284°)", -28.912340, -49.464070, 40, "topo a 44 m, a 10,2 km"),
    ("Torres existentes do Morro das Antenas", -28.843869, -49.398756, 13, "estruturas de até ~13 m num raio de 40 m"),
]


def bloqueio():
    cache = AQUI / "dem" / "pbb_posicoes_mds.npz"
    if cache.exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    from analise_mds import Nada, Superficie
    from relevo import Relevo
    from relevo_sigsc import RelevoSIGSC
    from simular_bloqueio import perfis, simular
    pos = [(la, lo) for la, lo, _ in POSICOES.values()]
    srtm = Relevo(*pos[0], fino_km=4.0, largo_km=100)
    mdt = RelevoSIGSC(srtm, posicoes=pos, raio_fino_km=2.0)
    mds = RelevoSIGSC(Nada(), posicoes=pos, raio_fino_km=2.0, padrao=PADRAO_MDS, acervo=ACERVO_MDS, mediana=True)
    sup = Superficie(mds, mdt, 6.0)
    az = np.arange(0, 360, 1.0)
    out = {"az": az}
    for k, (la, lo, h) in enumerate(POSICOES.values()):
        chao = float(mdt(la, lo))
        pf = perfis(la, lo, sup, az=az, max_km=60)
        _, d, r = simular(la, lo, chao + h, sup, elevacoes=(0.5, 1.4), perfis_prontos=pf)
        for km in (10, 30, 60):
            i = np.searchsorted(d, km * 1000) - 1
            out[f"p{k}_05_{km}"], out[f"p{k}_14_{km}"] = r[0.5][:, i], r[1.4][:, i]
        out[f"p{k}_chao"] = np.array(chao)
        print(list(POSICOES)[k], "ok", flush=True)
    np.savez(cache, **out)
    return out


def tabela(mdt1, mds1):
    la0, lo0, _ = POSICOES["Atual (reboque, antena ~3 m)"]
    linhas = [["tipo", "nome", "lat", "lon", "chao_mdt_m", "superficie_mds_m", "altura_objeto_m", "dist_da_antena_m",
               "azimute_da_antena", "observacao"]]

    def alt(m, la, lo):
        try:
            v = float(m(la, lo))
            return "" if np.isnan(v) else f"{v:.1f}"
        except Exception:
            return ""
    for n, (la, lo, h) in POSICOES.items():
        az, _, d = G.inv(lo0, la0, lo, la)
        linhas.append(["radar", n, f"{la:.6f}", f"{lo:.6f}", alt(mdt1, la, lo), alt(mds1, la, lo), h,
                       f"{d:.0f}" if d > 1 else "", f"{az % 360:.0f}" if d > 1 else "", ""])
    for n, la, lo, h, obs in OBSTACULOS:
        if la is None:
            linhas.append(["obstáculo", n, "", "", "", "", "", "", "", obs]); continue
        az, _, d = G.inv(lo0, la0, lo, la)
        linhas.append(["obstáculo", n, f"{la:.6f}", f"{lo:.6f}", alt(mdt1, la, lo), alt(mds1, la, lo), h, f"{d:.0f}",
                       f"{az % 360:.0f}", obs])
    with open(AQUI / "relatorio" / "posicoes_obstaculos.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)
    return linhas


def main():
    pbb = bloqueio()
    t = Transformer.from_crs("EPSG:4326", "EPSG:31982", always_xy=True)
    lim = (651500.0, 6794500.0, 666500.0, 6813500.0)
    mdt5 = Mosaico(folhas(PADRAO), 5.0, lim)
    mds5 = Mosaico(folhas(PADRAO_MDS, ACERVO_MDS), 5.0, lim)
    linhas = tabela(mdt5, mds5)
    for l in linhas:
        print(" | ".join(map(str, l[:9])))

    figuras(pbb, t)
    print("ok")


def figuras(pbb, t):
    lim = (645500.0, 6794500.0, 666500.0, 6813500.0)
    mdt = Mosaico(folhas(PADRAO), 5.0, lim)
    mds = Mosaico(folhas(PADRAO_MDS, ACERVO_MDS), 5.0, lim)
    passo = 40.0
    E = np.arange(lim[0], lim[2], passo) + passo / 2
    N = np.arange(lim[3], lim[1], -passo) - passo / 2
    EE, NN = np.meshgrid(E, N)
    para_geo = Transformer.from_crs("EPSG:31982", "EPSG:4326", always_xy=True)
    LO, LA = para_geo.transform(EE, NN)
    Z = mds(LA, LO)
    Z = np.where(np.isnan(Z), mdt(LA, LO), Z)
    agua = ~np.isfinite(Z) | (np.nan_to_num(Z, nan=0) < 0.8)
    Z = np.nan_to_num(Z, nan=0.0)
    gy, gx = np.gradient(Z, passo)
    hs = np.clip(0.6 + 0.4 * (-gx - gy) / np.sqrt(1 + gx ** 2 + gy ** 2) * 3, 0, 1)
    rgb = cm.get_cmap("terrain")(colors.Normalize(-160, 330)(Z))[..., :3] * hs[..., None]
    rgb[agua] = (0.62, 0.78, 0.92)
    km = lambda x, y: ((x - lim[0]) / 1000, (y - lim[1]) / 1000)
    ext = (0, (lim[2] - lim[0]) / 1000, 0, (lim[3] - lim[1]) / 1000)
    nomes = list(POSICOES)
    obs = [(i + 1, n, la, lo) for i, (n, la, lo, h, _) in enumerate(OBSTACULOS) if la is not None]

    # 1) planta: um painel por posição, com o leque de raios de 0,5° colorido pelo bloqueio a 30 km
    fig, eixos = plt.subplots(1, 3, figsize=(21, 7.6), dpi=95)
    for k, nome in enumerate(nomes):
        ax = eixos[k]
        ax.imshow(rgb, extent=ext, origin="upper")
        la, lo, h = POSICOES[nome]
        x0, y0 = km(*t.transform(lo, la))
        f = pbb[f"p{k}_05_30"]
        for a, fa in zip(pbb["az"][::2], f[::2]):
            ax.plot([x0, x0 + 7 * math.sin(math.radians(a))], [y0, y0 + 7 * math.cos(math.radians(a))],
                    color=cm.get_cmap("RdYlGn_r")(float(fa)), lw=0.9, alpha=0.6)
        for j, outro in enumerate(nomes):
            ola, olo, _ = POSICOES[outro]
            ox, oy = km(*t.transform(olo, ola))
            ax.plot(ox, oy, "o", ms=9 if j == k else 7, mfc="red" if j == k else "white", mec="k", zorder=5)
            dx, dy = [(0.5, 0.4), (-2.2, -1.1), (0.5, 0.4)][j]
            ax.text(ox + dx, oy + dy, ["Atual", "P1", "P2"][j], fontsize=9, weight="bold", zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.7, pad=1))
        for n_, nm, ola, olo in obs:
            ox, oy = km(*t.transform(olo, ola))
            ax.plot(ox, oy, "^", ms=6, mfc="purple", mec="k", zorder=5)
            ax.text(ox - 0.9, oy - 0.9, str(n_), fontsize=8, color="purple", weight="bold", zorder=6)
        oeste = (pbb["az"] >= 240) & (pbb["az"] <= 340)
        ax.set_title(f"{nome}\nlat {la:.5f}, lon {lo:.5f}\n0,5° a 30 km: médio {f.mean():.0%}, oeste {f[oeste].mean():.0%}  |  "
                     f"1,4°: médio {pbb[f'p{k}_14_30'].mean():.0%}, oeste {pbb[f'p{k}_14_30'][oeste].mean():.0%}", fontsize=10)
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
        ax.set_xlabel("km (leste)")
    eixos[0].set_ylabel("km (norte)")
    sm = cm.ScalarMappable(cmap="RdYlGn_r", norm=colors.Normalize(0, 100))
    fig.colorbar(sm, ax=eixos, shrink=0.75, pad=0.01, label="Feixe de 0,5° bloqueado a 30 km (%)")
    leg = "  ".join(f"{n_} {nm} ({ola:.5f}, {olo:.5f})" for n_, nm, ola, olo in obs)
    fig.text(0.5, 0.005, "Obstáculos (▲): " + leg, ha="center", fontsize=8, wrap=True)
    fig.suptitle("Posições do radar e obstáculos sobre a superfície do SIGSC (MDS 1 m): raios de 7 km coloridos pelo "
                 "bloqueio simulado a 30 km", fontsize=12)
    fig.savefig(AQUI / "relatorio" / "figuras" / "v3_posicoes_planta.png", bbox_inches="tight"); plt.close(fig)

    # 2) vista 3D com hastes nas posições e nos obstáculos
    EXAG = 5
    fig = plt.figure(figsize=(14, 10), dpi=95)
    ax = fig.add_subplot(projection="3d")
    s_ = 2
    X, Y = np.meshgrid(np.linspace(ext[0], ext[1], Z.shape[1]), np.linspace(ext[3], ext[2], Z.shape[0]))
    ax.plot_surface(X[::s_, ::s_], Y[::s_, ::s_], Z[::s_, ::s_] * EXAG / 1000, facecolors=rgb[::s_, ::s_],
                    linewidth=0, antialiased=False, shade=False)
    topo = (np.nanmax(Z) + 120) * EXAG / 1000
    for j, outro in enumerate(nomes):
        la, lo, h = POSICOES[outro]
        x, y = km(*t.transform(lo, la))
        z = float(pbb[f"p{j}_chao"]) * EXAG / 1000
        ax.plot([x, x], [y, y], [z, topo], color="red", lw=2.5)
        ax.text(x + [0.3, -6.5, 0.3][j], y + [0.6, -1.2, 0][j], topo + 0.05, ["Atual", "P1 (topo do Conventos)", "P2 (Morro das Antenas)"][j], color="red",
                fontsize=10, weight="bold")
    for n_, nm, la, lo in obs:
        x, y = km(*t.transform(lo, la))
        z = float(np.nan_to_num(mds(la, lo), nan=0)) * EXAG / 1000
        ax.plot([x, x], [y, y], [z, z + 0.35], color="purple", lw=1.5)
        ax.text(x, y, z + 0.4, str(n_), color="purple", fontsize=9, weight="bold")
    ax.set_box_aspect((ext[1], ext[3], 2.5))
    ax.view_init(35, -110)
    ax.set_xlabel("km (leste)"); ax.set_ylabel("km (norte)"); ax.set_zticks([])
    ax.set_title("Vista 3D (exagero vertical 5×): posições do radar (vermelho) e obstáculos (roxo)\n" + leg, fontsize=9)
    fig.savefig(AQUI / "relatorio" / "figuras" / "v3_mapa3d_posicoes_simples.png", bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    main()
