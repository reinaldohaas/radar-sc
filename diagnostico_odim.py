# -*- coding: utf-8 -*-
"""Diagnóstico de um volume ODIM_H5 (ex.: Araranguá): o que é chuva, clutter, mar ou interferência?

Para cada elevação, nos gates com eco (DBZH >= 10 dBZ):
  - quanto o filtro de clutter removeu (TH com eco e DBZH sem);
  - fração com RhoHV < 0,8 (alvo não meteorológico), |V| < 1 m/s (alvo parado) e SQI baixo;
  - raios "riscados": eco em fração grande do alcance, típico de interferência ou sol;
  - eco por faixa de distância.
Gera também um painel com TH, DBZH, VRAD, RHOHV, SQI e SNR da elevação mais baixa.

Uso:
  python diagnostico_odim.py cache_vol/ARA/<arquivo>.hdf [saida.png]
"""
import sys
from pathlib import Path

import h5py
import numpy as np


def campos(ds):
    out = {}
    for d in ds:
        if not d.startswith("data"):
            continue
        a = ds[d]["what"].attrs
        q = a["quantity"].decode() if isinstance(a["quantity"], bytes) else str(a["quantity"])
        bruto = ds[d]["data"][()]
        v = bruto.astype(np.float32) * float(a["gain"]) + float(a["offset"])
        v[(bruto == a["nodata"]) | (bruto == a["undetect"])] = np.nan
        out[q] = v
    return out


def pct(x):
    return f"{100 * x:5.1f}%"


def main():
    arq = Path(sys.argv[1])
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else arq.with_suffix(".diagnostico.png")
    with h5py.File(arq, "r") as h:
        print(f"Arquivo: {arq.name}")
        how = h["how"].attrs
        print(f"Sistema: {how.get('system', b'').decode() if isinstance(how.get('system'), bytes) else how.get('system')}, "
              f"λ = {float(how['wavelength']):.2f} cm, feixe {float(how['beamwH']):.2f}°, ganho {float(how['antgain']):.1f} dB")
        fatias = sorted((k for k in h if k.startswith("dataset")), key=lambda k: int(k[7:]))
        painel = None
        for k in fatias:
            ds = h[k]
            w, hw = ds["where"].attrs, ds["how"].attrs
            c = campos(ds)
            rs = float(w["rscale"]) / 1000
            nb = int(w["nbins"])
            r = (np.arange(nb) + 0.5) * rs
            th, dbz = c.get("TH"), c.get("DBZH")
            eco = dbz >= 10 if dbz is not None else np.zeros((1, 1), bool)
            n = eco.sum()
            print(f"\n{k}: elevação {float(w['elangle']):.1f}°, PRF {float(hw['highprf']):.0f}/{float(hw['lowprf']):.0f} Hz, "
                  f"Nyquist {float(hw['NI']):.2f} m/s, pulso {float(hw['pulsewidth'])}, {float(hw['rpm']):.2f} rpm, "
                  f"limiares SQI={hw.get('SQI')} CSR={hw.get('CSR')} LOG={hw.get('LOG')}")
            if th is not None and dbz is not None:
                th_eco = th >= 10
                removido = (th_eco & ~eco).sum() / max(th_eco.sum(), 1)
                print(f"  gates com eco: TH {th_eco.sum()}  DBZH {n}  -> filtro removeu {pct(removido)} do eco bruto")
            if n == 0:
                continue
            for nome, teste in (("RhoHV < 0,80", lambda: c["RHOHV"] < 0.8),
                                ("|V| < 1 m/s", lambda: np.abs(c["VRAD"]) < 1.0),
                                ("SQI < 0,4", lambda: c["SQI"] < 0.4),
                                ("SNR < 5 dB", lambda: c["SNR"] < 5)):
                try:
                    m = teste() & eco
                    print(f"  {nome:13s}: {pct(m.sum() / n)} dos gates com eco")
                except KeyError:
                    pass
            # Raios riscados: eco contínuo ao longo do raio
            frac_raio = eco.sum(axis=1) / nb
            riscos = np.where(frac_raio > 0.25)[0]
            if len(riscos):
                az = np.asarray(hw["startazA"], float)
                print(f"  raios com eco em >25% do alcance: {len(riscos)}; azimutes ~ "
                      f"{', '.join(f'{az[i]:.0f}°' for i in riscos[:15])}")
            faixas = [(0, 10), (10, 30), (30, 60), (60, 90), (90, 121)]
            txt = []
            for a0, a1 in faixas:
                sel = (r >= a0) & (r < a1)
                txt.append(f"{a0}-{a1} km {pct(eco[:, sel].mean())}")
            print("  cobertura de eco por distância: " + " | ".join(txt))
            # Eco isolado (speckle): gate com eco sem vizinho com eco
            viz = np.zeros_like(eco)
            viz[:, 1:] |= eco[:, :-1]; viz[:, :-1] |= eco[:, 1:]
            viz[1:, :] |= eco[:-1, :]; viz[:-1, :] |= eco[1:, :]
            print(f"  gates com eco isolados (sem vizinho): {pct((eco & ~viz).sum() / n)}")
            if painel is None:
                painel = (float(w["elangle"]), c, np.asarray(hw["startazA"], float), r)

    if painel:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ele, c, az, r = painel
        ordem = np.argsort(az)
        A, R = np.meshgrid(np.deg2rad(az[ordem]), r, indexing="ij")
        X, Y = R * np.sin(A), R * np.cos(A)
        passo = max(1, len(r) // 1200)
        specs = [("TH", "TH (bruto, dBZ)", "turbo", 0, 70), ("DBZH", "DBZH (filtrado, dBZ)", "turbo", 0, 70),
                 ("VRAD", "VRAD (m/s)", "RdBu_r", -7, 7), ("RHOHV", "RhoHV", "viridis", 0.5, 1.0),
                 ("SQI", "SQI", "magma", 0, 1), ("SNR", "SNR (dB)", "magma", 0, 40)]
        fig, eixos = plt.subplots(2, 3, figsize=(16, 11), dpi=90)
        for ax, (q, tit, cmap, v0, v1) in zip(eixos.flat, specs):
            if q in c:
                m = ax.pcolormesh(X[:, ::passo], Y[:, ::passo], np.ma.masked_invalid(c[q][ordem][:, ::passo]),
                                  cmap=cmap, vmin=v0, vmax=v1, shading="auto")
                fig.colorbar(m, ax=ax, shrink=0.8)
            ax.set_title(tit); ax.set_aspect("equal"); ax.set_xlabel("km leste"); ax.set_ylabel("km norte")
            for rr in (30, 60, 90, 120):
                t = np.linspace(0, 2 * np.pi, 200)
                ax.plot(rr * np.sin(t), rr * np.cos(t), color="gray", lw=0.4)
        fig.suptitle(f"{arq.name} · elevação {ele:.1f}°")
        fig.tight_layout()
        fig.savefig(saida)
        print(f"\nPainel: {saida}")


if __name__ == "__main__":
    main()
