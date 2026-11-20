# -*- coding: utf-8 -*-
"""MDT (ou MDS) de 1 m do SIGSC (aerolevantamento de SC, 2010–2012) como fonte de relevo.

As folhas 1:10.000 (MDT_SH-22-X-B-IV-3-NE-A.tif etc.) ficam no acervo SIGSC do usuário. Em SIRGAS 2000 / UTM 22S.
Para caber na memória, monta:
  - um mosaico de 5 m (máximo de cada bloco 5x5, lado seguro para bloqueio) de todas as folhas da lista;
  - mosaicos de 1 m num raio de `raio_fino_km` em volta de cada posição estudada.
Fora da cobertura, usa o relevo base (SRTM).

Uso:
  python relevo_sigsc.py          # confere alturas em pontos conhecidos
"""
import re
import sys
from pathlib import Path

import numpy as np

ACERVO = Path(r"C:\Users\haas\github\SIGSC\raster\mdt_sigsc")
PADRAO = "MDT_SH-22-X-*.tif"
ACERVO_MDS = Path(r"C:\Users\haas\github\SIGSC\raster\mds_sigsc")   # superfície: terreno + mata + prédios
PADRAO_MDS = "MDS_SH-22-X-*.tif"


def folhas(padrao=PADRAO, acervo=None):
    return sorted((acervo or ACERVO).glob(padrao))


class Mosaico:
    """Mosaico regular em UTM, amostrado por lat/lon (bilinear)."""

    def __init__(self, arquivos, res, limites=None, mediana=False):
        """mediana: filtro mediano 3x3 (1 m) antes de tudo, para tirar picos isolados do MDS (fios, aves, ruído)."""
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.merge import merge
        from pyproj import Transformer
        ds = [rasterio.open(a) for a in arquivos]
        if limites is not None:   # só as folhas que tocam os limites (x0, y0, x1, y1) em UTM
            x0, y0, x1, y1 = limites
            ds = [d for d in ds if not (d.bounds.right < x0 or d.bounds.left > x1 or d.bounds.top < y0 or d.bounds.bottom > y1)]
        if not ds:
            raise ValueError("nenhuma folha na área")
        self.crs = ds[0].crs
        nod = ds[0].nodata
        if res <= 1.5:
            # As folhas não têm nodata declarado e trazem uma moldura de 0 e -9999 nas bordas, que se sobrepõe
            # à folha vizinha (~270 m). Com method="max" o valor real da vizinha prevalece sobre a moldura.
            arr, self.transform = merge(ds, bounds=limites, res=res, nodata=-9999.0 if nod is None else nod,
                                        resampling=Resampling.nearest, dtype="float32", method="max")
            a = arr[0].astype("float32")
            if mediana:
                from scipy.ndimage import median_filter
                a = median_filter(a, size=3)
        else:
            # Máximo em blocos res x res, folha por folha (o rasterio não lê com Resampling.max)
            from rasterio.transform import from_origin
            k = int(round(res / ds[0].res[0]))
            x0 = min(d.bounds.left for d in ds); y1 = max(d.bounds.top for d in ds)
            x1 = max(d.bounds.right for d in ds); y0 = min(d.bounds.bottom for d in ds)
            x0, y1 = res * np.floor(x0 / res), res * np.ceil(y1 / res)
            a = np.full((int(np.ceil((y1 - y0) / res)) + 1, int(np.ceil((x1 - x0) / res)) + 1), np.nan, dtype="float32")
            for d in ds:
                b = d.read(1).astype("float32")
                if mediana:
                    from scipy.ndimage import median_filter
                    b = median_filter(b, size=3)
                if nod is not None:
                    b[b == nod] = np.nan
                h, w = (b.shape[0] // k) * k, (b.shape[1] // k) * k
                m = np.nanmax(b[:h, :w].reshape(h // k, k, w // k, k), axis=(1, 3))
                c0 = int(round((d.bounds.left - x0) / res)); l0 = int(round((y1 - d.bounds.top) / res))
                bloco = a[l0:l0 + m.shape[0], c0:c0 + m.shape[1]]
                a[l0:l0 + m.shape[0], c0:c0 + m.shape[1]] = np.fmax(bloco, m[:bloco.shape[0], :bloco.shape[1]])
            self.transform = from_origin(x0, y1, res, res)
        if nod is not None:
            a[a == nod] = np.nan
        a[a < -100] = np.nan
        self.alt = a
        for d in ds:
            d.close()
        self.inv = ~self.transform
        self.para_xy = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)

    def __call__(self, lat, lon):
        x, y = self.para_xy.transform(np.asarray(lon, float), np.asarray(lat, float))
        c, l = self.inv * (x, y)
        c, l = np.asarray(c) - 0.5, np.asarray(l) - 0.5
        i0, j0 = np.floor(c).astype(int), np.floor(l).astype(int)
        ok = (i0 >= 0) & (j0 >= 0) & (i0 < self.alt.shape[1] - 1) & (j0 < self.alt.shape[0] - 1)
        out = np.full(np.shape(c), np.nan)
        if ok.any():
            i, j = i0[ok], j0[ok]
            fx, fy = c[ok] - i, l[ok] - j
            a = self.alt
            out[ok] = ((a[j, i] * (1 - fx) + a[j, i + 1] * fx) * (1 - fy) + (a[j + 1, i] * (1 - fx) + a[j + 1, i + 1] * fx) * fy)
        return out


class RelevoSIGSC:
    """1 m perto das posições, 5 m no resto das folhas, base (SRTM) fora delas."""

    def __init__(self, base, posicoes=(), raio_fino_km=2.0, res_largo=5.0, padrao=PADRAO, acervo=None, mediana=False):
        from pyproj import Transformer
        arqs = folhas(padrao, acervo)
        if not arqs:
            raise SystemExit(f"Nenhuma folha {padrao} em {acervo or ACERVO}")
        self.base = base
        self.largo = Mosaico(arqs, res_largo, mediana=mediana)
        t = Transformer.from_crs("EPSG:4326", self.largo.crs, always_xy=True)
        self.finos = []
        for la, lo in posicoes:
            x, y = t.transform(lo, la)
            r = raio_fino_km * 1000
            try:
                self.finos.append(Mosaico(arqs, 1.0, limites=(x - r, y - r, x + r, y + r), mediana=mediana))
            except ValueError:
                pass

    def __call__(self, lat, lon, dist_km=None):
        lat, lon = np.asarray(lat, float), np.asarray(lon, float)
        z = np.full(lat.shape, np.nan)
        for m in self.finos + [self.largo]:
            falta = np.isnan(z)
            if not falta.any():
                break
            z[falta] = m(lat[falta], lon[falta])
        falta = np.isnan(z)
        if falta.any():
            d = np.zeros(lat.shape) + 99 if dist_km is None else np.broadcast_to(np.asarray(dist_km, float), lat.shape)
            z[falta] = self.base(lat[falta], lon[falta], d[falta])
        return z


PONTOS = {"radar (antena 49 m)": (-28.934548, -49.362490), "farol (topo 57 m)": (-28.934662, -49.362405),
          "colina (57 m)": (-28.925236, -49.370698), "vila (~10 m)": (-28.922000, -49.363759),
          "proposta (topo Conventos)": (-28.93725, -49.36762), "Morro das Antenas": (-28.843869, -49.398756),
          "centro de Araranguá": (-28.9350, -49.4860)}

if __name__ == "__main__":
    from relevo import Relevo
    arqs = folhas()
    print(f"{len(arqs)} folhas {PADRAO} em {ACERVO}")
    import rasterio
    with rasterio.open(arqs[0]) as d:
        print("exemplo:", arqs[0].name, d.crs, d.res, d.width, "x", d.height, "nodata", d.nodata, d.dtypes[0])
    srtm = Relevo(-28.934548, -49.362490, fino_km=4.0, largo_km=100)
    rel = RelevoSIGSC(srtm, posicoes=[PONTOS["radar (antena 49 m)"]], raio_fino_km=1.0)
    print("mosaico 5 m:", rel.largo.alt.shape, "| fino 1 m:", [m.alt.shape for m in rel.finos])
    for n, (la, lo) in PONTOS.items():
        print(f"  {n:28s} SIGSC {float(rel(la, lo)):7.1f} m   SRTM {float(srtm(la, lo, 0)):7.1f} m")
