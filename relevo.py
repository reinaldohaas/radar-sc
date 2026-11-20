# -*- coding: utf-8 -*-
"""Modelo de relevo a partir dos tiles públicos Terrarium (AWS elevation-tiles-prod; no Brasil a fonte é o SRTM de 30 m).

Monta dois mosaicos em volta de um ponto: um fino (zoom 14, ~8 m/pixel, interpolado do SRTM) para os primeiros km
e um largo (zoom 11, ~67 m/pixel) até ~80 km. Os tiles ficam em cache em dem/ (fora do git).

Limitação: o SRTM é um modelo de superfície de radar de 2000, com resolução de 30 m. Inclui parte da copa das árvores
e dos prédios, mas não postes, mastros, antenas nem árvores isoladas.
"""
import math
import urllib.request
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

CACHE = Path(__file__).resolve().parent / "dem"
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def _tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * n
    return x, y


def _tile(z, x, y):
    arq = CACHE / str(z) / f"{x}_{y}.png"
    if not arq.exists():
        arq.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "radar-sc"})
        arq.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    rgb = np.asarray(Image.open(arq).convert("RGB"), dtype=np.float64)
    return rgb[..., 0] * 256 + rgb[..., 1] + rgb[..., 2] / 256 - 32768


class Mosaico:
    """Grade de altitude (m) com amostragem bilinear por lat/lon."""

    def __init__(self, lat, lon, raio_km, z):
        self.z = z
        cx, cy = _tile_xy(lat, lon, z)
        tam_km = 40075.016 * math.cos(math.radians(lat)) / 2 ** z
        k = int(math.ceil(raio_km / tam_km)) + 1
        self.x0, self.y0 = int(cx) - k, int(cy) - k
        lado = 2 * k + 1
        self.alt = np.zeros((lado * 256, lado * 256))
        for j in range(lado):
            for i in range(lado):
                self.alt[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = _tile(z, self.x0 + i, self.y0 + j)
        # Picos e buracos isolados (defeitos do SRTM): pixel 30 m acima de todos os 8 vizinhos, ou abaixo de todos.
        # Encostas íngremes reais (escarpa da Serra Geral) não são alteradas.
        from scipy.ndimage import maximum_filter, median_filter, minimum_filter
        anel = np.ones((3, 3), bool); anel[1, 1] = False
        viz_max = maximum_filter(self.alt, footprint=anel, mode="nearest")
        viz_min = minimum_filter(self.alt, footprint=anel, mode="nearest")
        ruim = (self.alt > viz_max + 30) | (self.alt < viz_min - 30)
        self.picos = int(ruim.sum())
        self.alt = np.where(ruim, median_filter(self.alt, size=3), self.alt)

    def contem(self, lat, lon, margem_px=2):
        x, y = _tile_xy(np.asarray(lat), np.asarray(lon), self.z)
        px, py = (x - self.x0) * 256, (y - self.y0) * 256
        n = self.alt.shape[0]
        return (px >= margem_px) & (px <= n - margem_px) & (py >= margem_px) & (py <= n - margem_px)

    def __call__(self, lat, lon):
        x, y = _tile_xy(np.asarray(lat), np.asarray(lon), self.z)
        px = (x - self.x0) * 256 - 0.5
        py = (y - self.y0) * 256 - 0.5
        i0 = np.clip(np.floor(px).astype(int), 0, self.alt.shape[1] - 2)
        j0 = np.clip(np.floor(py).astype(int), 0, self.alt.shape[0] - 2)
        fx, fy = np.clip(px - i0, 0, 1), np.clip(py - j0, 0, 1)
        a = self.alt
        return ((a[j0, i0] * (1 - fx) + a[j0, i0 + 1] * fx) * (1 - fy)
                + (a[j0 + 1, i0] * (1 - fx) + a[j0 + 1, i0 + 1] * fx) * fy)


class Relevo:
    """Fino até `fino_km`, largo depois."""

    def __init__(self, lat, lon, fino_km=4.0, largo_km=80.0):
        self.fino_km = fino_km
        self.fino = Mosaico(lat, lon, fino_km + 1, 14)
        self.largo = Mosaico(lat, lon, largo_km + 2, 11)
        self.lat, self.lon = lat, lon

    def __call__(self, lat, lon, dist_km):
        usar_fino = (np.asarray(dist_km) <= self.fino_km) & self.fino.contem(lat, lon)
        return np.where(usar_fino, self.fino(lat, lon), self.largo(lat, lon))
