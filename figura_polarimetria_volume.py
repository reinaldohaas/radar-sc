# -*- coding: utf-8 -*-
"""Variáveis polarimétricas de um volume de Araranguá com chuva forte sobre o radar: por que hoje não dá para
corrigir a atenuação (nem a do radome molhado) com o ΦDP/KDP e o ZDR.

Painéis (0,5°): TH, ZDR, ΦDP, KDP (inclinação do ΦDP em ±1,5 km), RhoHV e SNR, até 80 km.
Perfil: num raio com chuva forte, o ΦDP medido x o ΦDP esperado pela refletividade (autoconsistência, banda X).
Diagnósticos impressos e gravados em relatorio/polarimetria_<data>.csv.

Uso: python figura_polarimetria_volume.py cache_vol/ARA/9842SAN-PPIVol-20261120-112044-0000.hdf
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter

from analise_polarimetrica import ler
from desenhar_ppi import CMAP, NORM
from leitor_odim import _suavizar

AQUI = Path(__file__).resolve().parent
C_KDP, B_KDP = 3.3e-4, 0.8     # KDP ≈ c·Z^b em banda X (chuva típica: 40 dBZ ↔ ~0,5 °/km)


def main():
    arq = Path(sys.argv[1])
    t = datetime.strptime(arq.name.split("-PPIVol-")[1][:15], "%Y%m%d-%H%M%S")
    az, dr, q = ler(arq)[0.5]
    th, zdr, ph, rho, snr = q["TH"], q["ZDR"], q["PHIDP"], q["RHOHV"], q["SNR"]
    r = (np.arange(th.shape[1]) + 0.5) * dr
    chuva = (_suavizar(rho, dr) >= 0.8) & (th >= 20) & (r >= 2.5)[None, :]
    phs = median_filter(np.nan_to_num(np.where(chuva, ph, np.nan), nan=-999), size=(1, 25))
    phs = np.where(phs < -900, np.nan, phs)
    n = int(round(1.5 / dr))
    kdp = np.full(th.shape, np.nan)
    kdp[:, n:-n] = (phs[:, 2 * n:] - phs[:, :-2 * n]) / (2 * 2 * n * dr)
    kdp = np.where(chuva, kdp, np.nan)

    # diagnósticos em chuva moderada a forte (35–55 dBZ)
    m = chuva & (th >= 35) & (th <= 55)
    tex = np.abs(ph - phs)
    kdp_esp = C_KDP * (10 ** (th / 10)) ** B_KDP
    diag = {
        "gates de chuva 35–55 dBZ": int(m.sum()),
        "SNR mediano (dB)": float(np.nanmedian(snr[m])),
        "RhoHV mediano": float(np.nanmedian(rho[m])),
        "ZDR mediano (dB; esperado +0,5 a +2)": float(np.nanmedian(zdr[m])),
        "fração com ZDR < 0": float(np.nanmean(zdr[m] < 0)),
        "ruído do ΦDP, mediana |ΦDP − suavizado| (°)": float(np.nanmedian(tex[m])),
        "KDP mediano medido (°/km)": float(np.nanmedian(kdp[m])),
        "KDP esperado pela refletividade (°/km)": float(np.nanmedian(kdp_esp[m])),
        "fração com KDP < 0": float(np.nanmean(kdp[m] < 0)),
    }
    for k, v in diag.items():
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}")
    rot = f"{t:%Y%m%d_%H%M}"
    with open(AQUI / "relatorio" / f"polarimetria_{rot}.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["indicador", "valor"]] + [[k, f"{v:.3f}" if isinstance(v, float) else v] for k, v in diag.items()])

    # raio com mais chuva forte para o perfil
    i = int(np.argmax(np.nansum(np.where(m, 10 ** (th / 10) ** B_KDP, 0), axis=1)))

    lim = r <= 80
    T, R = np.meshgrid(np.radians(az), r[lim], indexing="ij")
    X, Y = R * np.sin(T), R * np.cos(T)
    fig = plt.figure(figsize=(18, 15), dpi=85)
    paineis = [("TH (dBZ), máscara de RhoHV", np.where(chuva, th, np.nan), dict(cmap=CMAP, norm=NORM)),
               ("ZDR (dB)", np.where(chuva, zdr, np.nan), dict(cmap="RdBu_r", vmin=-4, vmax=4)),
               ("ΦDP (°)", np.where(chuva, ph, np.nan), dict(cmap="twilight", vmin=-180, vmax=180)),
               ("KDP (°/km), da inclinação do ΦDP", kdp, dict(cmap="RdBu_r", vmin=-4, vmax=4)),
               ("RhoHV", np.where(np.isfinite(th), rho, np.nan), dict(cmap="viridis", vmin=0.5, vmax=1)),
               ("SNR (dB)", np.where(np.isfinite(th), snr, np.nan), dict(cmap="magma", vmin=0, vmax=30))]
    for k, (tit, campo, kw) in enumerate(paineis):
        ax = fig.add_subplot(3, 3, k + 1)
        mm = ax.pcolormesh(X, Y, campo[:, lim], shading="auto", **kw)
        ax.plot([0, 80 * np.sin(np.radians(az[i]))], [0, 80 * np.cos(np.radians(az[i]))], "k--", lw=0.8)
        ax.set_aspect("equal"); ax.set_xlim(-80, 80); ax.set_ylim(-80, 80); ax.set_title(tit, fontsize=11)
        fig.colorbar(mm, ax=ax, shrink=0.8)
    ax = fig.add_subplot(3, 1, 3)
    ax.plot(r, th[i], color="0.5", lw=0.8, label="TH (dBZ)")
    ax.set_ylabel("TH (dBZ)"); ax.set_xlabel("Distância (km)"); ax.set_xlim(0, 80)
    ax2 = ax.twinx()
    esp = 2 * np.nancumsum(np.where(chuva[i], kdp_esp[i], 0) * dr)
    phi0 = np.nanmedian(ph[i, chuva[i]][:20]) if chuva[i].sum() > 20 else 0
    ax2.plot(r, np.where(chuva[i], ph[i], np.nan), ".", ms=2, color="tab:blue", label="ΦDP medido")
    ax2.plot(r, phi0 + esp, color="tab:red", lw=1.5, label="ΦDP esperado pela refletividade")
    ax2.plot(r, np.where(chuva[i], zdr[i] * 10, np.nan), ".", ms=2, color="tab:green", label="ZDR × 10 (dB)")
    ax2.set_ylabel("ΦDP (°)  /  ZDR × 10")
    ax2.legend(loc="upper right", fontsize=9); ax.legend(loc="upper left", fontsize=9)
    ax.set_title(f"Raio de {az[i]:.0f}°: o ΦDP medido não acompanha o esperado e o ZDR fica negativo em chuva forte", fontsize=11)
    fig.suptitle(f"Araranguá, 0,5°, {t:%d/%m/%Y %H:%M} UTC ({(t.hour - 3) % 24:02d}:{t:%M} local), com chuva sobre o radar", fontsize=13)
    fig.tight_layout()
    saida = AQUI / "relatorio" / "figuras" / f"polarimetria_{rot}.png"
    fig.savefig(saida); plt.close(fig)
    print(saida)


if __name__ == "__main__":
    main()
