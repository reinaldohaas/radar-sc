# -*- coding: utf-8 -*-
"""Desenha o PPI de refletividade da elevação mais baixa de um volume Rainbow5 (.vol).

Uso direto (teste):
  python desenhar_ppi.py arquivo_dBZ.vol saida.png
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from leitor_vol import ler_volume_rainbow, polar_para_latlon
from leitor_odim import ler_volume_odim

# Escala de refletividade em degraus de 5 dBZ
NIVEIS = list(range(10, 80, 5))
CORES = ["#04e9e7", "#019ff4", "#0300f4", "#02fd02", "#01c501", "#008e00", "#fdf802",
         "#e5bc00", "#fd9500", "#fd0000", "#d40000", "#bc0000", "#f800fd"]
CMAP = ListedColormap(CORES)
NORM = BoundaryNorm(NIVEIS, CMAP.N)

CIDADES = {
    "Chapecó": (-27.10, -52.62), "Lontras": (-27.17, -49.54), "Araranguá": (-28.94, -49.49),
    "Florianópolis": (-27.60, -48.55), "Joinville": (-26.30, -48.85), "Blumenau": (-26.92, -49.07),
    "Lages": (-27.82, -50.33), "Criciúma": (-28.68, -49.37), "Urubici": (-28.02, -49.59),
    "Joaçaba": (-27.17, -51.50), "São Miguel do Oeste": (-26.73, -53.52), "Caçador": (-26.78, -51.01),
}


def _fundo(ax):
    """Litoral e divisas estaduais via cartopy, se disponível; senão só grade."""
    try:
        import cartopy.feature as cf
        ax.add_feature(cf.COASTLINE.with_scale("10m"), linewidth=0.7, edgecolor="#444")
        ax.add_feature(cf.STATES.with_scale("10m"), linewidth=0.6, edgecolor="#666")
        ax.add_feature(cf.BORDERS.with_scale("10m"), linewidth=0.8, edgecolor="#444")
    except Exception:
        pass


def ler(caminho):
    """Rainbow5 (.vol) ou ODIM_H5 (.hdf/.h5)."""
    return ler_volume_odim(caminho) if Path(caminho).suffix.lower() in (".hdf", ".h5") else ler_volume_rainbow(caminho)


def desenhar(vol_path, saida, nome, t_utc: datetime, alcance_km=250):
    vol = ler(vol_path)
    s = min(vol["slices"], key=lambda x: x["ele_deg"])
    alcance_km = min(alcance_km, float(s["ranges_km"][-1]))
    passo = max(1, len(s["ranges_km"]) // 1500)  # bins de 31 m: reduz para a imagem
    dados = s["data"][:, ::passo].astype(float)
    s = dict(s, ranges_km=s["ranges_km"][::passo])
    dados[dados < NIVEIS[0]] = np.nan
    lat, lon, _ = polar_para_latlon(vol["lat0"], vol["lon0"], s["azimuths"], s["ranges_km"], s["ele_deg"])
    dentro = s["ranges_km"] <= alcance_km
    lat, lon, dados = lat[:, dentro], lon[:, dentro], dados[:, dentro]

    dlat = alcance_km / 111.132
    dlon = alcance_km / (111.320 * np.cos(np.deg2rad(vol["lat0"])))
    ext = [vol["lon0"] - dlon, vol["lon0"] + dlon, vol["lat0"] - dlat, vol["lat0"] + dlat]

    try:
        import cartopy.crs as ccrs
        fig = plt.figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(projection=ccrs.PlateCarree())
        ax.set_extent(ext, crs=ccrs.PlateCarree())
        kw = {"transform": ccrs.PlateCarree()}
        _fundo(ax)
    except Exception:
        fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
        ax.set_xlim(ext[:2]); ax.set_ylim(ext[2:]); ax.set_aspect(1 / np.cos(np.deg2rad(vol["lat0"])))
        kw = {}

    m = ax.pcolormesh(lon, lat, np.ma.masked_invalid(dados), cmap=CMAP, norm=NORM, shading="auto", **kw)

    # Anéis de 50 km
    az = np.linspace(0, 360, 361)
    passo_anel = 50 if alcance_km > 150 else 25
    for r in range(passo_anel, int(alcance_km) + 1, passo_anel):
        la, lo, _ = polar_para_latlon(vol["lat0"], vol["lon0"], az, np.array([r], dtype=float), 0.0)
        ax.plot(lo[:, 0], la[:, 0], color="#888", lw=0.5, ls="--", **kw)
    for cidade, (la, lo) in CIDADES.items():
        if ext[0] < lo < ext[1] and ext[2] < la < ext[3]:
            ax.plot(lo, la, "k.", ms=4, **kw)
            ax.text(lo + 0.03, la + 0.03, cidade, fontsize=7, **kw)
    ax.plot(vol["lon0"], vol["lat0"], "k+", ms=10, mew=1.5, **kw)

    local = t_utc - timedelta(hours=3)
    ax.set_title(f"{nome} · refletividade {s['ele_deg']:.1f}°\n"
                 f"{local:%d/%m/%Y %H:%M} local ({t_utc:%H:%M} UTC)", fontsize=11)
    cb = fig.colorbar(m, ax=ax, orientation="horizontal", fraction=0.04, pad=0.03, ticks=NIVEIS)
    cb.set_label("dBZ")
    fig.text(0.99, 0.005, "Dados: Defesa Civil de SC", ha="right", fontsize=7, color="#666")
    fig.savefig(saida, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import re
    p = Path(sys.argv[1])
    m = re.match(r"(\d{14})", p.name)
    t = datetime.strptime(m.group(1), "%Y%m%d%H%M%S") if m else datetime.utcnow()
    desenhar(p, sys.argv[2], "Teste", t)
