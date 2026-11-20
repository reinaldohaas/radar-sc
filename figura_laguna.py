# -*- coding: utf-8 -*-
"""Refletividade do radar de Araranguá na chegada da chuva extrema a Laguna (20/11/2026, manhã).

Painéis: 08:18 e 08:57 (hora local), 0,5° e 1,4°, TH com máscara de RhoHV médio ≥ 0,8 (leitor_odim).
Entre 08:21 e 08:57 não há volumes no FTP.
Saída: relatorio/figuras/laguna_20261120_refletividade.png
"""
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
import numpy as np

from desenhar_ppi import CMAP, NIVEIS, NORM
from leitor_odim import ler_volume_odim
from leitor_vol import polar_para_latlon

AQUI = Path(__file__).resolve().parent
VOLUMES = ["9842SAN-PPIVol-20261120-111841-0000.hdf", "9842SAN-PPIVol-20261120-115737-0000.hdf"]
LUGARES = {"Laguna": (-28.4825, -48.7808), "Tubarão": (-28.4667, -49.0069), "Imbituba": (-28.2400, -48.6703),
           "Criciúma": (-28.6775, -49.3697), "Araranguá": (-28.9350, -49.4860), "Jaguaruna": (-28.6147, -49.0258)}
EXT = [-49.75, -48.55, -29.20, -28.15]


def main():
    fig, eixos = plt.subplots(2, 2, figsize=(13, 12), dpi=100, subplot_kw={"projection": ccrs.PlateCarree()})
    for col, nome in enumerate(VOLUMES):
        t = datetime.strptime(nome.split("-PPIVol-")[1][:15], "%Y%m%d-%H%M%S")
        vol = ler_volume_odim(AQUI / "cache_vol" / "ARA" / nome)
        for lin, e in enumerate((0.5, 1.4)):
            s = min(vol["slices"], key=lambda x: abs(x["ele_deg"] - e))
            dados = s["data"].astype(float)
            dados[dados < NIVEIS[0]] = np.nan
            lat, lon, _ = polar_para_latlon(vol["lat0"], vol["lon0"], s["azimuths"], s["ranges_km"], s["ele_deg"])
            ax = eixos[lin, col]
            ax.set_extent(EXT, crs=ccrs.PlateCarree())
            ax.add_feature(cf.COASTLINE.with_scale("10m"), linewidth=0.7, edgecolor="#444")
            m = ax.pcolormesh(lon[:, ::2], lat[:, ::2], np.ma.masked_invalid(dados[:, ::2]), cmap=CMAP, norm=NORM,
                              shading="auto", transform=ccrs.PlateCarree())
            for nm, (la, lo) in LUGARES.items():
                ax.plot(lo, la, "k.", ms=5, transform=ccrs.PlateCarree())
                ax.text(lo + 0.02, la + 0.015, nm, fontsize=9, weight="bold" if nm == "Laguna" else None,
                        transform=ccrs.PlateCarree())
            ax.plot(vol["lon0"], vol["lat0"], "k+", ms=12, mew=1.8, transform=ccrs.PlateCarree())
            az = np.linspace(0, 360, 361)
            for r in (25, 50, 75, 100):
                la, lo, _ = polar_para_latlon(vol["lat0"], vol["lon0"], az, np.array([float(r)]), 0.0)
                ax.plot(lo[:, 0], la[:, 0], color="#888", lw=0.5, ls="--", transform=ccrs.PlateCarree())
            local = t - timedelta(hours=3)
            ax.set_title(f"{local:%H:%M} local ({t:%H:%M} UTC), elevação {s['ele_deg']:.1f}°", fontsize=11)
    cb = fig.colorbar(m, ax=eixos, orientation="horizontal", fraction=0.035, pad=0.03, ticks=NIVEIS)
    cb.set_label("Refletividade TH (dBZ), máscara de RhoHV médio ≥ 0,8")
    fig.suptitle("Radar de Araranguá, 20/11/2026: chegada da chuva extrema a Laguna\n"
                 "(não há volumes no FTP entre 08:21 e 08:57; anéis a cada 25 km)", fontsize=12)
    fig.text(0.99, 0.005, "Dados: Defesa Civil de SC", ha="right", fontsize=8, color="#666")
    saida = AQUI / "relatorio" / "figuras" / "laguna_20261120_refletividade.png"
    fig.savefig(saida, bbox_inches="tight"); plt.close(fig)
    print(saida)


if __name__ == "__main__":
    main()
