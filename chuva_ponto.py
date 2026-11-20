# -*- coding: utf-8 -*-
"""Taxa de precipitação estimada pelo radar de Araranguá num ponto (média num círculo), numa janela de horário local.

Para cada volume ODIM da janela:
  - refletividade bruta TH, com máscara de RhoHV médio ≥ 0,8 (chuva), sem a zona cega;
  - correção de atenuação em banda X pelo ΦDP (Zc = TH + 0,28·(ΦDP − Φ0)) só com --atenuacao;
  - R(Z) Marshall-Palmer (Z = 200 R^1,6) e R(Z) convectivo (Z = 300 R^1,4);
  - R(KDP) = 19,63·KDP^0,823 (banda X), com KDP da inclinação do ΦDP em ±1,5 km, onde KDP > 0,3 °/km.
Acumulado: integração no tempo entre os volumes.

Uso:
  python chuva_ponto.py --lat -28.4825 --lon -48.7808 --nome Laguna --data 2026-11-20 --das 8 --ate 9
Saída: chuva/<nome>_<data>.csv e chuva/<nome>_<data>.png
"""
import argparse
import csv
import ftplib
from datetime import datetime, timedelta
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import baixar_ftp_sc as ftpsc
from leitor_odim import RHOHV_MIN, ZONA_CEGA_KM, _suavizar

AQUI = Path(__file__).resolve().parent
RADAR = (-28.934548, -49.362490)
FUSO = -3  # horário de Brasília
ATENUACAO = False


def _fis(g):
    a = g["what"].attrs
    b = g["data"][()]
    f = b.astype(float) * float(a["gain"]) + float(a["offset"])
    f[(b == a["nodata"]) | (b == a["undetect"])] = np.nan
    return f


def ler(arq, elev):
    with h5py.File(arq, "r") as h:
        for k in h:
            if k.startswith("dataset") and round(float(h[k]["where"].attrs["elangle"]), 1) == elev:
                ds = h[k]
                w = ds["where"].attrs
                q = {ds[d]["what"].attrs["quantity"].decode(): _fis(ds[d]) for d in ds if d.startswith("data")}
                how = ds["how"].attrs
                ini, fim = np.asarray(how["startazA"], float), np.asarray(how["stopazA"], float)
                az = (ini + (fim - ini) % 360 / 2) % 360
                return az, float(w["rscale"]) / 1000, q
    return None


def taxa(arq, elev, alvo, raio_km):
    lido = ler(arq, elev)
    if lido is None:
        return None
    az, dr, q = lido
    th, rho, ph = q["TH"], q["RHOHV"], q["PHIDP"]
    r = (np.arange(th.shape[1]) + 0.5) * dr
    chuva = (_suavizar(rho, dr) >= RHOHV_MIN) & np.isfinite(th) & (r >= ZONA_CEGA_KM)[None, :]
    # atenuação: ΦDP acumulado ao longo de cada raio, só em chuva
    phc = np.where(chuva, ph, np.nan)
    from scipy.ndimage import median_filter
    phs = median_filter(np.nan_to_num(phc, nan=-999), size=(1, 33))
    phs = np.where(phs < -900, np.nan, phs)
    phi0 = np.nanpercentile(phs, 5, axis=1, keepdims=True)
    acum = np.fmax.accumulate(np.nan_to_num(phs - phi0, nan=0.0).clip(0, 120), axis=1)
    # A correção pelo ΦDP fica desligada por padrão: com o SNR baixo deste radar o ΦDP acumula ruído (5–12 dB falsos).
    zc = np.where(chuva, th + (0.28 * acum if ATENUACAO else 0.0), np.nan)
    # KDP: inclinação do ΦDP suavizado em ±1,5 km
    n = int(round(1.5 / dr))
    kdp = np.full(th.shape, np.nan)
    kdp[:, n:-n] = (phs[:, 2 * n:] - phs[:, :-2 * n]) / (2 * 2 * n * dr)
    # gates dentro do círculo em volta do alvo
    from pyproj import Geod
    g = Geod(ellps="WGS84")
    az_a, _, d_a = g.inv(RADAR[1], RADAR[0], alvo[1], alvo[0])
    d_a /= 1000
    A, Rr = np.meshgrid(np.radians(az), r, indexing="ij")
    x, y = Rr * np.sin(A), Rr * np.cos(A)
    xa, ya = d_a * np.sin(np.radians(az_a)), d_a * np.cos(np.radians(az_a))
    perto = (x - xa) ** 2 + (y - ya) ** 2 <= raio_km ** 2
    z = zc[perto]
    frac_chuva = np.isfinite(z).mean()
    zlin = 10 ** (np.nan_to_num(z, nan=-99) / 10)
    r_mp = np.where(np.isfinite(z), (zlin / 200) ** (1 / 1.6), 0.0)
    r_cv = np.where(np.isfinite(z), (zlin / 300) ** (1 / 1.4), 0.0)
    k = kdp[perto]
    kk = np.where(np.isfinite(z) & (k > 0.3), k, np.nan)
    r_kdp = np.where(np.isfinite(kk), 19.63 * np.nan_to_num(kk) ** 0.823, np.where(np.isfinite(z), r_mp, 0.0))
    return dict(dist_km=d_a, az=az_a, n=int(perto.sum()), frac=frac_chuva,
                z_med=float(np.nanmedian(z)) if np.isfinite(z).any() else np.nan,
                z_max=float(np.nanmax(z)) if np.isfinite(z).any() else np.nan,
                pia=float(np.nanmedian(0.28 * acum[perto])),
                r_mp=float(r_mp.mean()), r_cv=float(r_cv.mean()), r_kdp=float(r_kdp.mean()),
                campo=(az, r, zc))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--nome", required=True)
    ap.add_argument("--data", required=True, help="AAAA-MM-DD (horário local)")
    ap.add_argument("--das", type=float, required=True, help="hora local de início")
    ap.add_argument("--ate", type=float, required=True, help="hora local de fim")
    ap.add_argument("--raio", type=float, default=3.0, help="raio do círculo em volta do ponto (km)")
    ap.add_argument("--atenuacao", action="store_true", help="corrige a atenuação pelo ΦDP (ruidoso neste radar)")
    a = ap.parse_args()
    global ATENUACAO
    ATENUACAO = a.atenuacao
    dia = datetime.strptime(a.data, "%Y-%m-%d")
    ini = dia + timedelta(hours=a.das - FUSO) - timedelta(minutes=10)
    fim = dia + timedelta(hours=a.ate - FUSO) + timedelta(minutes=10)

    host, user, senha = ftpsc.credenciais()
    with ftplib.FTP(host, timeout=60) as ftp:
        ftp.login(user, senha)
        vols = ftpsc.volumes(ftp, "ARA", "HDF5", ini, fim)
        print(f"{len(vols)} volumes de {ini:%H:%M} a {fim:%H:%M} UTC")
        arqs = [(t, ftpsc.baixar(ftp, "ARA", "HDF5", n)) for t, n in vols]

    alvo = (a.lat, a.lon)
    saida = AQUI / "chuva"
    saida.mkdir(exist_ok=True)
    base = saida / f"{a.nome}_{a.data}"
    linhas = [["hora_local", "hora_utc", "elev", "dist_km", "gates", "fracao_com_chuva", "z_mediano_dbz", "z_max_dbz",
               "atenuacao_phidp_db" + ("" if ATENUACAO else "_nao_aplicada"), "r_marshall_palmer_mm_h", "r_convectivo_mm_h", "r_kdp_mm_h"]]
    serie = {0.5: [], 1.4: []}
    mapa = None
    for t, arq in arqs:
        for e in (0.5, 1.4):
            res = taxa(arq, e, alvo, a.raio)
            if res is None:
                continue
            tl = t + timedelta(hours=FUSO)
            linhas.append([f"{tl:%H:%M:%S}", f"{t:%H:%M:%S}", e, f"{res['dist_km']:.1f}", res["n"], f"{res['frac']:.2f}",
                           f"{res['z_med']:.1f}", f"{res['z_max']:.1f}", f"{res['pia']:.1f}",
                           f"{res['r_mp']:.2f}", f"{res['r_cv']:.2f}", f"{res['r_kdp']:.2f}"])
            serie[e].append((tl, res["r_mp"], res["r_cv"], res["r_kdp"]))
            if e == 1.4 and (mapa is None or res["r_mp"] > mapa[1]):
                mapa = (tl, res["r_mp"], res["campo"])
    with open(f"{base}.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)

    def acumulado(s, i):
        h0, h1 = dia + timedelta(hours=a.das), dia + timedelta(hours=a.ate)
        tt = np.array([(x[0] - h0).total_seconds() / 3600 for x in s]); vv = np.array([x[i] for x in s])
        ok = (tt >= -0.01) & (tt <= (h1 - h0).total_seconds() / 3600 + 0.01)
        return float(np.trapezoid(vv[ok], tt[ok])) if ok.sum() > 1 else np.nan

    print(f"{a.nome}: {serie[1.4][0][0]:%H:%M}–{serie[1.4][-1][0]:%H:%M} local, distância {linhas[1][3]} km")
    for e in (0.5, 1.4):
        s = serie[e]
        if s:
            print(f"  {e}°: acumulado {a.das:.0f}–{a.ate:.0f} h: MP {acumulado(s, 1):.1f} mm, convectivo {acumulado(s, 2):.1f} mm, "
                  f"KDP {acumulado(s, 3):.1f} mm | taxa máx MP {max(x[1] for x in s):.1f} mm/h, KDP {max(x[3] for x in s):.1f} mm/h")

    fig, (ax, axm) = plt.subplots(1, 2, figsize=(15, 6), dpi=100, gridspec_kw={"width_ratios": [1.3, 1]})
    for e, ls in ((0.5, "--"), (1.4, "-")):
        s = serie[e]
        if not s:
            continue
        tt = [x[0] for x in s]
        ax.plot(tt, [x[1] for x in s], ls, color="#3182bd", label=f"Z=200R^1,6 ({e}°)")
        ax.plot(tt, [x[2] for x in s], ls, color="#e6550d", label=f"Z=300R^1,4 ({e}°)")
        ax.plot(tt, [x[3] for x in s], ls, color="#31a354", label=f"KDP ({e}°)")
    ax.set_ylabel("Taxa média no círculo (mm/h)"); ax.set_xlabel("Hora local")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title(f"{a.nome}: taxa de precipitação pelo radar de Araranguá (círculo de {a.raio:.0f} km)")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    if mapa:
        tl, _, (az, r, zc) = mapa
        lim = r <= 110
        T, Rr = np.meshgrid(np.radians(az), r[lim], indexing="ij")
        X, Y = Rr * np.sin(T), Rr * np.cos(T)
        zl = 10 ** (zc[:, lim] / 10)
        R = (zl / 200) ** (1 / 1.6)
        m = axm.pcolormesh(X, Y, np.where(R >= 0.5, R, np.nan), cmap="turbo", vmin=0, vmax=50, shading="auto")
        from pyproj import Geod
        g = Geod(ellps="WGS84")
        az_a, _, d_a = g.inv(RADAR[1], RADAR[0], a.lon, a.lat)
        xa, ya = d_a / 1000 * np.sin(np.radians(az_a)), d_a / 1000 * np.cos(np.radians(az_a))
        axm.add_patch(plt.Circle((xa, ya), a.raio, fill=False, color="k", lw=1.2))
        axm.text(xa + a.raio, ya, a.nome, fontsize=9, weight="bold")
        axm.plot(0, 0, "k+", ms=10); axm.text(1, -4, "Araranguá", fontsize=8)
        axm.set_aspect("equal"); axm.set_xlim(-30, 100); axm.set_ylim(-40, 100)
        axm.set_xlabel("km a leste do radar"); axm.set_ylabel("km ao norte do radar")
        axm.set_title(f"Taxa (Z=200R^1,6), 1,4°, {tl:%H:%M} local")
        fig.colorbar(m, ax=axm, label="mm/h")
    fig.tight_layout(); fig.savefig(f"{base}.png"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
