# -*- coding: utf-8 -*-
"""Por que os setores sem eco mudam de um horário para outro? Compara, volume a volume, a refletividade total (TH)
com a filtrada (DBZH) a 0,5° e 1,4°.

Para cada raio com chuva no TH (RhoHV médio ≥ 0,8 e TH ≥ 15 dBZ em pelo menos 20 gates entre 5 e 60 km):
  - "apagado pelo filtro": o DBZH tem menos de 20% desses gates;
  - "sombra de atenuação": a chuva no TH termina num núcleo de ≥ 45 dBZ e não há eco nos 10 km seguintes,
    enquanto os raios vizinhos (±5°) seguem com eco além dali.
Também mede se chovia sobre o radar (TH ≥ 25 dBZ em ≥ 30% do anel de 2,5–5 km), o que molha o radome.

Saída: relatorio/setores_por_volume.csv e relatorio/figuras/v3_setores_por_volume.png
"""
import csv
import glob
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analise_polarimetrica import ler
from leitor_odim import RHOHV_MIN, _suavizar

AQUI = Path(__file__).resolve().parent


def analisar(q, dr):
    th, dbzh = q["TH"], q["DBZH"]
    r = (np.arange(th.shape[1]) + 0.5) * dr
    faixa = (r >= 5) & (r <= 60)
    chuva = (_suavizar(q["RHOHV"], dr) >= RHOHV_MIN) & (th >= 15) & faixa[None, :]
    n_th = chuva.sum(1)
    n_dbzh = (chuva & np.isfinite(dbzh)).sum(1)
    com_chuva = n_th >= 20
    apagado = com_chuva & (n_dbzh < 0.2 * n_th)
    # sombra de atenuação
    ult = np.array([np.flatnonzero(c)[-1] if c.any() else -1 for c in chuva])
    sombra = np.zeros(len(ult), bool)
    n10 = int(10 / dr)
    for i, j in enumerate(ult):
        if j < 0 or j + n10 >= th.shape[1] or r[j] > 50:
            continue
        nucleo = np.nanmax(th[i, max(0, j - n10):j + 1]) >= 45
        viz = [(i + k) % len(ult) for k in range(-5, 6) if k]
        alem = np.mean([ult[v] > j + n10 for v in viz])
        sombra[i] = nucleo and alem >= 0.5
    anel = (r >= 2.5) & (r <= 5)
    radome = np.nanmean(np.nan_to_num(th[:, anel], nan=-99) >= 25) >= 0.3
    return com_chuva.sum(), apagado.sum(), sombra.sum(), radome, apagado


def main():
    arqs = sorted(glob.glob(str(AQUI / "amostras" / "ARA" / "*.hdf")))
    linhas = [["volume_utc", "elev", "raios_com_chuva_TH", "raios_apagados_no_DBZH", "fracao_apagada",
               "raios_com_sombra_de_atenuacao", "chuva_sobre_o_radar"]]
    mapa = {}
    for a in arqs:
        t = datetime.strptime(Path(a).name.split("-PPIVol-")[1][:15], "%Y%m%d-%H%M%S")
        vol = ler(a)
        for e in (0.5, 1.4):
            if e not in vol:
                continue
            az, dr, q = vol[e]
            n, ap, sb, rd, mask = analisar(q, dr)
            linhas.append([f"{t:%Y-%m-%d %H:%M}", e, n, ap, f"{ap / n:.2f}" if n else "", sb, int(rd)])
            if e == 0.5:
                mapa[t] = (az, mask, n)
    with open(AQUI / "relatorio" / "setores_por_volume.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)

    # figura: raios apagados pelo filtro, por volume (0,5°)
    ts = sorted(t for t in mapa if mapa[t][2] >= 30)
    fig, ax = plt.subplots(figsize=(13, 6), dpi=100)
    for k, t in enumerate(ts):
        az, mask, _ = mapa[t]
        ax.scatter(az[mask], np.full(mask.sum(), k), s=4, color="#d62728")
    ax.set_yticks(range(len(ts))); ax.set_yticklabels([f"{t:%d/%m %H:%M}" for t in ts], fontsize=7)
    ax.set_xlim(0, 360); ax.set_xticks(range(0, 361, 30)); ax.set_xlabel("Azimute (°)")
    ax.set_title("0,5°: raios com chuva no TH e apagados no DBZH pelo filtro de clutter, por volume (UTC)")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout(); fig.savefig(AQUI / "relatorio" / "figuras" / "v3_setores_por_volume.png"); plt.close(fig)

    v = np.array([[float(x) if x != "" else np.nan for x in l[2:]] for l in linhas[1:]])
    e = np.array([l[1] for l in linhas[1:]])
    for el in (0.5, 1.4):
        s = (e == el) & (v[:, 0] >= 30)
        print(f"{el}°: {s.sum()} volumes com chuva; raios apagados pelo filtro: mediana {np.nanmedian(v[s, 1]):.0f} "
              f"(máx {np.nanmax(v[s, 1]):.0f}), fração mediana {np.nanmedian(v[s, 2]):.2f}; sombras de atenuação: "
              f"mediana {np.nanmedian(v[s, 3]):.0f} (máx {np.nanmax(v[s, 3]):.0f}); chuva sobre o radar em {int(np.nansum(v[s, 4]))} volumes")


if __name__ == "__main__":
    main()
