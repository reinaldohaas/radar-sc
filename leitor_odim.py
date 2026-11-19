# -*- coding: utf-8 -*-
"""Leitor de volumes ODIM_H5 (PVOL), como os do radar de Araranguá (EEC Ranger, arquivos *-PPIVol-*.hdf).

Devolve o mesmo dicionário de leitor_vol.ler_volume_rainbow: lat0, lon0, alt0 e slices com
ele_deg, azimuths (ordenados), ranges_km e data (valores físicos, NaN fora de eco).
"""
from pathlib import Path

import numpy as np

PREFERIDAS = ("DBZH", "TH")  # refletividade corrigida, depois a total


def _txt(v):
    return v.decode() if isinstance(v, bytes) else str(v)


RHOHV_MIN = 0.8


def _fisico(g):
    at = g["what"].attrs
    bruto = g["data"][()]
    fis = bruto.astype(np.float32) * float(at["gain"]) + float(at["offset"])
    fis[(bruto == at["nodata"]) | (bruto == at["undetect"])] = np.nan
    return fis


def ler_volume_odim(caminho, quantidades=PREFERIDAS, th_rhohv=True):
    """th_rhohv=True: usa a refletividade bruta (TH) e retira os gates com RhoHV < 0,8.

    Em Araranguá, o filtro de clutter Doppler que gera o DBZH apaga raios inteiros de chuva, porque a PRF
    baixa (400/267 Hz em banda X) deixa a velocidade e o SQI sem sentido. O RhoHV não depende do Doppler:
    retira mar, relevo e ruído (RhoHV baixo) e mantém a chuva (RhoHV ~0,95–1).
    """
    import h5py
    with h5py.File(Path(caminho), "r") as h:
        onde = h["where"].attrs
        lat0, lon0, alt0 = float(onde["lat"]), float(onde["lon"]), float(onde["height"])
        fatias = []
        for nome in sorted((k for k in h if k.startswith("dataset")), key=lambda k: int(k[7:])):
            ds = h[nome]
            w = ds["where"].attrs
            dados = {_txt(ds[d]["what"].attrs["quantity"]): ds[d] for d in ds if d.startswith("data")}
            if th_rhohv and "TH" in dados and "RHOHV" in dados:
                q = f"TH, RhoHV ≥ {RHOHV_MIN:.1f}"
                fis = _fisico(dados["TH"])
                rho = _fisico(dados["RHOHV"])
                fis[~(rho >= RHOHV_MIN)] = np.nan
            else:
                q = next((q for q in quantidades if q in dados), None)
                if q is None:
                    continue
                fis = _fisico(dados[q])

            nr = int(w["nrays"])
            how = ds["how"].attrs if "how" in ds else {}
            if "startazA" in how and "stopazA" in how:
                ini, fim = np.asarray(how["startazA"], float), np.asarray(how["stopazA"], float)
                az = (ini + (fim - ini) % 360 / 2) % 360   # centro do raio, tratando a passagem por 0°
            else:
                az = (np.arange(nr) + 0.5) * 360.0 / nr
            ordem = np.argsort(az)
            rscale_km = float(w["rscale"]) / 1000.0
            ranges = float(w.get("rstart", 0.0)) + (np.arange(int(w["nbins"]), dtype=np.float32) + 0.5) * rscale_km
            fatias.append({"ele_deg": float(w["elangle"]), "azimuths": az[ordem], "ranges_km": ranges,
                           "data": fis[ordem], "quantity": q})
    return {"lat0": lat0, "lon0": lon0, "alt0": alt0, "slices": fatias}
