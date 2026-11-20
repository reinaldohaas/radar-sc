# -*- coding: utf-8 -*-
"""KML para conferir no Google Earth o bloqueio do radar de Araranguá no setor 320–325°.

Camadas:
  - radar (coordenadas do arquivo ODIM) e Farol do Morro dos Conventos (OpenStreetMap, node 1181497480);
  - setor bloqueado 320–325° em duas escalas: 150 m (para ver o farol) e 5 km;
  - linha "onde o radar teria de estar": se o farol bloqueia a 322,5°, o radar está a 142,5° do farol;
  - zona cega de 2,2 km.

Uso:
  python gerar_kml_bloqueio.py            # grava kml/ararangua_bloqueio.kml
"""
import math
from pathlib import Path

RADAR_ODIM = (-28.9346, -49.3627)     # where/lat, where/lon do arquivo ODIM (21 m da posição real)
RADAR = (-28.934548, -49.362490)      # posição real informada; antena a 49 m
ANTENA_M = 49.0
FAROL = (-28.934662, -49.362405)      # posição informada; topo a 57 m (8 m acima da antena)
OBSTACULO = (-28.925104, -49.370708)  # colina de 57 m (obstaculo.kmz, Google Earth)
SETOR = (321.0, 324.0)                # bloqueio total de 0,5° a 3,4°; parcial a 4,5°
TOPO_GRAUS = 4.5                      # elevação aproximada do topo do obstáculo, vista da antena
SETOR_NORTE = (352.0, 356.0)          # queda a 0,5° e bloqueio a 1,4°
ZONA_CEGA_KM = 2.2


def destino(lat, lon, az, d_m):
    """Ponto a d_m metros no azimute az (aproximação local, suficiente para poucos km)."""
    dlat = d_m * math.cos(math.radians(az)) / 111_130
    dlon = d_m * math.sin(math.radians(az)) / (111_320 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def coords(pontos):
    return " ".join(f"{lon:.7f},{lat:.7f},0" for lat, lon in pontos)


def cunha(centro, az0, az1, raio_m, passo=0.5):
    pts = [centro] + [destino(*centro, az0 + i * passo, raio_m) for i in range(int((az1 - az0) / passo) + 1)] + [centro]
    return coords(pts)


def circulo(centro, raio_m):
    return coords([destino(*centro, a, raio_m) for a in range(0, 361, 2)])


def placemark(nome, desc, estilo, geom):
    return f"<Placemark><name>{nome}</name><description><![CDATA[{desc}]]></description><styleUrl>#{estilo}</styleUrl>{geom}</Placemark>"


def main():
    def rel(p):
        dy = (p[0] - RADAR[0]) * 111_130
        dx = (p[1] - RADAR[1]) * 111_320 * math.cos(math.radians(RADAR[0]))
        return math.hypot(dx, dy), math.degrees(math.atan2(dx, dy)) % 360
    d_f, az_f = rel(FAROL)
    d_o, az_o = rel(OBSTACULO)
    d_odim, _ = rel(RADAR_ODIM)
    meio = sum(SETOR) / 2
    ponto = lambda la, lo: f"<Point><coordinates>{lo},{la},0</coordinates></Point>"
    itens = [
        placemark("Radar (posição real)", f"{RADAR[0]}, {RADAR[1]}; antena a {ANTENA_M:.0f} m.", "radar", ponto(*RADAR)),
        placemark("Radar (coordenadas do arquivo ODIM)", f"{RADAR_ODIM[0]}, {RADAR_ODIM[1]}: a {d_odim:.0f} m da posição real.",
                  "odim", ponto(*RADAR_ODIM)),
        placemark("Farol do Morro dos Conventos", f"Topo a 57 m (8 m acima da antena).<br>Do radar: azimute {az_f:.1f}°, {d_f:.0f} m, "
                  f"topo a {math.degrees(math.atan2(8, d_f)):.0f}° de elevação.<br>Nos dados, a 0,5° o eco cai a zero a partir de 146°.",
                  "farol", ponto(*FAROL)),
        placemark("Colina de 57 m", f"Do radar: azimute {az_o:.1f}° (no meio do setor bloqueado), {d_o:.0f} m, topo a "
                  f"{math.degrees(math.atan2(57 - ANTENA_M, d_o)):.2f}° de elevação.<br>Tira ~43% do feixe de 0,5° (−2,5 dB), "
                  f"~13% do de 1,4° e nada acima.<br>Não explica a perda total de 0,5° a 3,4°: para isso o topo teria de chegar a ~150 m.",
                  "obst", ponto(*OBSTACULO)),
        placemark("Zona de campo próximo da antena (~60 m)",
                  "Antena de ~1 m (feixe de 2,2° em banda X): até 2D²/λ ≈ 60 m, um objeto do tamanho da antena sombreia o feixe inteiro.<br>"
                  "O transmissor funciona no setor (o anel de vazamento em 2,14 km continua), então o bloqueio é físico.",
                  "cega", f"<LineString><tessellate>1</tessellate><coordinates>{circulo(RADAR, 60)}</coordinates></LineString>"),
        placemark(f"Setor bloqueado {SETOR[0]:.0f}–{SETOR[1]:.0f}° (1,5 km)",
                  f"Sem eco de 0,5° a 3,4° de elevação nos 7 horários; perda parcial a 4,5°.<br>Topo do obstáculo ~{TOPO_GRAUS}° acima da antena.",
                  "setor", f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{cunha(RADAR, *SETOR, 1500)}"
                           f"</coordinates></LinearRing></outerBoundaryIs></Polygon>"),
        placemark(f"Setor bloqueado {SETOR[0]:.0f}–{SETOR[1]:.0f}° (5 km)", "Mesmo setor, até 5 km.",
                  "setor_longe", f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{cunha(RADAR, *SETOR, 5000)}"
                                 f"</coordinates></LinearRing></outerBoundaryIs></Polygon>"),
        placemark(f"Setor {SETOR_NORTE[0]:.0f}–{SETOR_NORTE[1]:.0f}° (perda a 0,5° e 1,4°)", "Obstáculo mais baixo: não afeta 2,4° e acima.",
                  "setor_norte", f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{cunha(RADAR, *SETOR_NORTE, 2000)}"
                                 f"</coordinates></LinearRing></outerBoundaryIs></Polygon>"),
        placemark("Zona cega (2,2 km)", "Até 2,17 km todos os raios saem saturados (~74 dBZ): sem medida real.",
                  "cega", f"<LineString><tessellate>1</tessellate><coordinates>{circulo(RADAR, ZONA_CEGA_KM * 1000)}"
                          f"</coordinates></LineString>"),
    ]
    # Onde estaria, a 322,5°, um objeto cujo topo fica a TOPO_GRAUS acima da antena
    for d in (10, 20, 40, 60):
        h_rel = d * math.tan(math.radians(TOPO_GRAUS))
        la, lo = destino(*RADAR, meio, d)
        itens.append(placemark(f"A {d:.0f} m: topo >= {ANTENA_M + h_rel:.1f} m (+{h_rel:.1f} m)",
                               f"Objeto a {meio}° e {d:.0f} m, com ~1 m de largura e topo {h_rel:.1f} m acima da antena, "
                               f"explicaria o bloqueio até ~{TOPO_GRAUS}°.",
                               "candidato", ponto(la, lo)))
    estilos = """
<Style id="radar"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/target.png</href></Icon></IconStyle></Style>
<Style id="farol"><IconStyle><scale>1.2</scale><color>ff00ffff</color><Icon><href>http://maps.google.com/mapfiles/kml/shapes/star.png</href></Icon></IconStyle></Style>
<Style id="setor"><LineStyle><color>ff0000ff</color><width>2</width></LineStyle><PolyStyle><color>660000ff</color></PolyStyle></Style>
<Style id="setor_longe"><LineStyle><color>ff0000ff</color><width>1</width></LineStyle><PolyStyle><color>220000ff</color></PolyStyle></Style>
<Style id="odim"><IconStyle><scale>0.8</scale><color>ff888888</color><Icon><href>http://maps.google.com/mapfiles/kml/shapes/target.png</href></Icon></IconStyle></Style>
<Style id="obst"><IconStyle><scale>1.1</scale><color>ff0080ff</color><Icon><href>http://maps.google.com/mapfiles/kml/shapes/caution.png</href></Icon></IconStyle></Style>
<Style id="candidato"><IconStyle><scale>0.7</scale><color>ff00ff00</color><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle></Style>
<Style id="setor_norte"><LineStyle><color>ff00a5ff</color><width>1.5</width></LineStyle><PolyStyle><color>4400a5ff</color></PolyStyle></Style>
<Style id="cega"><LineStyle><color>ffffffff</color><width>1.5</width></LineStyle></Style>"""
    kml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           f"<name>Radar de Araranguá: bloqueios</name>{estilos}\n" + "\n".join(itens) + "\n</Document></kml>\n")
    saida = Path(__file__).resolve().parent / "kml" / "ararangua_bloqueio.kml"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(kml, encoding="utf-8")
    print(f"{saida}  (farol: {az_f:.1f}°, {d_f:.0f} m; obstáculo informado: {az_o:.1f}°, {d_o:.0f} m)")


if __name__ == "__main__":
    main()
