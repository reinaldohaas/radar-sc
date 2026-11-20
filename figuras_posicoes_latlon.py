# -*- coding: utf-8 -*-
"""Figuras das posições do radar com as coordenadas (lat/lon) escritas em cada uma.

  relatorio/figuras/v3_pbb_posicoes.png      bloqueio (0,5° e 1,4°, até 60 km) com torre de 25 m em cada posição
  relatorio/figuras/v3_mapa3d_posicoes.png   relevo 3D (SIGSC, MDS) com as posições e os obstáculos, com lat/lon
Bloqueio: MDS de 1 m do SIGSC + 6 m de mata desde 2012, Terra 4/3, feixe de 2,2°.
"""
import math
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, colors
from matplotlib.colors import LightSource
from pyproj import Transformer

from posicoes_obstaculos import OBSTACULOS
from relevo_sigsc import ACERVO_MDS, PADRAO, PADRAO_MDS, Mosaico, folhas

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
FIG = AQUI / "relatorio" / "figuras"
POS = {"Atual": (-28.934548, -49.362490), "Topo da colina a NW": (-28.925236, -49.370698),
       "Proposta 1: topo do Morro dos Conventos": (-28.937250, -49.367620),
       "Proposta 2: Morro das Antenas": (-28.843869, -49.398756)}
TORRE = 25.0


def fmt(la, lo):
    return f"{la:.5f}, {lo:.5f}".replace(".", ",").replace(",  ", ", ")


def bloqueio():
    cache = AQUI / "dem" / "pbb_4posicoes_completo.npz"
    if cache.exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    from analise_mds import Nada, Superficie
    from relevo import Relevo
    from relevo_sigsc import RelevoSIGSC
    from simular_bloqueio import perfis, simular
    pos = list(POS.values())
    srtm = Relevo(*pos[0], fino_km=4.0, largo_km=100)
    mdt = RelevoSIGSC(srtm, posicoes=pos, raio_fino_km=2.0)
    mds = RelevoSIGSC(Nada(), posicoes=pos, raio_fino_km=2.0, padrao=PADRAO_MDS, acervo=ACERVO_MDS, mediana=True)
    sup = Superficie(mds, mdt, 6.0)
    az = np.arange(0, 360, 1.0)
    out = {"az": az}
    for k, (la, lo) in enumerate(pos):
        chao = float(mdt(la, lo))
        pf = perfis(la, lo, sup, az=az, max_km=60)
        _, d, r = simular(la, lo, chao + TORRE, sup, elevacoes=(0.5, 1.4), perfis_prontos=pf)
        out["d"] = d
        out[f"p{k}_05"], out[f"p{k}_14"], out[f"p{k}_chao"] = r[0.5], r[1.4], np.array(chao)
        print(list(POS)[k], "ok", flush=True)
    np.savez_compressed(cache, **out)
    return out


def polar(b):
    az, d = b["az"], b["d"]
    oeste = (az >= 240) & (az <= 340)
    i30 = np.searchsorted(d, 30000) - 1
    fig, eixos = plt.subplots(2, 4, figsize=(22, 11.5), subplot_kw={"projection": "polar"}, dpi=90)
    for col, (nome, (la, lo)) in enumerate(POS.items()):
        for lin, e in enumerate((0.5, 1.4)):
            ax = eixos[lin, col]
            r = b[f"p{col}_{'05' if e == 0.5 else '14'}"]
            T, R = np.meshgrid(np.radians(az), d / 1000, indexing="ij")
            m = ax.pcolormesh(T, R, r * 100, cmap="magma_r", vmin=0, vmax=100, shading="auto")
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1); ax.set_rlim(0, 60); ax.set_rticks([20, 40, 60])
            ax.set_title(f"{nome}\nlat {la:.5f}, lon {lo:.5f}; chão {float(b[f'p{col}_chao']):.0f} m, torre 25 m\n"
                         f"elevação {e}°: a 30 km, média {r[:, i30].mean():.0%}, oeste {r[oeste, i30].mean():.0%}",
                         fontsize=9.5)
    fig.colorbar(m, ax=eixos, shrink=0.6, label="Potência do feixe bloqueada (%)")
    fig.suptitle("Bloqueio simulado com torre de 25 m em cada posição: MDS 1 m do SIGSC (mata +6 m desde 2012), até 60 km",
                 fontsize=12)
    fig.savefig(FIG / "v3_pbb_posicoes.png", bbox_inches="tight"); plt.close(fig)


def _superficie(lim, passo):
    para_geo = Transformer.from_crs("EPSG:31982", "EPSG:4326", always_xy=True)
    res = 1.0 if passo < 5 else 5.0
    mdt = Mosaico(folhas(PADRAO), res, lim)
    mds = Mosaico(folhas(PADRAO_MDS, ACERVO_MDS), res, lim)
    E = np.arange(lim[0], lim[2], passo) + passo / 2
    N = np.arange(lim[3], lim[1], -passo) - passo / 2
    EE, NN = np.meshgrid(E, N)
    LO, LA = para_geo.transform(EE, NN)
    Z = mds(LA, LO)
    Z = np.where(np.isnan(Z), mdt(LA, LO), Z)
    agua = ~np.isfinite(Z) | (np.nan_to_num(Z, nan=0) < 0.8)
    Z = np.clip(np.nan_to_num(Z, nan=0.0), 0, None)
    ls = LightSource(azdeg=315, altdeg=40)
    base = cm.get_cmap("terrain")(colors.Normalize(-150, 330)(Z))
    rgb = ls.shade_rgb(base[..., :3], Z, vert_exag=3, blend_mode="soft")
    rgb[agua] = (0.62, 0.78, 0.92)
    return LO, LA, Z, rgb, mds


def _marca(ax, lo, la, z0, z1, txt, cor, dx, dy, tam=9):
    ax.plot([lo, lo], [la, la], [z0, z1], color=cor, lw=2.2)
    ax.plot([lo, lo + dx], [la, la + dy], [z1, z1], color=cor, lw=0.8)
    ax.text(lo + dx, la + dy, z1, txt, color=cor, fontsize=tam, weight="bold",
            bbox=dict(fc="white", ec=cor, alpha=0.85, pad=1.5))


def mapa3d(b):
    t = Transformer.from_crs("EPSG:4326", "EPSG:31982", always_xy=True)
    x0, y0 = t.transform(-49.3625, -28.9345)
    fig = plt.figure(figsize=(22, 11), dpi=95)

    # (a) regional: Morro dos Conventos e Morro das Antenas
    ax = fig.add_subplot(1, 2, 1, projection="3d", computed_zorder=False)
    lim = (649500.0, 6794500.0, 664500.0, 6812500.0)
    LO, LA, Z, rgb, mds = _superficie(lim, 40.0)
    EX = 6
    ax.plot_surface(LO, LA, Z * EX, facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    cores = ["red", "darkorange", "blue", "blue"]
    rot = ["Atual", "Colina NW", "P1 (topo do Conventos)", "P2 (Morro das Antenas)"]
    desl = [(0.012, -0.012), (-0.03, 0.02), (-0.045, -0.02), (0.015, 0.012)]
    for k, (nome, (la, lo)) in enumerate(POS.items()):
        z0 = float(b[f"p{k}_chao"]) * EX
        _marca(ax, lo, la, z0, z0 + 900 + 500 * k, f"{rot[k]}\n{la:.5f}, {lo:.5f}", cores[k], *desl[k])
    for n, (nm, la, lo, h, _) in enumerate(OBSTACULOS, 1):
        if nm.startswith(("Morro com mata", "Prédio")):
            z = float(np.nan_to_num(mds(la, lo), nan=0)) * EX
            _marca(ax, lo, la, z, z + 700, f"{n}", "purple", 0.0, 0.004, 8)
    ax.set_box_aspect((np.ptp(LO) * math.cos(math.radians(-28.9)), np.ptp(LA), 0.07))
    ax.view_init(30, -60)
    ax.set_xlabel("Longitude (°)", labelpad=10); ax.set_ylabel("Latitude (°)", labelpad=10); ax.set_zticks([])
    ax.set_title("(a) Região: Morro dos Conventos, Araranguá e Morro das Antenas (exagero 6×)", fontsize=11)

    # (b) aproximação do Morro dos Conventos
    ax = fig.add_subplot(1, 2, 2, projection="3d", computed_zorder=False)
    lim = (x0 - 1900.0, y0 - 1500.0, x0 + 700.0, y0 + 1700.0)
    LO, LA, Z, rgb, mds = _superficie(lim, 6.0)
    EX = 4
    ax.plot_surface(LO, LA, Z * EX, facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    desl = [(0.003, -0.004), (-0.006, 0.003), (-0.006, -0.004)]
    for k, (nome, (la, lo)) in enumerate(list(POS.items())[:3]):
        z0 = float(b[f"p{k}_chao"]) * EX
        _marca(ax, lo, la, z0, z0 + 170 + 70 * k, f"{rot[k]}\n{la:.5f}, {lo:.5f}", cores[k], *desl[k])
    for n, (nm, la, lo, h, _) in enumerate(OBSTACULOS, 1):
        if nm.startswith(("Farol", "Crista", "Vila")):
            z = float(np.nan_to_num(mds(la, lo), nan=0)) * EX
            dx, dy = {"Farol": (0.004, 0.0012), "Crista": (0.0025, 0.0015), "Vila": (0.002, 0.001)}[nm.split()[0]]
            _marca(ax, lo, la, z, z + 120, f"{n} {nm.split(' (')[0]}\n{la:.5f}, {lo:.5f}", "purple", dx, dy, 8)
    ax.set_box_aspect((np.ptp(LO) * math.cos(math.radians(-28.93)), np.ptp(LA), 0.35 * np.ptp(LA)))
    ax.view_init(38, -55)
    ax.set_xlabel("Longitude (°)", labelpad=10); ax.set_ylabel("Latitude (°)", labelpad=10); ax.set_zticks([])
    ax.set_title("(b) Morro dos Conventos (MDS 1 m, malha 6 m, exagero 4×): radar, propostas e obstáculos", fontsize=11)
    for a in fig.axes:
        a.ticklabel_format(useOffset=False)
    leg = "; ".join(f"{n} {nm} ({la:.5f}, {lo:.5f})" for n, (nm, la, lo, h, _) in enumerate(OBSTACULOS, 1)
                    if la is not None and not nm.startswith(("Mata do topo", "Torres existentes")))
    fig.text(0.5, 0.03, "Obstáculos (roxo): " + leg, ha="center", fontsize=8.5, wrap=True)
    fig.suptitle("Relevo e superfície do SIGSC: posições do radar (vermelho = atual, azul = propostas) e obstáculos", fontsize=13)
    fig.savefig(FIG / "v3_mapa3d_posicoes.png", bbox_inches="tight"); plt.close(fig)


def main():
    b = bloqueio()
    polar(b)
    mapa3d(b)
    print("ok")


if __name__ == "__main__":
    main()
