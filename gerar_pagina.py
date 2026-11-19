# -*- coding: utf-8 -*-
"""Galeria das imagens de radar do evento de Chapecó (04/11/2026).

Copia as figuras de radar do projeto echo_em_arco para imagens/ e gera duas páginas:

  index.html     versão pública: só figuras próprias e atuais (é a que vai para o GitHub)
  completo.html  versão local: inclui também imagens de terceiros (REDEMET/DECEA, capturas)
                 e as figuras da primeira versão, que o echo_em_arco não publica

As imagens de terceiros e as da primeira versão ficam em imagens/_privado/, ignorada pelo git.

Uso:
  python gerar_pagina.py [--origem ../echo_em_arco]
"""
import argparse
import csv
import html
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LOCAL = timedelta(hours=-3)

# flag: None = própria e atual; "terceiros" = produto de terceiros; "anterior" = primeira versão, superada
SECOES = [
    {
        "id": "visao-geral",
        "titulo": "Visão geral do evento",
        "texto": "Evolução da linha em arco sobre o Oeste de SC e trajetória dos núcleos, a partir dos volumes brutos do radar banda S de Chapecó e dos MaxCAPPI do DECEA.",
        "itens": [
            {"src": "radar/figuras/chapeco_quadros_redemet.png", "titulo": "Evolução em seis horários",
             "legenda": "Quadros do radar em seis horários da passagem da linha.", "script": "radar/plotar_radar_chapeco.py"},
            {"src": "radar/figuras/chapeco_trajetoria_nucleos.png", "titulo": "Trajetória dos núcleos",
             "legenda": "Refletividade máxima acumulada e trajetória dos núcleos, 09:00–12:00 local.", "script": "radar/plotar_radar_chapeco.py"},
            {"src": "radar/figuras/chapeco_redemet_georref.png", "titulo": "MaxCAPPI REDEMET georreferenciado",
             "legenda": "Santiago e Morro da Igreja com limites e horários UTC reais do produto, sem converter cor em dBZ.",
             "script": "radar/painel_redemet_georref.py", "flag": "terceiros"},
            {"src": "radar/figuras/mapa_danos_trilha.png", "titulo": "Bairros com danos e trilha do radar",
             "legenda": "Envelope dos bairros com danos relatados, trilha do núcleo e hidrografia. A Defesa Civil divulgou bairros, não pontos de dano. Hidrografia e bairros © colaboradores do OpenStreetMap.",
             "script": "radar/mapa_danos_trilha.py"},
            {"src": "assets/radar_4paineis_chapeco_1030.jpg", "titulo": "Quatro painéis, 10:30 local",
             "legenda": "Captura de tela do radar de Chapecó.", "flag": "terceiros"},
            {"src": "assets/radar_bow_echo_topo_71c.jpg", "titulo": "Eco em arco",
             "legenda": "Captura de tela com a linha em arco.", "flag": "terceiros"},
            {"src": "assets/radar_zoom_circulos_chapeco.jpg", "titulo": "Zoom sobre Chapecó",
             "legenda": "Captura de tela com destaque sobre Chapecó.", "flag": "terceiros"},
        ],
    },
    {
        "id": "animacoes",
        "titulo": "Animações",
        "texto": "Laços de quadros e vídeos. Use o controle deslizante para parar num horário.",
        "itens": [
            {"tipo": "video", "src": "assets/radar_chapeco_20261104.mp4", "titulo": "Gravação do radar, 09:16–11:45 local",
             "legenda": "Gravação de tela do radar durante a passagem da linha."},
            {"tipo": "laco", "id": "quadros-gravacao", "glob": "assets/radar_frame_0*.png", "titulo": "Quadros da gravação",
             "legenda": "Sete quadros extraídos da gravação do radar."},
            {"tipo": "laco", "id": "redemet-mi", "glob": "radar/mi/maxcappi/*.png", "csv": "radar/mi/maxcappi/quadros.csv",
             "titulo": "MaxCAPPI, Morro da Igreja, Urubici (DECEA)", "legenda": "Produto REDEMET como veio, a cada ~20 min.",
             "script": "radar/baixar_redemet_chapeco.py", "flag": "terceiros"},
            {"tipo": "laco", "id": "redemet-sg", "glob": "radar/sg/maxcappi/*.png", "csv": "radar/sg/maxcappi/quadros.csv",
             "titulo": "MaxCAPPI, Santiago (DECEA)", "legenda": "Produto REDEMET como veio, a cada ~20 min.",
             "script": "radar/baixar_redemet_chapeco.py", "flag": "terceiros"},
        ],
    },
    {
        "id": "campos",
        "titulo": "Campos polarimétricos, 10:30 local (13:30 UTC), 0,5°",
        "texto": "Varredura mais baixa do radar banda S de Chapecó em torno do Aeroporto. O feixe passa ~280 m acima do chão sobre o aeroporto.",
        "itens": [
            {"src": "radar/figuras/video/campo_Z.png", "titulo": "Refletividade (Z)", "legenda": "Z a 0,5°, 13:30 UTC.", "script": "radar/figuras_video.py"},
            {"src": "radar/figuras/video/campo_V.png", "titulo": "Velocidade radial (V)", "legenda": "V a 0,5°, 13:30 UTC.", "script": "radar/figuras_video.py"},
            {"src": "radar/figuras/video/campo_CC.png", "titulo": "Coeficiente de correlação (CC)", "legenda": "CC a 0,5°, 13:30 UTC. O CC anômalo sobre o aeroporto é a principal pendência.", "script": "radar/figuras_video.py"},
            {"src": "radar/figuras/video/campo_ZDR.png", "titulo": "Refletividade diferencial (ZDR)", "legenda": "ZDR a 0,5°, 13:30 UTC.", "script": "radar/figuras_video.py"},
            {"src": "radar/figuras/video/mapa.png", "titulo": "Mapa da trilha", "legenda": "Base usada para animar a trilha do núcleo no vídeo.", "script": "radar/figuras_video.py"},
            {"src": "assets/radar_v2/poster.jpg", "titulo": "Capa do vídeo v2", "legenda": "Quadro de abertura do vídeo."},
            {"src": "assets/radar_v2/z.png", "titulo": "Z (painel do vídeo, 1ª versão)", "legenda": "Painel da primeira versão do vídeo.", "script": "radar/figuras_video_1330.py", "flag": "anterior"},
            {"src": "assets/radar_v2/cc.png", "titulo": "CC (painel do vídeo, 1ª versão)", "legenda": "Painel da primeira versão do vídeo.", "script": "radar/figuras_video_1330.py", "flag": "anterior"},
            {"src": "assets/radar_v2/v_rel.png", "titulo": "V relativa ao núcleo (1ª versão)", "legenda": "V − U·r, com U = 40,4 m/s para leste.", "script": "radar/figuras_video_1330.py", "flag": "anterior"},
            {"src": "assets/radar_v2/linha.png", "titulo": "Linha (1ª versão)", "legenda": "Painel da primeira versão do vídeo.", "script": "radar/figuras_video_microexplosao.py", "flag": "anterior"},
        ],
    },
    {
        "id": "vertical",
        "titulo": "Estrutura vertical e hidrometeoros",
        "texto": "Alturas acima do radar (822 m). A fusão, estimada pelo próprio radar depois da passagem, fica a ~3,0–3,3 km acima dele.",
        "itens": [
            {"src": "assets/radar_v2/corte_vertical.png", "titulo": "Corte vertical seguindo o núcleo",
             "legenda": "Z, ZDR, CC, KDP e classes, de 10:12 a 10:42 local.", "script": "radar/corte_vertical_hidrometeoros.py"},
            {"src": "radar/figuras/corte_vertical_hidrometeoros.png", "titulo": "Coluna e hidrometeoros",
             "legenda": "Nível de fusão (QVP), viés de ZDR e coluna seguindo o núcleo.", "script": "radar/corte_vertical_hidrometeoros.py"},
            {"src": "assets/radar_v2/chuva.png", "titulo": "Z máximo por altura e horário",
             "legenda": "Só com CC ≥ 0,90: a coluna é de chuva intensa.", "script": "radar/figuras_video_microexplosao.py"},
            {"src": "radar/figuras/aeroporto_1330_elevacoes.png", "titulo": "Aeroporto, 13:30 UTC, por elevação",
             "legenda": "O núcleo de CC baixo nas elevações do volume de 13:30 UTC.", "script": "radar/analise_rotacao.py"},
            {"src": "radar/figuras/gancho_baixos_niveis.png", "titulo": "Eco em gancho e BWER",
             "legenda": "Busca de BWER, eco em gancho e granizo, 13:00–14:00 UTC, em grade de 1 km.", "script": "radar/analise_bwer_gancho_granizo.py"},
            {"src": "radar/figuras/chapeco_corte_vertical_rhi_1030.png", "titulo": "Corte vertical RHI, 10:30 (1ª versão)",
             "legenda": "Usava fusão a 3,8 km, valor que está errado.", "script": "radar/plotar_radar_chapeco.py", "flag": "anterior"},
            {"src": "assets/radar_v2/descida.png", "titulo": "Descida do máximo (1ª versão)",
             "legenda": "Painel da primeira versão do vídeo.", "script": "radar/figuras_video_microexplosao.py", "flag": "anterior"},
            {"src": "assets/radar_v2/perfil.png", "titulo": "Perfil vertical (1ª versão)",
             "legenda": "Painel da primeira versão do vídeo.", "script": "radar/figuras_video_1330.py", "flag": "anterior"},
        ],
    },
    {
        "id": "vento",
        "titulo": "Vento, cisalhamento e rotação",
        "texto": "Com radar único e a fronteira quase radial, rotação e cisalhamento linear dão o mesmo sinal.",
        "itens": [
            {"src": "assets/radar_v2/vento.png", "titulo": "Vento atrás da linha, 10:30 local",
             "legenda": "A componente em direção ao radar cai de 27 m/s a 130 m para 18 m/s a 810 m. Uma única varredura.",
             "script": "radar/figuras_video_microexplosao.py"},
            {"src": "assets/radar_v2/cisalhamento.png", "titulo": "Cisalhamento em 2 km",
             "legenda": "V e cisalhamento sem gates dobrados: núcleo contra outros discos.", "script": "radar/figuras_video_microexplosao.py"},
            {"src": "radar/figuras/velocidade_painel.png", "titulo": "Velocidade radial em torno do Aeroporto",
             "legenda": "13:12–13:48 UTC, com aliasing corrigido por regiões contíguas.", "script": "radar/analise_velocidade.py"},
            {"src": "radar/figuras/rotacao_resumo.png", "titulo": "Resumo da análise de rotação",
             "legenda": "Descida de precipitação, velocidade relativa ao núcleo e largura espectral.", "script": "radar/analise_rotacao_final.py"},
            {"src": "radar/figuras/rotacao_evolucao.png", "titulo": "Evolução da rotação",
             "legenda": "Cisalhamento seguindo o núcleo de CC baixo ao longo dos volumes.", "script": "radar/analise_rotacao.py"},
            {"src": "radar/figuras/rotacao_perfil_vertical.png", "titulo": "Perfil vertical da rotação",
             "legenda": "As 14 elevações, seguindo o núcleo com o movimento ajustado.", "script": "radar/analise_rotacao.py"},
            {"src": "radar/figuras/descida_rotacao.png", "titulo": "A rotação desceu?",
             "legenda": "Maior cisalhamento em arco de 2 km perto da trilha, todas as elevações, 13:06–13:36 UTC.", "script": "radar/analise_descida.py"},
            {"src": "radar/figuras/chapeco_4paineis_reais_1030.png", "titulo": "Quatro painéis, 10:30 (1ª versão)",
             "legenda": "Figura da primeira versão da análise.", "script": "radar/plotar_radar_chapeco.py", "flag": "anterior"},
        ],
    },
    {
        "id": "topo",
        "titulo": "Topo do eco e radar sobre satélite",
        "texto": "Echo Top e echomax do radar de Chapecó sobre o canal 13 do GOES-19, 12–15 UTC. Perto do radar o topo fica truncado e é só um limite inferior.",
        "itens": [
            {"src": "satelite/figuras/echotop_1330.png", "titulo": "Echo Top, 13:30 UTC",
             "legenda": "Topo a 18 dBZ (eco) e 40 dBZ (núcleo convectivo) sobre o GOES-19.", "script": "satelite/compor_echotop_satelite.py"},
            {"src": "satelite/figuras/echotop_painel.png", "titulo": "Echo Top em seis horários",
             "legenda": "Painel de Echo Top sobre o canal 13.", "script": "satelite/compor_echotop_satelite.py"},
            {"tipo": "laco", "id": "echotop", "glob": "satelite/figuras/echotop/e_*.png", "csv": "satelite/figuras/echotop_estatisticas.csv",
             "titulo": "Echo Top, quadro a quadro", "legenda": "Um quadro por volume do radar, a cada 6 min.", "script": "satelite/compor_echotop_satelite.py"},
            {"src": "assets/radar_v2/composicao_1330.png", "titulo": "Echomax e satélite, 13:30 UTC",
             "legenda": "Satélite, echomax e composição no volume de 13:30 UTC.", "script": "satelite/compor_radar_satelite.py"},
            {"src": "satelite/figuras/composicao_painel.png", "titulo": "Composição em seis horários",
             "legenda": "Echomax sobre o canal 13 do GOES-19.", "script": "satelite/compor_radar_satelite.py"},
            {"tipo": "video", "src": "satelite/figuras/echotop_animacao.mp4", "titulo": "Animação do Echo Top",
             "legenda": "Echo Top sobre o GOES-19, 12–15 UTC.", "script": "satelite/compor_echotop_satelite.py"},
        ],
    },
]

NOMES_RADAR = {"mi": "Morro da Igreja, Urubici (SC)", "sg": "Santiago (RS)", "ct": "Curitiba (PR)"}


def secao_recentes():
    """Laços das imagens baixadas por baixar_recentes.py (recentes/<radar>/<produto>/quadros.csv)."""
    itens = []
    for q in sorted((AQUI / "recentes").glob("*/*/quadros.csv")):
        with open(q, encoding="utf-8") as f:
            linhas = [r for r in csv.DictReader(f) if (q.parent / r["arquivo"]).exists()]
        if not linhas:
            continue
        area, produto = q.parent.parent.name, q.parent.name
        itens.append({
            "tipo": "laco", "flag": "terceiros", "script": "baixar_recentes.py",
            "titulo": f"{produto.upper()}, {NOMES_RADAR.get(area, area)}",
            "legenda": f"{len(linhas)} quadros, de {utc_para_rotulo(linhas[0]['data_utc'])} a {utc_para_rotulo(linhas[-1]['data_utc'])}. Produto REDEMET/DECEA como veio.",
            "quadros": [{"src": (q.parent / r["arquivo"]).relative_to(AQUI).as_posix(),
                         "rotulo": utc_para_rotulo(r["data_utc"])} for r in linhas],
        })
    if not itens:
        return None
    return {"id": "recentes", "titulo": "Últimas horas",
            "texto": "Imagens recentes dos radares do DECEA, baixadas com baixar_recentes.py. Rode de novo para atualizar.",
            "itens": itens}


SCRIPTS_FORA = {"baixar_ftp_chapeco.py", "baixar_sdc_ftp.py"}  # acesso ao FTP da SDC: não vão para o repositório público
SCRIPTS_SATELITE = ["compor_echotop_satelite.py", "compor_radar_satelite.py", "echotop_trilha.py"]


def utc_para_rotulo(texto):
    t = datetime.strptime(texto, "%Y-%m-%d %H:%M:%S" if "-" in texto else "%H:%M:%S")
    return f"{t:%H:%M} UTC · {t + LOCAL:%H:%M} local"


def rotulos_laco(origem, item, arquivos):
    if "csv" not in item:
        return [f"quadro {i + 1}" for i in range(len(arquivos))]
    with open(origem / item["csv"], encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    if "arquivo" in linhas[0]:
        por_nome = {r["arquivo"]: utc_para_rotulo(r["data_utc"]) for r in linhas}
        return [por_nome.get(a.name, a.stem) for a in arquivos]
    # sem coluna de arquivo: uma linha por quadro, na mesma ordem
    return [utc_para_rotulo(linhas[i]["radar_utc"]) if i < len(linhas) else a.stem
            for i, a in enumerate(arquivos)]


def destino(secao, item, nome):
    base = AQUI / "imagens" / ("_privado" if item.get("flag") else "") / secao
    return base / nome


def copiar(orig, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_mtime < orig.stat().st_mtime or dest.stat().st_size != orig.stat().st_size:
        shutil.copy2(orig, dest)


def coletar(origem):
    faltando = []
    for s in SECOES:
        for it in s["itens"]:
            if it.get("tipo") == "laco":
                arquivos = sorted((origem / Path(it["glob"]).parent).glob(Path(it["glob"]).name))
                if not arquivos:
                    faltando.append(it["glob"])
                rot = rotulos_laco(origem, it, arquivos) if arquivos else []
                it["quadros"] = []
                for a, r in zip(arquivos, rot):
                    d = destino(s["id"], it, f"{it['id']}/{a.name}")
                    copiar(a, d)
                    it["quadros"].append({"src": d.relative_to(AQUI).as_posix(), "rotulo": r})
            else:
                a = origem / it["src"]
                if not a.exists():
                    faltando.append(it["src"])
                    it["ausente"] = True
                    continue
                d = destino(s["id"], it, a.name)
                copiar(a, d)
                it["arquivo"] = d.relative_to(AQUI).as_posix()
    return faltando


def copiar_scripts(origem):
    copiados = []
    for p in sorted((origem / "radar").glob("*.py")):
        if p.name not in SCRIPTS_FORA:
            copiar(p, AQUI / "radar" / p.name)
            copiados.append(f"radar/{p.name}")
    for extra in ["radar/RELATORIO_ROTACAO.md"] + [f"satelite/{n}" for n in SCRIPTS_SATELITE]:
        if (origem / extra).exists():
            copiar(origem / extra, AQUI / extra)
            copiados.append(extra)
    return copiados


SELO = {"terceiros": "terceiros", "anterior": "1ª versão"}


def cartao(it):
    e = html.escape
    selo = f'<span class="selo selo-{it["flag"]}">{SELO[it["flag"]]}</span>' if it.get("flag") else ""
    script = (f'<a class="script" href="{e(it["script"])}"><code>{e(it["script"])}</code></a>'
              if it.get("script") else "")
    rodape = f'<figcaption><h3>{e(it["titulo"])} {selo}</h3><p>{e(it["legenda"])}</p>{script}</figcaption>'
    tipo = it.get("tipo", "img")
    if tipo == "laco":
        dados = html.escape(json.dumps(it["quadros"], ensure_ascii=False), quote=True)
        primeiro = it["quadros"][0]
        return (f'<figure class="cartao largo laco" data-quadros="{dados}">'
                f'<div class="quadro"><img src="{e(primeiro["src"])}" alt="{e(it["titulo"])}" loading="lazy"></div>'
                f'<div class="controles"><button type="button" class="tocar" aria-label="Tocar">▶</button>'
                f'<input type="range" min="0" max="{len(it["quadros"]) - 1}" value="0" aria-label="Quadro">'
                f'<select aria-label="Velocidade"><option value="900">lento</option><option value="450" selected>normal</option><option value="180">rápido</option></select>'
                f'<output>{e(primeiro["rotulo"])}</output></div>{rodape}</figure>')
    if tipo == "video":
        return (f'<figure class="cartao largo"><video controls loop muted playsinline preload="metadata" src="{e(it["arquivo"])}"></video>'
                f'{rodape}</figure>')
    return (f'<figure class="cartao"><button type="button" class="abrir" aria-label="Ampliar {e(it["titulo"])}">'
            f'<img src="{e(it["arquivo"])}" alt="{e(it["titulo"])}" loading="lazy"></button>{rodape}</figure>')


def pagina(completa, scripts):
    e = html.escape
    secoes_html, nav = [], []
    total = 0
    for s in SECOES:
        itens = [it for it in s["itens"] if not it.get("ausente") and (completa or not it.get("flag"))
                 and (it.get("tipo") != "laco" or it.get("quadros"))]
        if not itens:
            continue
        total += sum(len(it.get("quadros", [])) or 1 for it in itens)
        nav.append(f'<a href="#{s["id"]}">{e(s["titulo"].split(",")[0])}</a>')
        secoes_html.append(f'<section id="{s["id"]}"><h2>{e(s["titulo"])}</h2><p class="intro">{e(s["texto"])}</p>'
                           f'<div class="grade">{"".join(cartao(it) for it in itens)}</div></section>')
    lista_scripts = "".join(f'<li><a href="{e(p)}"><code>{e(p)}</code></a></li>' for p in scripts)
    aviso = ("" if not completa else
             '<p class="aviso">Versão local completa: inclui produtos de terceiros (REDEMET/DECEA e capturas de tela) '
             'e figuras da 1ª versão, superadas. Não publique esta página.</p>')
    outra = ('<a href="index.html">versão pública</a>' if completa else "")
    return TEMPLATE.format(
        titulo="Radar de Chapecó" + (" (completo)" if completa else ""),
        nav="".join(nav), secoes="".join(secoes_html), scripts=lista_scripts, aviso=aviso, total=total,
        gerado=datetime.now().strftime("%d/%m/%Y %H:%M"), outra=outra,
    )


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="Galeria das imagens de radar do evento de vento forte em Chapecó, 04/11/2026.">
<style>
:root {{
  --fundo: #f6f7f9; --superficie: #ffffff; --texto: #1b1f24; --suave: #5b6470; --borda: #dde1e6;
  --destaque: #0b6bcb; --terceiros: #9a5b00; --terceiros-fundo: #fff1dc; --anterior: #7a3e9d; --anterior-fundo: #f3e8fa;
  --quadro: #0e1116;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --fundo: #0e1116; --superficie: #171b21; --texto: #e6e9ed; --suave: #9aa4b0; --borda: #2a3038;
    --destaque: #5aa9ff; --terceiros: #ffc46b; --terceiros-fundo: #3a2a10; --anterior: #d6a6f2; --anterior-fundo: #2e1e3a;
  }}
}}
:root[data-theme="dark"] {{
  --fundo: #0e1116; --superficie: #171b21; --texto: #e6e9ed; --suave: #9aa4b0; --borda: #2a3038;
  --destaque: #5aa9ff; --terceiros: #ffc46b; --terceiros-fundo: #3a2a10; --anterior: #d6a6f2; --anterior-fundo: #2e1e3a;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; scroll-padding-top: 64px; }}
body {{ margin: 0; background: var(--fundo); color: var(--texto);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
a {{ color: var(--destaque); }}
header {{ max-width: 1200px; margin: 0 auto; padding: 40px 16px 16px; }}
header h1 {{ margin: 0 0 8px; font-size: clamp(1.6rem, 4vw, 2.3rem); letter-spacing: -0.01em; }}
header p {{ margin: 0; color: var(--suave); max-width: 72ch; }}
nav {{ position: sticky; top: 0; z-index: 5; background: color-mix(in srgb, var(--fundo) 90%, transparent);
  backdrop-filter: blur(6px); border-bottom: 1px solid var(--borda); }}
nav div {{ max-width: 1200px; margin: 0 auto; padding: 10px 16px; display: flex; gap: 18px; overflow-x: auto;
  white-space: nowrap; font-size: 0.92rem; }}
nav a {{ text-decoration: none; color: var(--suave); }}
nav a:hover {{ color: var(--texto); }}
main {{ max-width: 1200px; margin: 0 auto; padding: 0 16px 48px; }}
section {{ padding-top: 32px; }}
h2 {{ font-size: 1.35rem; margin: 0 0 4px; }}
.intro {{ margin: 0 0 18px; color: var(--suave); max-width: 80ch; }}
.aviso {{ margin: 16px 0 0; padding: 10px 14px; border-radius: 8px; background: var(--terceiros-fundo);
  color: var(--terceiros); max-width: 80ch; }}
.grade {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr)); }}
.cartao {{ margin: 0; background: var(--superficie); border: 1px solid var(--borda); border-radius: 10px;
  overflow: hidden; display: flex; flex-direction: column; }}
.cartao.largo {{ grid-column: 1 / -1; }}
.abrir {{ all: unset; cursor: zoom-in; display: block; background: var(--quadro); }}
.abrir:focus-visible {{ outline: 2px solid var(--destaque); outline-offset: -2px; }}
.cartao img, .cartao video {{ display: block; width: 100%; height: auto; background: var(--quadro); }}
.abrir img {{ aspect-ratio: 4 / 3; object-fit: contain; }}
.quadro {{ background: var(--quadro); display: flex; justify-content: center; }}
.laco .quadro img {{ width: auto; max-width: 100%; max-height: 72vh; }}
.cartao video {{ max-height: 72vh; }}
figcaption {{ padding: 12px 14px 14px; }}
figcaption h3 {{ margin: 0 0 4px; font-size: 1rem; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
figcaption p {{ margin: 0 0 6px; color: var(--suave); font-size: 0.92rem; }}
.script {{ font-size: 0.8rem; text-decoration: none; }}
.selo {{ font-size: 0.72rem; font-weight: 600; padding: 1px 8px; border-radius: 999px; }}
.selo-terceiros {{ background: var(--terceiros-fundo); color: var(--terceiros); }}
.selo-anterior {{ background: var(--anterior-fundo); color: var(--anterior); }}
.controles {{ display: flex; gap: 10px; align-items: center; padding: 10px 14px 0; flex-wrap: wrap; }}
.controles input {{ flex: 1 1 200px; accent-color: var(--destaque); }}
.controles button, .controles select {{ font: inherit; color: var(--texto); background: var(--fundo);
  border: 1px solid var(--borda); border-radius: 6px; padding: 4px 10px; cursor: pointer; }}
.controles button {{ min-width: 44px; }}
.controles output {{ font-variant-numeric: tabular-nums; font-size: 0.9rem; color: var(--suave); min-width: 17ch; }}
.scripts ul {{ columns: 2 260px; padding-left: 18px; font-size: 0.9rem; }}
footer {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px 40px; color: var(--suave); font-size: 0.85rem;
  border-top: 1px solid var(--borda); }}
#caixa {{ border: 0; padding: 0; background: transparent; max-width: 100vw; max-height: 100vh; width: 100vw; height: 100vh; }}
#caixa::backdrop {{ background: rgba(0, 0, 0, 0.88); }}
#caixa .interior {{ width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px; padding: 16px; }}
#caixa img {{ max-width: 100%; max-height: calc(100vh - 90px); object-fit: contain; }}
#caixa p {{ color: #e6e9ed; margin: 0; text-align: center; }}
#caixa button {{ position: fixed; background: rgba(255,255,255,0.12); color: #fff; border: 0; border-radius: 999px;
  width: 44px; height: 44px; font-size: 1.3rem; cursor: pointer; }}
#caixa .fechar {{ top: 14px; right: 14px; }}
#caixa .ant {{ left: 14px; top: 50%; }}
#caixa .prox {{ right: 14px; top: 50%; }}
</style>
</head>
<body>
<header>
  <h1>Radar de Chapecó, 04/11/2026</h1>
  <p>Todas as figuras de radar da análise do evento de vento forte em Chapecó (SC): volumes brutos do radar banda S
  da Defesa Civil de SC, produtos derivados e composições com o GOES-19. Horários em UTC e local (UTC−3).
  Análise completa em <a href="https://github.com/reinaldohaas/echo_em_arco">echo_em_arco</a>. {outra}</p>
  {aviso}
</header>
<nav aria-label="Seções"><div>{nav}<a href="#scripts">Scripts</a></div></nav>
<main>
{secoes}
<section id="scripts" class="scripts">
  <h2>Scripts</h2>
  <p class="intro">Código que gera as figuras. Os volumes brutos (.vol) não estão no repositório.</p>
  <ul>{scripts}</ul>
</section>
</main>
<footer>{total} imagens · gerado em {gerado} por <code>gerar_pagina.py</code>.</footer>
<dialog id="caixa" aria-label="Imagem ampliada">
  <div class="interior"><img alt=""><p></p></div>
  <button type="button" class="fechar" aria-label="Fechar">✕</button>
  <button type="button" class="ant" aria-label="Anterior">‹</button>
  <button type="button" class="prox" aria-label="Próxima">›</button>
</dialog>
<script>
(() => {{
  // Laços de quadros
  document.querySelectorAll('.laco').forEach(fig => {{
    const quadros = JSON.parse(fig.dataset.quadros);
    const img = fig.querySelector('.quadro img'), faixa = fig.querySelector('input'),
          botao = fig.querySelector('.tocar'), vel = fig.querySelector('select'), rotulo = fig.querySelector('output');
    let i = 0, timer = null;
    const pre = new Set();
    const mostrar = n => {{
      i = (n + quadros.length) % quadros.length;
      img.src = quadros[i].src; faixa.value = i; rotulo.textContent = quadros[i].rotulo;
      const prox = quadros[(i + 1) % quadros.length].src;
      if (!pre.has(prox)) {{ pre.add(prox); new Image().src = prox; }}
    }};
    const parar = () => {{ clearInterval(timer); timer = null; botao.textContent = '▶'; botao.setAttribute('aria-label', 'Tocar'); }};
    const tocar = () => {{ parar(); timer = setInterval(() => mostrar(i + 1), +vel.value);
                           botao.textContent = '❚❚'; botao.setAttribute('aria-label', 'Pausar'); }};
    botao.addEventListener('click', () => timer ? parar() : tocar());
    faixa.addEventListener('input', () => {{ parar(); mostrar(+faixa.value); }});
    vel.addEventListener('change', () => {{ if (timer) tocar(); }});
    fig.querySelector('.quadro').addEventListener('click', () => timer ? parar() : tocar());
  }});

  // Caixa de ampliação
  const caixa = document.getElementById('caixa'), cimg = caixa.querySelector('img'), ctxt = caixa.querySelector('p');
  const botoes = [...document.querySelectorAll('.abrir')];
  let atual = 0;
  const abrir = n => {{
    atual = (n + botoes.length) % botoes.length;
    const b = botoes[atual], im = b.querySelector('img');
    cimg.src = im.src; cimg.alt = im.alt;
    ctxt.textContent = b.closest('figure').querySelector('h3').textContent.trim();
    if (!caixa.open) caixa.showModal();
  }};
  botoes.forEach((b, n) => b.addEventListener('click', () => abrir(n)));
  caixa.querySelector('.fechar').addEventListener('click', () => caixa.close());
  caixa.querySelector('.ant').addEventListener('click', () => abrir(atual - 1));
  caixa.querySelector('.prox').addEventListener('click', () => abrir(atual + 1));
  caixa.addEventListener('click', ev => {{ if (ev.target === caixa || ev.target.classList.contains('interior')) caixa.close(); }});
  document.addEventListener('keydown', ev => {{
    if (!caixa.open) return;
    if (ev.key === 'ArrowLeft') abrir(atual - 1);
    if (ev.key === 'ArrowRight') abrir(atual + 1);
  }});
}})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origem", default=str(AQUI.parent / "echo_em_arco"), help="pasta do projeto echo_em_arco")
    origem = Path(ap.parse_args().origem).resolve()
    faltando = coletar(origem)
    scripts = copiar_scripts(origem) + ["baixar_recentes.py", "gerar_pagina.py"]
    recentes = secao_recentes()
    if recentes:
        SECOES.insert(0, recentes)
    (AQUI / "index.html").write_text(pagina(False, scripts), encoding="utf-8")
    (AQUI / "completo.html").write_text(pagina(True, scripts), encoding="utf-8")
    print(f"Origem: {origem}")
    print(f"Scripts copiados: {len(scripts)}")
    print("Páginas: index.html (pública) e completo.html (local)")
    for f in faltando:
        print("  AUSENTE:", f)


if __name__ == "__main__":
    main()
