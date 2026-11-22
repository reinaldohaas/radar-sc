# -*- coding: utf-8 -*-
"""Procura interferência de rádio (RFI) nos volumes ODIM de Araranguá.

Em banda X (~9,4 GHz), a fonte provável seria radar de navegação de barcos (9,3–9,5 GHz); Wi-Fi (2,4/5/6 GHz)
não entra. A assinatura de interferência é um raio estreito, com eco em quase todo o alcance, inclusive longe
(40–118 km), potência recebida que não cai com a distância (dBZ subindo ~20 dB por década) e vizinhos vazios.

Para cada raio de cada elevação calcula a fração do trecho 40–118 km com TH, compara com os raios a ±3–5°
e marca os candidatos (cobertura ≥ 50%, vizinhos ≤ 25%). Também acompanha o raio de 349,5°, que aparece em
quase todos os volumes a 0,5°.

Uso: python verificar_interferencia.py [pasta_dos_volumes ...]   (padrão: amostras/ARA e cache_vol/ARA)
Saída: relatorio/figuras/interferencia_candidatos.csv e um resumo na tela.
"""
import csv
import re
import sys
from pathlib import Path

import h5py
import numpy as np

AQUI = Path(__file__).resolve().parent
R0, R1 = 40.0, 118.0
AZ_FIXO = 349.5


def _fisico(g):
    at = g["what"].attrs
    b = g["data"][()]
    x = b.astype(np.float32) * float(at["gain"]) + float(at["offset"])
    x[(b == at["nodata"]) | (b == at["undetect"])] = np.nan
    return x


def _txt(v):
    return v.decode() if isinstance(v, bytes) else str(v)


def analisar(arq):
    t = re.search(r"(\d{8}-\d{6})", arq.name).group(1)
    cand, fixo = [], {}
    with h5py.File(arq, "r") as h:
        for k in sorted((k for k in h if k.startswith("dataset")), key=lambda k: int(k[7:])):
            ds = h[k]
            w, how = ds["where"].attrs, (ds["how"].attrs if "how" in ds else {})
            d = {_txt(ds[x]["what"].attrs["quantity"]): ds[x] for x in ds if x.startswith("data")}
            if "TH" not in d:
                continue
            nr = int(w["nrays"])
            if "startazA" in how:
                ini, fim = np.asarray(how["startazA"], float), np.asarray(how["stopazA"], float)
                az = (ini + (fim - ini) % 360 / 2) % 360
            else:
                az = (np.arange(nr) + 0.5) * 360 / nr
            o = np.argsort(az)
            az = az[o]
            r = (np.arange(int(w["nbins"])) + 0.5) * float(w["rscale"]) / 1000
            sel = (r >= R0) & (r <= R1)
            th = _fisico(d["TH"])[o][:, sel]
            rho = _fisico(d["RHOHV"])[o][:, sel] if "RHOHV" in d else np.full_like(th, np.nan)
            cob = np.isfinite(th).mean(1)
            viz = np.array([np.mean([cob[(i + j) % nr] for j in (-5, -4, -3, 3, 4, 5)]) for i in range(nr)])
            ele = round(float(w["elangle"]), 1)
            for i in np.flatnonzero((cob >= 0.5) & (viz <= 0.25)):
                ok = np.isfinite(th[i])
                incl = np.polyfit(np.log10(r[sel][ok]), th[i][ok], 1)[0] if ok.sum() > 10 else np.nan
                cand.append(dict(volume=t, ele=ele, az=round(float(az[i]), 1), cobertura=round(float(cob[i]), 2),
                                 vizinhos=round(float(viz[i]), 2), dbz_por_decada=round(float(incl), 1),
                                 rhohv_mediano=round(float(np.nanmedian(rho[i])), 2)))
            i = int(np.argmin(np.abs(az - AZ_FIXO)))
            todo = _fisico(d["TH"])[o][i]
            fixo[ele] = [np.isfinite(todo[(r >= x) & (r < x + 10)]).mean() for x in range(10, 120, 10)]
    return cand, fixo


def main():
    pastas = [Path(p) for p in sys.argv[1:]] or [AQUI / "amostras" / "ARA", AQUI / "cache_vol" / "ARA"]
    arqs = sorted({a.name: a for p in pastas for a in p.glob("*PPIVol*.hdf")}.values(), key=lambda a: a.name)
    todos, perfis = [], {}
    for a in arqs:
        c, f = analisar(a)
        todos += c
        for e, p in f.items():
            perfis.setdefault(e, []).append(p)
    saida = AQUI / "relatorio" / "figuras" / "interferencia_candidatos.csv"
    with open(saida, "w", newline="", encoding="utf-8") as fh:
        campos = ["volume", "ele", "az", "cobertura", "vizinhos", "dbz_por_decada", "rhohv_mediano"]
        wr = csv.DictWriter(fh, fieldnames=campos)
        wr.writeheader()
        wr.writerows(todos)
    print(f"{len(arqs)} volumes, {len(todos)} raios candidatos -> {saida}")
    rfi = [c for c in todos if c["dbz_por_decada"] >= 15 and c["rhohv_mediano"] < 0.8 and abs(c["az"] - AZ_FIXO) > 3]
    print(f"candidatos com potência constante e RhoHV < 0,8, fora de {AZ_FIXO}°: {len(rfi)}")
    for c in rfi:
        print("  ", c)
    for e, p in sorted(perfis.items())[:2]:
        print(f"raio de {AZ_FIXO}° a {e}°, fração com eco por faixa de 10 km (10–120 km):",
              " ".join(f"{v:.2f}" for v in np.mean(p, 0)))


if __name__ == "__main__":
    main()
