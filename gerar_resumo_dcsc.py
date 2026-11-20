# -*- coding: utf-8 -*-
"""Gera relatorio/Resumo_Radar_Ararangua_DCSC.pdf: resumo executivo do diagnóstico do radar de Araranguá
para a Defesa Civil de Santa Catarina."""
import os
from pathlib import Path

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

AQUI = Path(__file__).resolve().parent
REL = AQUI / "relatorio"
FIG = REL / "figuras"
import sys
SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else REL / "Resumo_Radar_Ararangua_DCSC.pdf"

TTF = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DV", str(TTF / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(TTF / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-I", str(TTF / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DV-BI", str(TTF / "DejaVuSans-BoldOblique.ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

AZUL = colors.HexColor("#1f4e79")
st = getSampleStyleSheet()
corpo = ParagraphStyle("corpo", parent=st["Normal"], fontName="DV", fontSize=9.5, leading=13, alignment=TA_JUSTIFY,
                       spaceAfter=5)
peq = ParagraphStyle("peq", parent=corpo, fontSize=8, leading=10, alignment=0, spaceAfter=0)
peqb = ParagraphStyle("peqb", parent=peq, fontName="DV-B", textColor=colors.white)
tit = ParagraphStyle("tit", parent=st["Title"], fontName="DV-B", fontSize=16, leading=20, textColor=AZUL, spaceAfter=4)
sub = ParagraphStyle("sub", parent=corpo, fontSize=10, leading=13, textColor=colors.HexColor("#444444"), alignment=1)
h1 = ParagraphStyle("h1", parent=st["Heading2"], fontName="DV-B", fontSize=12, leading=15, textColor=AZUL,
                    spaceBefore=10, spaceAfter=5)
leg = ParagraphStyle("leg", parent=peq, fontName="DV-I", alignment=1, spaceAfter=8)
caixa = ParagraphStyle("caixa", parent=corpo, fontSize=9.5, leading=13, backColor=colors.HexColor("#eef3f8"),
                       borderColor=AZUL, borderWidth=0.8, borderPadding=7, spaceBefore=6, spaceAfter=10)


def P(t, s=corpo):
    return Paragraph(t, s)


def lista(itens, s=corpo):
    return ListFlowable([ListItem(P(t, s), leftIndent=12) for t in itens], bulletType="bullet", start="•",
                        leftIndent=12, bulletFontName="DV")


def tabela(linhas, larguras, cab=AZUL):
    dados = [[P(c, peqb) for c in linhas[0]]] + [[P(c, peq) for c in l] for l in linhas[1:]]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), cab), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9fb3c8")),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fa")]),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def figura(arq, largura_cm, legenda):
    from PIL import Image as PI
    w, h = PI.open(arq).size
    larg = largura_cm * cm
    return KeepTogether([Image(str(arq), width=larg, height=larg * h / w), P(legenda, leg)])


def rodape(c, doc):
    c.saveState()
    c.setFont("DV", 7.5)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawString(2 * cm, 1.2 * cm, "Radar meteorológico de Araranguá — resumo do diagnóstico para a Defesa Civil de SC")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"página {doc.page}")
    c.restoreState()


def main():
    doc = SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title="Radar de Araranguá — resumo do diagnóstico",
                            author="Reinaldo Haas", subject="Diagnóstico do radar meteorológico de Araranguá (SC)")
    s = []
    s += [P("Radar meteorológico de Araranguá", tit),
          P("Diagnóstico dos dados, bloqueios do feixe e recomendações<br/>Resumo para a Defesa Civil de Santa Catarina — 20/11/2026<br/>Autor: Reinaldo Haas", sub),
          Spacer(1, 10)]

    s += [P("1. Contexto", h1),
          P("O radar de Araranguá (EEC Ranger, banda X, 410 W, Morro dos Conventos) tem sido apontado por usuários, "
            "inclusive pesquisadores do INPE, como fonte de dados inconsistentes. Este resumo apresenta o diagnóstico "
            "feito a partir dos volumes publicados no FTP da Defesa Civil (16 a 20/11/2026), da simulação do bloqueio "
            "do feixe com o modelo de terreno (MDT) e de superfície (MDS) de 1 m do SIGSC e da análise das variáveis "
            "polarimétricas. O relatório técnico completo, com métodos, figuras e scripts, está no repositório "
            "<i>github.com/reinaldohaas/radar-sc</i> (relatorio/RELATORIO_ARARANGUA.md).")]

    s += [P("2. Conclusão principal", h1),
          P("<b>Os dados não são inconsistentes ao acaso.</b> Há um conjunto de causas identificadas que se somam. "
            "Quase todas têm solução simples, por configuração e sem obra. "
            "O ponto que precisa de diagnóstico do fabricante é a <b>sensibilidade do radar</b>, que está muito abaixo "
            "do esperado para um radar de banda X. O bloqueio do feixe a oeste tem solução definitiva com uma "
            "<b>torre de 25 m no local atual</b>, sem necessidade de mudar o radar de lugar.", caixa)]

    s += [P("3. Principais constatações", h1),
          lista([
              "<b>Configuração da PRF inutiliza o Doppler.</b> Com 400/267 Hz em banda X, a velocidade máxima "
              "medida é de 3,2 m/s por PRF (6,4 m/s com dupla PRF), menor que a largura espectral da própria chuva. "
              "A velocidade sai aleatória e o filtro de clutter, que depende dela, apaga raios inteiros de chuva: "
              "em mediana 44% dos raios com chuva a 0,5°, sobretudo nos setores norte e nordeste. Como os raios "
              "apagados mudam a cada volume, os produtos feitos com a refletividade filtrada mostram setores "
              "\"bloqueados\" que mudam de um dia para outro. O bloqueio real (relevo e mata) é fixo.",
              "<b>Sensibilidade cerca de 25 a 35 dB abaixo do esperado.</b> A menor refletividade detectada é de "
              "~30 dBZ a 20 km, ~38 dBZ a 40 km e ~48 dBZ a 80 km. Chuva fraca e estratiforme não aparece além de "
              "~20 km. Com sinal-ruído baixo, o RhoHV cai, o ZDR fica negativo e a fase diferencial fica ruidosa. "
              "A especificação publicada pelo fabricante para o protótipo de 100 W é de 18 dBZ a 50 km; este "
              "radar (410 W) mede ~41 dBZ a 50 km, 22–29 dB pior. Isso indica defeito ou configuração "
              "(compressão de pulso, pulso de preenchimento, perdas ou receptor), não um limite do equipamento.",
              "<b>ZDR descalibrado</b> (mediana negativa em chuva, quando deveria ser positiva) e <b>zona cega de "
              "2,2 km</b> em volta do radar, onde todos os raios saem saturados em ~74 dBZ.",
              "<b>Atenuação em banda X e radome molhado.</b> Células fortes perto do radar apagam o que está atrás "
              "delas, em cunha. Com chuva sobre o radar (18 de 47 volumes analisados), o radome molhado reduz o "
              "sinal em todas as direções. Por isso, em dias de chuva intensa, a imagem mostra só os núcleos fortes.",
              "<b>Setor oeste bloqueado pela vegetação</b>, não pelo relevo: o topo do Morro dos Conventos (~69 m) e a "
              "colina a noroeste (~67 m) estão praticamente na mesma altitude do chão do radar (~68 m). A mata (10–17 m em 2012, mais "
              "alta hoje) e obstáculos a menos de 100 m da antena bloqueiam 70–90% do feixe de 0,5° e grande parte "
              "do de 1,4° entre 240° e 340° — a direção do interior e da Serra Geral.",
              "<b>Radar móvel colado no farol e na rede elétrica.</b> A antena fica num reboque, a ~3–4 m do chão, "
              "a ~15 m do farol (que bloqueia ~141–153° em todas as elevações) e ao lado de um poste com fios, que "
              "explicam setores estreitos sem eco e o aspecto de \"pente\" das imagens. Por ser móvel, o radar pode "
              "ser afastado desses obstáculos ou levado a um ponto mais alto sem obra civil grande.",
              "<b>Eco fixo a 268–271°</b> (planície, cidade de Araranguá e Serra Geral) visto por uma abertura na "
              "mata. Os prédios de Araranguá (até ~40 m) causam clutter, mas bloqueiam no máximo ~13% do feixe.",
              "<b>Lacunas na transmissão:</b> em 8 horas de 20/11, faltaram volumes em 7 intervalos de mais de "
              "15 min, somando 3 horas (37% do tempo). Também há erro nos metadados de posição e altitude.",
          ])]

    s += [KeepTogether([P("Exemplo: Laguna, 20/11/2026, 8–9 h", ParagraphStyle("h3", parent=h1, fontSize=10, spaceBefore=6)),
          P("Laguna fica a 76 km do radar. A essa distância só são detectados ecos acima de ~45 dBZ (~25 mm/h); "
            "faltaram volumes entre 08:21 e 08:57, justamente quando uma célula de 48–53 dBZ chegava à cidade; e os "
            "5 pluviômetros do Cemaden no município estavam sem dados. Não foi possível saber quanto choveu.")])]

    s += [KeepTogether([P("4. Problemas e soluções", h1),
          tabela([
              ["Problema", "Solução", "Responsável", "Custo / prazo"],
              ["PRF 400/267 Hz: velocidade inútil, filtro apaga chuva", "Alterar para <b>1200/900 Hz</b> (Nyquist ~29 m/s, alcance 125 km)", "Fabricante / operador", "Baixo / imediato"],
              ["Sensibilidade 25–35 dB abaixo do esperado", "Testar potência transmitida, compressão de pulso, perdas (guia, junta rotativa), ruído do receptor; recalibrar", "Fabricante", "<b>A definir pelo diagnóstico</b>"],
              ["ZDR descalibrado", "Varredura vertical (birdbath) em chuva fraca", "Operador", "Baixo / imediato"],
              ["Possível desvio de azimute (2–4°)", "Varredura do Sol", "Operador", "Baixo / imediato"],
              ["Zona cega de 2,2 km", "Ativar pulso curto de preenchimento, se disponível", "Fabricante", "Baixo"],
              ["Lacunas no FTP (37% do tempo em 8 h)", "Rever transmissão e envio dos volumes", "DCSC / TI", "Baixo / imediato"],
              ["Metadados de posição e altitude", "Corrigir configuração do site (−28,934548; −49,362490; antena ~71 m)", "Operador", "Baixo / imediato"],
              ["Farol, poste e fios a poucos metros do radar móvel", "Afastar o reboque ≥ 50–100 m do farol, longe de fios; ou elevá-lo numa plataforma", "DCSC", "Baixo / semanas"],
              ["Bloqueio a oeste por vegetação", "Poda até ~300 m da antena (paliativo, com licença ambiental); antena a <b>25 m</b> (torre ou plataforma) ou reboque num ponto alto (definitivo)", "DCSC", "Médio / meses"],
          ], [4.4 * cm, 6.2 * cm, 2.8 * cm, 3.6 * cm])])]

    s += [P("5. Bloqueio do feixe e altura da antena", h1),
          P("A simulação com o MDS de 1 m do SIGSC mostra que elevar a antena para 25 m acima do solo no local atual "
            "tem o mesmo efeito que transferir o radar para a colina, para o topo do Morro dos Conventos ou para o "
            "Morro das Antenas. No setor oeste, a 30 km, o bloqueio do feixe de 1,4° cai de ~40–75% para ~0%."),
          tabela([
              ["Posição (antena acima do solo)", "Bloqueio médio a 30 km (0,5° / 1,4°)", "Setor oeste a 30 km (0,5° / 1,4°)"],
              ["Atual, como está (~3 m)", "37–42% / 18–28%", "72–87% / 39–74%"],
              ["<b>Atual, torre de 25 m</b>", "<b>14% / 0%</b>", "<b>18% / 0%</b>"],
              ["Topo do Morro dos Conventos, 25 m", "14% / 0%", "17% / 0%"],
              ["Morro das Antenas, 25–35 m", "6–9% / 0–1%", "14–15% / 1%"],
          ], [6.0 * cm, 5.5 * cm, 5.5 * cm]),
          Spacer(1, 6),
          figura(FIG / "v3_pbb_posicoes.png", 13, "Bloqueio simulado com torre de 25 m em cada posição (MDS do SIGSC). "
                 "Cores escuras: maior fração do feixe bloqueada.")]

    s += [P("6. Recomendações, em ordem de prioridade", h1),
          ListFlowable([ListItem(P(t), leftIndent=14) for t in [
              "<b>Solicitar ao fabricante</b>: (a) alteração da PRF para 1200/900 Hz; (b) especificação de sensibilidade "
              "do equipamento (refletividade mínima a 1 km ou a 50 km) e teste de potência, compressão de pulso e "
              "ruído; (c) ativação do pulso de preenchimento da zona cega.",
              "<b>Calibração</b>: varredura vertical para o ZDR e varredura do Sol para o azimute; correção dos "
              "metadados do site.",
              "<b>Transmissão</b>: eliminar as lacunas de envio de volumes ao FTP.",
              "<b>Vistoria no local</b>: medir azimute e distância do farol, do poste e dos fios a partir da antena, "
              "e os obstáculos a menos de 300 m, para escolher onde reposicionar o reboque.",
              "<b>Reposicionar o radar móvel</b> longe do farol e da rede elétrica: é a ação de menor custo para "
              "os setores bloqueados perto da antena.",
              "<b>Decidir a torre de 25 m</b> depois do diagnóstico da sensibilidade: se o radar recuperar a "
              "sensibilidade esperada, a torre o torna um radar de cobertura regional para o sul de SC; se a "
              "sensibilidade for limitação do equipamento, ele permanece útil para chuva moderada a forte até "
              "~40–50 km, como complemento dos radares de banda S.",
          ]], bulletType="1", leftIndent=14, bulletFontName="DV")]

    s += [P("7. Orientação para quem usa os dados hoje", h1),
          lista(["usar a refletividade total (TH), não a filtrada (DBZH), com máscara de RhoHV ≥ 0,8;",
                 "descartar os primeiros 2,2 km e não usar a velocidade radial;",
                 "não usar o ZDR sem correção de deslocamento;",
                 "tratar o setor de 240–340° nas elevações de 0,5° e 1,4° como bloqueado;",
                 "lembrar que ausência de eco além de ~20 km não significa ausência de chuva."])]

    s += [Spacer(1, 10),
          P("Contato técnico: Reinaldo Haas. Relatório completo, dados derivados e scripts em "
            "github.com/reinaldohaas/radar-sc.", ParagraphStyle("fim", parent=peq, fontName="DV-I"))]
    doc.build(s, onFirstPage=rodape, onLaterPages=rodape)
    print(SAIDA)


if __name__ == "__main__":
    main()
