# -*- coding: utf-8 -*-
"""Modelo 3D do Morro dos Conventos (SIGSC 1 m) e feixes do radar de Araranguá para o Google Earth.

Gera em kml/:
  morro_conventos_3d.kmz   para o Google Earth Pro: dois modelos COLLADA (terreno MDT e superfície MDS, com mata),
                           radar, torre de 25 m e os feixes de 0,5° e 1,4° coloridos pelo bloqueio simulado;
  feixes_radar_ararangua.kml  só os feixes e o radar (polígonos com altitude absoluta), para o Google Earth Studio,
                           que aceita pontos e polígonos em KML, mas não modelos 3D.

Os modelos ficam em altitude absoluta (metros sobre o nível do mar, SIGSC). O terreno do Google Earth na região fica
~10–20 m abaixo do SIGSC; para ver só o modelo, desligue a camada "Terreno" no Google Earth Pro, ou use --offset.

Uso:
  python gerar_kmz_3d.py              # passo da malha 8 m
  python gerar_kmz_3d.py --passo 5 --offset -12
"""
import argparse
import io
import math
import os
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
from matplotlib import cm, colors
from PIL import Image
from pyproj import Transformer
from scipy.ndimage import maximum_filter, median_filter

from relevo_sigsc import ACERVO_MDS, PADRAO, PADRAO_MDS, PONTOS, Mosaico, folhas
from simular_bloqueio import FEIXE_GRAUS, destino

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "kml"
ATUAL = PONTOS["radar (antena 49 m)"]
LIM = (657400.0, 6796600.0, 660600.0, 6800100.0)   # UTM 22S: Morro dos Conventos, colina e vila
CHAO_RADAR = 67.8
H_ANTENA, H_TORRE = 3.0, 25.0
R_FEIXE = 3000.0   # comprimento dos feixes desenhados (m)


# ----------------------------------------------------------------------------- malha
def grades(passo):
    mds = Mosaico(folhas(PADRAO_MDS, ACERVO_MDS), 1.0, LIM)
    mdt = Mosaico(folhas(PADRAO), 1.0, LIM)
    s = median_filter(mds.alt, size=3)
    t = mdt.alt
    # altura da mata/construções com correção das falésias (ver mapa_altura_superficie.py)
    gy, gx = np.gradient(t)
    decl = np.degrees(np.arctan(np.hypot(gx, gy)))
    d3 = np.hypot(*np.mgrid[-3:4, -3:4]) <= 3
    d15 = np.hypot(*np.mgrid[-15:16, -15:16]) <= 15
    alt = np.where(maximum_filter(decl > 30, footprint=d15), s - maximum_filter(t, footprint=d15),
                   s - maximum_filter(t, footprint=d3))
    k = passo
    ny, nx = (t.shape[0] // k) * k, (t.shape[1] // k) * k
    red = lambda a, f: f(a[:ny, :nx].reshape(ny // k, k, nx // k, k), axis=(1, 3))
    T = red(t, np.nanmean)
    S = red(s, np.nanmax)                 # superfície: o mais alto do bloco (copas)
    A = red(np.clip(alt, 0, None), np.nanmax)
    x0, y1 = mdt.transform.c, mdt.transform.f
    E = x0 + (np.arange(nx // k) + 0.5) * k
    N = y1 - (np.arange(ny // k) + 0.5) * k
    return E, N, T, S, A


def textura(Z, A, com_mata, n=2048):
    """Relevo sombreado em cores hipsométricas; com_mata pinta a vegetação/construções de verde."""
    gy, gx = np.gradient(np.nan_to_num(Z, nan=0.0))
    az, alt = math.radians(315), math.radians(45)
    sl = np.pi / 2 - np.arctan(np.hypot(gx, gy) / 2.0)
    aspect = np.arctan2(-gx, gy)
    hs = np.clip(np.sin(alt) * np.sin(sl) + np.cos(alt) * np.cos(sl) * np.cos(az - aspect), 0, 1)
    agua = ~np.isfinite(Z) | (np.nan_to_num(Z, nan=0) < 0.8)
    base = cm.get_cmap("terrain")(colors.Normalize(-30, 120)(np.nan_to_num(Z, nan=0)))[..., :3]
    base[agua] = (0.55, 0.72, 0.88)
    if com_mata:
        f = np.clip(np.nan_to_num(A, nan=0.0) / 15, 0, 1)[..., None] * (~agua)[..., None]
        base = base * (1 - 0.8 * f) + np.array([0.13, 0.42, 0.16]) * 0.8 * f
    rgb = np.clip(base * (0.45 + 0.55 * hs[..., None]), 0, 1)
    img = Image.fromarray((rgb * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS)
    b = io.BytesIO(); img.save(b, "JPEG", quality=88)
    return b.getvalue()


def collada(E, N, Z, offset, tex_nome, lat0, lon0):
    """Malha triangulada em coordenadas locais (m, leste/norte a partir de lat0/lon0)."""
    para_geo = Transformer.from_crs("EPSG:31982", "EPSG:4326", always_xy=True)
    EE, NN = np.meshgrid(E, N)
    lo, la = para_geo.transform(EE, NN)
    R = 6371008.8
    x = np.radians(lo - lon0) * R * math.cos(math.radians(lat0))
    y = np.radians(la - lat0) * R
    z = np.nan_to_num(Z, nan=0.0) + offset
    ny, nx = Z.shape
    u = np.tile(np.linspace(0, 1, nx), (ny, 1))
    v = np.tile(np.linspace(1, 0, ny)[:, None], (1, nx))
    # normais
    dzx = np.gradient(z, axis=1) / np.gradient(x, axis=1)
    dzy = np.gradient(z, axis=0) / np.gradient(y, axis=0)
    nrm = np.dstack([-dzx, -dzy, np.ones_like(z)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    idx = np.arange(ny * nx).reshape(ny, nx)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel()
    # ordem anti-horária vista de cima (y cresce para o norte; a linha 0 é a do norte)
    tri = np.concatenate([np.stack([a, c, b], 1), np.stack([b, c, d], 1)])
    f = lambda arr, fmt: " ".join(fmt % v for v in arr.ravel())
    pos = f(np.dstack([x, y, z]).reshape(-1, 3), "%.2f")
    nor = f(nrm.reshape(-1, 3), "%.3f")
    uv = f(np.dstack([u, v]).reshape(-1, 2), "%.4f")
    ind = " ".join(map(str, tri.ravel()))
    nv, nt = ny * nx, len(tri)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
 <asset><unit name="meter" meter="1"/><up_axis>Z_UP</up_axis></asset>
 <library_images><image id="img"><init_from>{tex_nome}</init_from></image></library_images>
 <library_effects><effect id="fx"><profile_COMMON>
  <newparam sid="surf"><surface type="2D"><init_from>img</init_from></surface></newparam>
  <newparam sid="samp"><sampler2D><source>surf</source></sampler2D></newparam>
  <technique sid="c"><lambert><diffuse><texture texture="samp" texcoord="UV"/></diffuse></lambert></technique>
 </profile_COMMON><extra><technique profile="GOOGLEEARTH"><double_sided>1</double_sided></technique></extra></effect></library_effects>
 <library_materials><material id="mat"><instance_effect url="#fx"/></material></library_materials>
 <library_geometries><geometry id="g"><mesh>
  <source id="p"><float_array id="pa" count="{nv * 3}">{pos}</float_array>
   <technique_common><accessor source="#pa" count="{nv}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
  <source id="n"><float_array id="na" count="{nv * 3}">{nor}</float_array>
   <technique_common><accessor source="#na" count="{nv}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
  <source id="t"><float_array id="ta" count="{nv * 2}">{uv}</float_array>
   <technique_common><accessor source="#ta" count="{nv}" stride="2"><param name="S" type="float"/><param name="T" type="float"/></accessor></technique_common></source>
  <vertices id="v"><input semantic="POSITION" source="#p"/><input semantic="NORMAL" source="#n"/></vertices>
  <triangles material="m" count="{nt}"><input semantic="VERTEX" source="#v" offset="0"/><input semantic="TEXCOORD" source="#t" offset="0" set="0"/><p>{ind}</p></triangles>
 </mesh></geometry></library_geometries>
 <library_visual_scenes><visual_scene id="s"><node id="morro"><instance_geometry url="#g"><bind_material><technique_common>
  <instance_material symbol="m" target="#mat"><bind_vertex_input semantic="UV" input_semantic="TEXCOORD" input_set="0"/></instance_material>
 </technique_common></bind_material></instance_geometry></node></visual_scene></library_visual_scenes>
 <scene><instance_visual_scene url="#s"/></scene>
</COLLADA>"""


# ----------------------------------------------------------------------------- bloqueio
def bloqueio_por_azimute():
    """PBB a 40 km por azimute (0,5° e 1,4°), antena atual e torre de 25 m, com o MDS (+6 m de mata desde 2012).
    Guardado em dem/pbb_azimute_mds.npz (demora alguns minutos na primeira vez)."""
    cache = AQUI / "dem" / "pbb_azimute_mds.npz"
    if cache.exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    from analise_mds import Nada, Superficie
    from relevo import Relevo
    from relevo_sigsc import RelevoSIGSC
    from simular_bloqueio import perfis, simular
    srtm = Relevo(*ATUAL, fino_km=4.0, largo_km=100)
    mdt = RelevoSIGSC(srtm, posicoes=[ATUAL], raio_fino_km=2.0)
    mds = RelevoSIGSC(Nada(), posicoes=[ATUAL], raio_fino_km=2.0, padrao=PADRAO_MDS, acervo=ACERVO_MDS, mediana=True)
    sup = Superficie(mds, mdt, 6.0)
    az = np.arange(0, 360, 1.0)
    pf = perfis(*ATUAL, sup, az=az, max_km=40)
    out = {"az": az}
    for nome, h in (("atual", H_ANTENA), ("torre", H_TORRE)):
        _, d, r = simular(*ATUAL, CHAO_RADAR + h, sup, elevacoes=(0.5, 1.4), perfis_prontos=pf)
        out[f"{nome}_05"], out[f"{nome}_14"] = r[0.5][:, -1], r[1.4][:, -1]
    np.savez(cache, **out)
    return out


def cor_kml(f, alfa):
    r, g, b, _ = cm.get_cmap("RdYlGn_r")(float(np.clip(f, 0, 1)))
    return f"{int(alfa):02x}{int(b * 255):02x}{int(g * 255):02x}{int(r * 255):02x}"


def feixe_kml(nome, h_antena, elev, pbb, az, visivel, borda=None, ident="", origem=None, alcance=None):
    """Superfície do feixe (centro, ou borda inferior com borda=-1) até R_FEIXE, um quadrilátero por grau."""
    ang = elev + (borda or 0) * FEIXE_GRAUS / 2
    origem = origem or ATUAL
    rs = np.linspace(100.0, alcance or R_FEIXE, 8)
    Re = 8495e3
    h = np.sqrt(rs ** 2 + Re ** 2 + 2 * rs * Re * math.sin(math.radians(ang))) - Re + h_antena
    marcas = []
    for i, a in enumerate(az):
        a0, a1 = a - 0.5, a + 0.5
        ida = [destino(*origem, a0, r) for r in rs]
        volta = [destino(*origem, a1, r) for r in rs[::-1]]
        coords = [(lo, la, hh) for (la, lo), hh in zip(ida, h)] + [(lo, la, hh) for (la, lo), hh in zip(volta, h[::-1])]
        coords.append(coords[0])
        txt = " ".join(f"{lo:.7f},{la:.7f},{hh:.2f}" for lo, la, hh in coords)
        cor = cor_kml(pbb[i], 150) if borda is None else "66aaaaaa"
        marcas.append(f"<Placemark><name>{a:.0f}° ({pbb[i] * 100:.0f}% bloqueado)</name><Style><PolyStyle><color>{cor}</color>"
                      f"<outline>0</outline></PolyStyle></Style><Polygon><altitudeMode>absolute</altitudeMode>"
                      f"<outerBoundaryIs><LinearRing><coordinates>{txt}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>")
    return (f"<Folder{f' id=\"{ident}\"' if ident else ''}><name>{nome}</name><visibility>{int(visivel)}</visibility>"
            f"<open>0</open>{''.join(marcas)}</Folder>")


def elementos_radar(pbb, offset=0.0):
    """offset: o mesmo deslocamento vertical dos modelos, para radar e feixes ficarem no lugar certo sobre eles."""
    az = pbb["az"]
    lat, lon = ATUAL
    CHAO = CHAO_RADAR + offset
    pts = []
    for (rot, h) in (("Antena atual (~3 m acima do chão)", H_ANTENA), ("Antena na torre de 25 m", H_TORRE)):
        pts.append(f"<Placemark><name>{rot}</name><Point><altitudeMode>absolute</altitudeMode><extrude>1</extrude>"
                   f"<coordinates>{lon},{lat},{CHAO + h}</coordinates></Point></Placemark>")
    torre = (f"<Placemark><name>Torre de 25 m</name><Style><LineStyle><color>ff0000ff</color><width>4</width></LineStyle></Style>"
             f"<LineString><altitudeMode>absolute</altitudeMode><coordinates>{lon},{lat},{CHAO} {lon},{lat},{CHAO + H_TORRE}"
             f"</coordinates></LineString></Placemark>")
    pastas = [
        feixe_kml("Feixe 0,5° — centro (antena atual; cor = bloqueio a 40 km)", CHAO + H_ANTENA, 0.5, pbb["atual_05"], az, True, ident="f05c"),
        feixe_kml("Feixe 0,5° — borda inferior (−0,6°)", CHAO + H_ANTENA, 0.5, pbb["atual_05"], az, True, borda=-1, ident="f05b"),
        feixe_kml("Feixe 1,4° — centro (antena atual)", CHAO + H_ANTENA, 1.4, pbb["atual_14"], az, False, ident="f14c"),
        feixe_kml("Feixe 1,4° — borda inferior (+0,3°)", CHAO + H_ANTENA, 1.4, pbb["atual_14"], az, False, borda=-1, ident="f14b"),
        feixe_kml("Torre 25 m: feixe 0,5° — centro", CHAO + H_TORRE, 0.5, pbb["torre_05"], az, False, ident="t05c"),
        feixe_kml("Torre 25 m: feixe 0,5° — borda inferior", CHAO + H_TORRE, 0.5, pbb["torre_05"], az, False, borda=-1, ident="t05b"),
    ]
    return "".join(pts) + torre + "".join(pastas) + propostas_e_obstaculos(offset)


def propostas_e_obstaculos(offset):
    """Posições propostas (com os feixes de 0,5° e 1,4° coloridos pelo bloqueio a 30 km) e obstáculos medidos."""
    cache = AQUI / "dem" / "pbb_posicoes_mds.npz"
    if not cache.exists():
        return ""
    from posicoes_obstaculos import OBSTACULOS, POSICOES
    d = np.load(cache)
    az = d["az"]
    nomes = list(POSICOES)
    pastas = []
    for k in (1, 2):
        la, lo, h = POSICOES[nomes[k]]
        chao = float(d[f"p{k}_chao"]) + offset
        corpo = (f"<Placemark><name>{nomes[k]}</name><Point><altitudeMode>absolute</altitudeMode><extrude>1</extrude>"
                 f"<coordinates>{lo},{la},{chao + h}</coordinates></Point></Placemark>"
                 + feixe_kml("Feixe 0,5° — centro (cor = bloqueio a 30 km)", chao + h, 0.5, d[f"p{k}_05_30"], az, True,
                             ident=f"p{k}05c", origem=(la, lo), alcance=5000)
                 + feixe_kml("Feixe 0,5° — borda inferior", chao + h, 0.5, d[f"p{k}_05_30"], az, False, borda=-1,
                             ident=f"p{k}05b", origem=(la, lo), alcance=5000)
                 + feixe_kml("Feixe 1,4° — centro", chao + h, 1.4, d[f"p{k}_14_30"], az, False,
                             ident=f"p{k}14c", origem=(la, lo), alcance=5000))
        pastas.append(f"<Folder><name>{nomes[k]}</name><visibility>0</visibility>{corpo}</Folder>")
    obs = []
    for n, la, lo, h, txt in OBSTACULOS:
        if la is None:
            continue
        obs.append(f"<Placemark><name>{n}</name><description>{txt}</description><Style><IconStyle><color>ffff00aa</color>"
                   f"</IconStyle></Style><Point><coordinates>{lo},{la},0</coordinates></Point></Placemark>")
    return (f"<Folder><name>Posições propostas</name>{''.join(pastas)}</Folder>"
            f"<Folder><name>Obstáculos</name>{''.join(obs)}</Folder>")


def tour(offset):
    """gx:Tour para o Google Earth Pro: visão geral, aproximação do radar, órbita, feixe de 1,4°, torre de 25 m."""
    lat, lon = ATUAL
    alt = CHAO_RADAR + offset

    def voo(dur, h, tilt, rng, la=lat, lo=lon, a=None, modo="smooth"):
        return (f"<gx:FlyTo><gx:duration>{dur}</gx:duration><gx:flyToMode>{modo}</gx:flyToMode><LookAt>"
                f"<longitude>{lo}</longitude><latitude>{la}</latitude><altitude>{a if a is not None else alt}</altitude>"
                f"<heading>{h}</heading><tilt>{tilt}</tilt><range>{rng}</range><altitudeMode>absolute</altitudeMode></LookAt></gx:FlyTo>")

    def vis(pares, dur=1.5):
        ups = "".join(f'<Change><Folder targetId="{i}"><visibility>{v}</visibility></Folder></Change>' for i, v in pares)
        return (f"<gx:AnimatedUpdate><gx:duration>{dur}</gx:duration><Update><targetHref/>{ups}</Update></gx:AnimatedUpdate>"
                f"<gx:Wait><gx:duration>{dur}</gx:duration></gx:Wait>")

    pausa = lambda d: f"<gx:Wait><gx:duration>{d}</gx:duration></gx:Wait>"
    passos = [vis([("f05c", 1), ("f05b", 1), ("f14c", 0), ("f14b", 0), ("t05c", 0), ("t05b", 0)], 0.1),
              voo(1, 320, 60, 6000, lat - 0.02, lon + 0.02, 0, "bounce"), pausa(2),
              voo(6, 300, 72, 1800), pausa(2),
              voo(5, 250, 80, 700), pausa(2)]
    for h in range(250, 250 + 361, 30):           # órbita em volta da antena
        passos.append(voo(2.5, h % 360, 78, 900))
    passos += [pausa(1), vis([("f05c", 0), ("f05b", 0), ("f14c", 1), ("f14b", 1)]), voo(5, 290, 75, 1200), pausa(3),
               vis([("f14c", 0), ("f14b", 0), ("t05c", 1), ("t05b", 1)]), voo(5, 300, 78, 900), pausa(3),
               voo(8, 320, 65, 5000, lat - 0.015, lon + 0.015, 0), pausa(2)]
    return (f"<gx:Tour><name>Tour: o feixe do radar e a mata do Morro dos Conventos</name><gx:Playlist>{''.join(passos)}"
            f"</gx:Playlist></gx:Tour>")


def kml(corpo, nome):
    return (f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2"><Document><name>{nome}</name>'
            f"<LookAt><longitude>{ATUAL[1] - 0.004}</longitude><latitude>{ATUAL[0] - 0.012}</latitude><altitude>0</altitude>"
            f"<heading>330</heading><tilt>70</tilt><range>3500</range></LookAt>{corpo}</Document></kml>")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passo", type=int, default=8, help="passo da malha (m)")
    ap.add_argument("--offset", type=float, default=0.0, help="soma à altitude dos modelos (m)")
    a = ap.parse_args()
    SAIDA.mkdir(exist_ok=True)
    print("lendo MDT e MDS...", flush=True)
    E, N, T, S, A = grades(a.passo)
    print("malha", T.shape, flush=True)
    para_geo = Transformer.from_crs("EPSG:31982", "EPSG:4326", always_xy=True)
    lon0, lat0 = para_geo.transform(E[0], N[-1])
    print("bloqueio por azimute...", flush=True)
    pbb = bloqueio_por_azimute()

    modelos = []
    arquivos = {}
    for nome, Z, mata, vis in (("terreno_mdt", T, False, 0), ("superficie_mds", S, True, 1)):
        arquivos[f"modelos/{nome}.jpg"] = textura(Z, A, mata)
        arquivos[f"modelos/{nome}.dae"] = collada(E, N, Z, a.offset, f"{nome}.jpg", lat0, lon0).encode()
        rot = "Terreno SIGSC (MDT 1 m, sem mata)" if nome == "terreno_mdt" else "Superfície SIGSC (MDS 1 m: terreno + mata + construções, 2010–2012)"
        modelos.append(f"<Placemark><name>{rot}</name><visibility>{vis}</visibility><Model><altitudeMode>absolute</altitudeMode>"
                       f"<Location><longitude>{lon0}</longitude><latitude>{lat0}</latitude><altitude>0</altitude></Location>"
                       f"<Orientation><heading>0</heading><tilt>0</tilt><roll>0</roll></Orientation>"
                       f"<Scale><x>1</x><y>1</y><z>1</z></Scale><Link><href>modelos/{nome}.dae</href></Link></Model></Placemark>")
    leia = ("<description><![CDATA[Modelo 3D do Morro dos Conventos a partir do MDT/MDS de 1 m do SIGSC (malha de "
            f"{a.passo} m), em altitude absoluta. O terreno do Google Earth aqui fica ~10–20 m abaixo do SIGSC: para ver só o "
            "modelo, desligue a camada Terreno (Google Earth Pro: painel Camadas). Feixes: cor = fração bloqueada a 40 km "
            "(verde 0%, vermelho 100%), simulada com o MDS + 6 m de mata.]]></description>")
    corpo = leia + f"<Folder><name>Modelos 3D (SIGSC)</name><open>1</open>{''.join(modelos)}</Folder>" + elementos_radar(pbb, a.offset) + tour(a.offset)
    destino_kmz = SAIDA / "morro_conventos_3d.kmz"
    with zipfile.ZipFile(destino_kmz, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("doc.kml", kml(corpo, "Radar de Araranguá — Morro dos Conventos 3D"))
        for k, v in arquivos.items():
            z.writestr(k, v)
    (SAIDA / "feixes_radar_ararangua.kml").write_text(kml(elementos_radar(pbb, a.offset), "Radar de Araranguá — feixes"), encoding="utf-8")
    print(destino_kmz, f"{os.path.getsize(destino_kmz) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
