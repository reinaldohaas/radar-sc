# -*- coding: utf-8 -*-
"""Bloqueio do feixe de Araranguá estimado pelos próprios dados polarimétricos (PHIDP → KDP, e ZDR).

Ideia: a fase diferencial ΦDP não depende da potência recebida. Se parte do feixe está bloqueada, a refletividade
cai, mas o ΔΦDP acumulado na chuva continua o mesmo. Na chuva vale KDP ≈ c·Z^b, então ΔΦDP = 2·c·∫Z^b dr.
Com c de referência (azimutes livres), a razão entre o ΔΦDP medido e o esperado pela refletividade dá a perda
de potência no azimute (método de autoconsistência, Giangrande & Ryzhkov 2005; Lang et al. 2009).

Passos por raio (só gates de chuva: RhoHV ≥ 0,95, SNR ≥ 10 dB, 10 ≤ TH ≤ 55 dBZ, 3–60 km):
  - ΦDP suavizado (mediana móvel), ΔΦDP = fim − início do trecho de chuva; usa raios com ΔΦDP ≥ 4°;
  - atenuação corrigida: Zc = TH + α·(ΦDP − Φ0), α = 0,28 dB/° (banda X); ZDRc = ZDR + β·(ΦDP − Φ0), β = 0,04 dB/°;
  - c_est = ΔΦDP / (2 ∫ Zc^b dr), b = 0,8;
  - perda (dB) = (10/b)·log10(c_est / c_ref); fração bloqueada = 1 − 10^(−perda/10).
ZDR: mediana em chuva fraca (20–30 dBZ, RhoHV ≥ 0,97), onde o ZDR verdadeiro fica em ~0,2–0,5 dB.
Desvios por azimute indicam bloqueio diferencial entre H e V; o desvio médio é o erro de calibração do ZDR.

Entrada: amostras/ARA/*.hdf (baixar com baixar_ftp_sc.py --amostra ARA --quantas N)
Saída:  relatorio/polarimetria_azimute.csv, relatorio/figuras/v3_polarimetria.png
"""
import csv
import glob
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter

AQUI = Path(__file__).resolve().parent
ALFA, BETA, B = 0.28, 0.04, 0.8
REF = (30, 200)          # azimutes de referência: mar e planície a leste, sem bloqueio simulado a 1,4° e 2,4°
PASSO = 5                # largura das classes de azimute (graus)
ELEV = (0.5, 1.4, 2.4)


def _fis(g):
    a = g["what"].attrs
    b = g["data"][()]
    f = b.astype(float) * float(a["gain"]) + float(a["offset"])
    f[(b == a["nodata"]) | (b == a["undetect"])] = np.nan
    return f


def ler(arq):
    out = {}
    with h5py.File(arq, "r") as h:
        for k in h:
            if not k.startswith("dataset"):
                continue
            ds = h[k]
            w = ds["where"].attrs
            e = round(float(w["elangle"]), 1)
            if e not in ELEV:
                continue
            q = {ds[d]["what"].attrs["quantity"].decode(): _fis(ds[d]) for d in ds if d.startswith("data")}
            how = ds["how"].attrs if "how" in ds else {}
            nr = int(w["nrays"])
            if "startazA" in how:
                ini, fim = np.asarray(how["startazA"], float), np.asarray(how["stopazA"], float)
                az = (ini + (fim - ini) % 360 / 2) % 360
            else:
                az = (np.arange(nr) + 0.5) * 360.0 / nr
            out[e] = (az, float(w["rscale"]) / 1000, q)
    return out


def raios(az, dr, q):
    th, zdr, rho, ph, snr = q["TH"], q["ZDR"], q["RHOHV"], q["PHIDP"], q["SNR"]
    r = (np.arange(th.shape[1]) + 0.5) * dr
    m = (rho >= 0.95) & (snr >= 10) & (th >= 10) & (th <= 55) & (r >= 3) & (r <= 60)
    for i in range(th.shape[0]):
        idx = np.flatnonzero(m[i])
        if len(idx) < 60 or (idx[-1] - idx[0]) * dr < 3:
            continue
        phi = ph[i, idx]
        med = np.nanmedian(phi)
        ok = np.abs(phi - med) < 90
        idx, phi = idx[ok], phi[ok]
        if len(idx) < 60:
            continue
        phs = median_filter(phi, size=25, mode="nearest")
        phi0 = np.median(phi[:25])
        dphi = np.median(phi[-25:]) - phi0
        acum = np.clip(np.maximum.accumulate(phs) - phi0, 0, None)
        zc = th[i, idx] + ALFA * acum
        integ = np.sum(10 ** (B * zc / 10)) * dr
        fraca = (zc >= 20) & (zc <= 30) & (rho[i, idx] >= 0.97)
        zdr_c = np.median(zdr[i, idx][fraca] + BETA * acum[fraca]) if fraca.sum() >= 10 else np.nan
        yield az[i], dphi, integ, zdr_c, len(idx)


def sensibilidade(arqs, elev=2.4):
    """Menor refletividade detectada por distância (Zmin = TH − SNR, mediana) e percentis de TH, a 2,4° (pouco clutter)."""
    th_, snr_, r_ = [], [], []
    for a in arqs:
        az, dr, q = ler(a)[elev]
        th = q["TH"]
        r = np.broadcast_to((np.arange(th.shape[1]) + 0.5) * dr, th.shape)
        m = np.isfinite(th) & (r > 2.5)
        th_.append(th[m]); snr_.append(q["SNR"][m]); r_.append(r[m])
    th, snr, r = map(np.concatenate, (th_, snr_, r_))
    linhas = [["dist_km", "gates", "th_p1_dbz", "th_p5_dbz", "zmin_dbz", "zmin_reduzido_a_1km_dbz"]]
    for r0 in (3, 5, 10, 20, 30, 40, 60, 80, 100):
        s = (r >= r0) & (r < r0 * 1.15)
        if s.sum() > 100:
            zmin = np.nanmedian(th[s] - snr[s])
            linhas.append([r0, int(s.sum()), f"{np.percentile(th[s], 1):.1f}", f"{np.percentile(th[s], 5):.1f}",
                           f"{zmin:.1f}", f"{zmin - 20 * np.log10(r0):.1f}"])
    with open(AQUI / "relatorio" / "sensibilidade_alcance.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)


def main():
    arqs = sorted(glob.glob(str(AQUI / "amostras" / "ARA" / "*.hdf")))
    print(len(arqs), "volumes")
    sensibilidade(arqs)
    reg = []
    for a in arqs:
        try:
            vol = ler(a)
        except Exception as e:
            print("falhou", Path(a).name, e); continue
        for e, (az, dr, q) in vol.items():
            for azr, dphi, integ, zdr_c, n in raios(az, dr, q):
                reg.append((Path(a).name, e, azr, dphi, integ, zdr_c, n))
    reg = np.array([(e, az, dp, it, zd, n) for _, e, az, dp, it, zd, n in reg], float)
    print(len(reg), "raios com chuva")
    E, AZ, DP, IT, ZD, N = reg.T
    usa = DP >= 4
    logc = np.where(usa, np.log10(np.maximum(DP, 1e-3) / (2 * IT)), np.nan)
    ref = usa & (AZ >= REF[0]) & (AZ <= REF[1]) & (E >= 1.4)
    logc_ref = np.nanmedian(logc[ref])
    zdr_ref = np.nanmedian(ZD[(AZ >= REF[0]) & (AZ <= REF[1]) & (E >= 1.4)])
    print(f"c_ref = {10 ** logc_ref:.3g} ({ref.sum()} raios); ZDR mediano em chuva fraca nos azimutes livres: {zdr_ref:.2f} dB")

    linhas = [["elev", "az_ini", "az_fim", "raios_kdp", "perda_db", "fracao_bloqueada", "raios_zdr", "zdr_mediano_db",
               "zdr_desvio_db"]]
    res = {}
    classes = np.arange(0, 360, PASSO)
    for e in ELEV:
        perda, zd_bin, n_bin = [], [], []
        for a0 in classes:
            s = (E == e) & (AZ >= a0) & (AZ < a0 + PASSO)
            sk = s & usa
            p = (10 / B) * (np.nanmedian(logc[sk]) - logc_ref) if sk.sum() >= 3 else np.nan
            z = np.nanmedian(ZD[s]) if np.isfinite(ZD[s]).sum() >= 3 else np.nan
            perda.append(p); zd_bin.append(z); n_bin.append(int(sk.sum()))
            frac = 1 - 10 ** (-max(p, 0) / 10) if np.isfinite(p) else np.nan
            linhas.append([e, a0, a0 + PASSO, int(sk.sum()), "" if np.isnan(p) else f"{p:.1f}",
                           "" if np.isnan(frac) else f"{frac:.2f}", int(np.isfinite(ZD[s]).sum()),
                           "" if np.isnan(z) else f"{z:.2f}", "" if np.isnan(z) else f"{z - zdr_ref:.2f}"])
        res[e] = (np.array(perda), np.array(zd_bin), np.array(n_bin))
    with open(AQUI / "relatorio" / "polarimetria_azimute.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)

    fig, eixos = plt.subplots(len(ELEV), 2, figsize=(15, 10), sharex=True, dpi=100)
    x = classes + PASSO / 2
    for k, e in enumerate(ELEV):
        perda, zd_bin, n_bin = res[e]
        frac = np.where(np.isfinite(perda), 1 - 10 ** (-np.clip(perda, 0, None) / 10), np.nan)
        ax = eixos[k, 0]
        ax.bar(x, frac * 100, width=PASSO * 0.9, color="#3182bd")
        for xi, ni, fi in zip(x, n_bin, frac):
            if ni and np.isfinite(fi):
                ax.text(xi, min(fi * 100 + 2, 95), str(ni), ha="center", fontsize=6)
        ax.axvspan(*REF, color="0.9", zorder=0)
        ax.set_ylim(0, 100); ax.set_ylabel(f"{e}°: bloqueio por ΦDP (%)")
        ax2 = eixos[k, 1]
        ax2.bar(x, zd_bin - zdr_ref, width=PASSO * 0.9, color="#e6550d")
        ax2.axhline(0, color="k", lw=0.6); ax2.set_ylim(-3, 3)
        ax2.set_ylabel(f"{e}°: ZDR − referência (dB)")
    for ax in eixos[-1]:
        ax.set_xlabel("Azimute (°)"); ax.set_xticks(range(0, 361, 30))
    eixos[0, 0].set_title(f"Perda de potência pela autoconsistência Z–ΦDP (cinza: referência {REF[0]}–{REF[1]}°; número = raios)")
    eixos[0, 1].set_title(f"ZDR em chuva fraca, menos a referência ({zdr_ref:.2f} dB)")
    fig.suptitle(f"Araranguá: bloqueio estimado pelos dados polarimétricos ({len(arqs)} volumes)")
    fig.tight_layout(); fig.savefig(AQUI / "relatorio" / "figuras" / "v3_polarimetria.png"); plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
