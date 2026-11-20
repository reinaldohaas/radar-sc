# -*- coding: utf-8 -*-
"""Simula o bloqueio do feixe pelo relevo (PBB, partial beam blockage) para uma posição de radar.

Método (Bech et al., 2003, J. Atmos. Oceanic Technol. 20, 845–855):
  - Terra com raio efetivo 4/3 (8495 km);
  - feixe de seção circular com diâmetro igual à largura a meia potência;
  - em cada raio, a fração bloqueada à distância r é a maior fração encontrada até r (o bloqueio se acumula).
Obstáculos acima do relevo (árvores, casas) entram como uma altura somada ao terreno em terra firme.

Uso como módulo: pbb = simular(lat, lon, h_antena_m, relevo, elevacoes=(0.5, 1.4, 2.4))
"""
import math

import numpy as np

R_EF = 8495e3
FEIXE_GRAUS = 2.2


def destino(lat, lon, az_graus, d_m):
    """Ponto a d_m no azimute az (grande círculo, esfera)."""
    R = 6371e3
    la, lo, az = map(np.radians, (lat, lon, az_graus))
    dd = np.asarray(d_m) / R
    la2 = np.arcsin(np.sin(la) * np.cos(dd) + np.cos(la) * np.sin(dd) * np.cos(az))
    lo2 = lo + np.arctan2(np.sin(az) * np.sin(dd) * np.cos(la), np.cos(dd) - np.sin(la) * np.sin(la2))
    return np.degrees(la2), np.degrees(lo2)


D_MIN = 100.0  # até ~60–100 m o SRTM (30 m) não representa o entorno e o feixe ainda está em campo próximo


def distancias(max_km=80.0, d_min=D_MIN):
    """Passo de 10 m até 2 km, 30 m até 10 km e 100 m depois, a partir de d_min."""
    d = np.r_[np.arange(10, 2000, 10), np.arange(2000, 10000, 30), np.arange(10000, max_km * 1000 + 1, 100)].astype(float)
    return d[d >= d_min]


def fracao_bloqueada(y):
    """Fração da área de um círculo de raio 1 abaixo da corda a y raios do centro (y em [-1, 1])."""
    y = np.clip(y, -1, 1)
    return (y * np.sqrt(1 - y ** 2) + np.arcsin(y) + math.pi / 2) / math.pi


def perfis(lat, lon, relevo, az=np.arange(0, 360, 0.5), max_km=80.0, obst_m=0.0, agua_m=1.0, d_min=D_MIN):
    """Altitude do terreno (+ obstáculos em terra) em cada (azimute, distância)."""
    d = distancias(max_km, d_min)
    A, D = np.meshgrid(az, d, indexing="ij")
    la, lo = destino(lat, lon, A, D)
    z = relevo(la, lo, D / 1000)
    if obst_m:
        z = np.where(z > agua_m, z + obst_m, z)
    return az, d, z


def simular(lat, lon, h_antena, relevo, elevacoes=(0.5, 1.4, 2.4), az=np.arange(0, 360, 0.5), max_km=80.0,
            obst_m=0.0, perfis_prontos=None):
    """Devolve (az, d, {elev: PBB[az, d]}) com PBB acumulado ao longo do raio, entre 0 e 1."""
    az, d, z = perfis_prontos or perfis(lat, lon, relevo, az, max_km, obst_m)
    out = {}
    for e in elevacoes:
        er = math.radians(e)
        # altura do centro do feixe acima do mar (Terra 4/3)
        hc = np.sqrt(d ** 2 + R_EF ** 2 + 2 * d * R_EF * math.sin(er)) - R_EF + h_antena
        raio = d * math.tan(math.radians(FEIXE_GRAUS / 2))
        y = (z - hc[None, :]) / raio[None, :]
        out[e] = np.maximum.accumulate(fracao_bloqueada(y), axis=1)
    return az, d, out


def resumo(az, d, pbb, ate_km=60.0, limiar=0.5):
    """Fração dos azimutes com PBB >= limiar a ate_km."""
    i = np.searchsorted(d, ate_km * 1000) - 1
    return {e: float(np.mean(p[:, i] >= limiar)) for e, p in pbb.items()}
