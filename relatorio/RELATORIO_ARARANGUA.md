# Radar meteorológico de Araranguá: diagnóstico, bloqueios do feixe e posição alternativa

**Autor:** Dr. Reinaldo Haas. Análises e scripts desenvolvidos com auxílio do Claude (Anthropic).

Relatório técnico no âmbito do **Termo de Cooperação Técnica nº 007/SDC/2025** entre a Secretaria de Estado da Proteção e Defesa Civil (SDC) e a Universidade Federal de Santa Catarina (UFSC). O objeto do termo é a troca, integração e acesso a dados hidrológicos e meteorológicos, incluindo os do radar meteorológico, via FTP. As atividades 1.2 e 2.1 do Plano de Ação preveem a comparação com produtos de radar e o uso de dados de radar em tempo real.

Versão 3, 20/11/2026. Relevo: **MDT e MDS de 1 m do SIGSC** (MDT das folhas SH-22-X-B-IV-3, SH-22-X-A-VI-4 e SH-22-X-B-IV-1; MDS das folhas B-IV-3 e B-IV-1, levantamento de 2010–2012) e SRTM fora delas.
Dados: volumes do FTP da Defesa Civil de SC, de 16/11 a 20/11/2026 (7 para a validação do bloqueio; 47 para a polarimetria e a sensibilidade).

## Introdução: como este estudo começou

Este trabalho começou em 19/11/2026. Houve relatos de chuva forte no sul de Santa Catarina, e tentei usar os dados do radar de Araranguá, publicados no FTP da Defesa Civil, para verificar essas chuvas e os padrões de precipitação na região. Era um uso simples, o mesmo que se espera de qualquer radar meteorológico: localizar as células, estimar a intensidade e acompanhar o deslocamento. Os dados não permitiram fazer isso.

Já nas primeiras imagens, o que o radar mostrava não fazia sentido:
- **Setores inteiros sem eco** a oeste e a noroeste, na direção do interior e da Serra Geral, justamente de onde vem boa parte dos sistemas.
- **Chuva em forma de "pente":** faixas radiais estreitas, com raios cheios ao lado de raios vazios. Num mesmo setor, a aparência mudava de um volume para o outro e de um dia para o outro.
- **Um disco saturado** de ~74 dBZ em volta do radar, até ~2 km, em todas as direções e com qualquer tempo.
- **Ecos fixos e fortes** na direção da cidade de Araranguá e da Serra Geral, que pareciam chuva sem ser.
- **Velocidade radial sem nenhuma coerência,** inclusive dentro da chuva.
- **Chuva fraca e moderada praticamente ausente** além de 20–30 km. Os núcleos fortes apareciam isolados, sem a chuva estratiforme em volta.
- **Lacunas de dezenas de minutos** entre os volumes publicados.

Os problemas apareceram todos juntos na tentativa de verificar a chuva extrema de 20/11 em Laguna, a 76 km do radar. Essa chuva foi a chegada da piscina fria de um CCM com número excepcional de descargas (ver o exemplo adiante):
- faltavam os volumes justamente do horário em que a célula chegava à cidade;
- àquela distância, o radar só vê ecos acima de ~45 dBZ (~25 mm/h);
- os pluviômetros do Cemaden no município estavam sem dados.

Não foi possível dizer quanto choveu. Um pesquisador do INPE já havia tentado usar o mesmo radar e chegado à mesma conclusão: os dados pareciam "totalmente inconsistentes".

A partir daí, o estudo passou a investigar a causa de cada defeito. Isso envolveu:
- os metadados e as variáveis dos volumes ODIM;
- a qualidade de cada variável por elevação;
- a simulação do bloqueio do feixe com o relevo e a vegetação de 1 m do SIGSC;
- a comparação com a especificação publicada pelo fabricante;
- a análise volume a volume dos raios sem eco;
- uma foto do local, que mostrou o radar móvel ao lado do farol e de um poste da rede elétrica.

### Os erros encontrados

1. **PRF errada para banda X.** Com 400/267 Hz, a velocidade máxima medida é de 3,2 m/s por PRF, menor que a largura espectral da própria chuva. A velocidade sai aleatória (seção 2.1).
2. **Filtro de clutter apagando chuva.** O filtro Doppler depende dessa velocidade aleatória e remove raios inteiros de chuva: em mediana, 44% dos raios com chuva a 0,5°. É a principal causa do "pente" e dos setores que mudam de um dia para o outro (seções 2 e 3.1).
3. **Sensibilidade muito abaixo da especificação.** O radar detecta só ~41 dBZ a 50 km, contra os 18 dBZ especificados pelo fabricante para um protótipo de potência menor: 22–29 dB pior. A chuva fraca e moderada desaparece com a distância, e as variáveis polarimétricas ficam ruidosas (seção 2.2).
4. **ZDR descalibrado,** negativo em chuva, e **zona cega saturada** de 2,2 km, sem o pulso de preenchimento que o projeto prevê (seções 2.2 e 4.2).
5. **Antena baixa, num reboque, cercada de obstáculos.**
   - O farol, a 15 m, bloqueia ~141–153° em todas as elevações.
   - O poste e os fios da rede elétrica cortam o feixe.
   - A mata do Morro dos Conventos bloqueia 70–90% do feixe de 0,5° a oeste (seções 3.3, 4 e 4.1).
6. **Clutter fixo** da cidade e da Serra Geral, visto por uma abertura na mata (seção 3).
7. **Atenuação em banda X e radome molhado,** que apagam o que fica atrás das células fortes e reduzem o sinal quando chove sobre o radar (seção 3.1).
8. **Falhas operacionais:**
   - volumes ausentes no FTP em 37% do tempo, num período de 8 horas;
   - posição e altitude erradas nos metadados;
   - possível desvio de azimute de 2–4° (seções 1 e 4.1).

### Utilidade dos dados hoje

Do jeito que o radar está configurado e instalado, **os dados têm pouca utilidade**:
- **Velocidade radial:** inútil.
- **Refletividade filtrada (DBZH):** perde quase metade dos raios com chuva.
- **Refletividade total (TH):**
  - só mostra chuva moderada a forte perto do radar;
  - nada a oeste em baixa elevação;
  - nada no setor do farol.
- **ZDR e KDP:** não servem sem calibração e com esse nível de sinal-ruído.
- **Estimativa de chuva:** não é possível com confiança além de ~20–30 km. Em parte dos horários, nem há dados.

O radar serve, no máximo, para indicar a presença de núcleos convectivos fortes, sobretudo a leste, sobre o mar, e ao sul. Não serve para quantificar a chuva nem para acompanhar sistemas que chegam do oeste.

**Isso não é inevitável.** Quase todos os problemas são de configuração, calibração e instalação, e não de projeto do equipamento. O caminho:
- corrigir a PRF;
- fazer o fabricante verificar a sensibilidade;
- calibrar o ZDR e o azimute;
- reposicionar o reboque longe do farol e da rede elétrica;
- elevar a antena.

Com isso, o radar pode cumprir o papel para o qual foi adquirido. As seções seguintes detalham cada problema, as evidências e as soluções.

## Os dados são inconsistentes? Tem solução?

Um pesquisador do INPE relatou que tentou usar os dados deste radar e os achou totalmente inconsistentes. O diagnóstico deste relatório confirma a impressão e explica de onde ela vem. **Os dados não são inconsistentes ao acaso:** há causas identificadas, e cada uma tem solução conhecida. Elas se somam, e quem usa o arquivo sem conhecê-las vê um radar que "não bate" com nada.

| O que o usuário vê | Causa | Solução | Quem resolve | Dificuldade |
|---|---|---|---|---|
| Velocidade radial sem sentido; ventos dobrados | PRF de 400/267 Hz em banda X: Nyquist de 3,2 m/s por PRF (seção 2.1) | PRF de 1200/900 Hz | fabricante / operador, por configuração | baixa |
| Raios inteiros de chuva apagados no DBZH; setores "bloqueados" que mudam de um dia para outro | filtro de clutter Doppler trabalhando com velocidade aleatória: apaga em mediana 44% dos raios com chuva a 0,5° (seções 2 e 3.1) | mudar a PRF; até lá, usar TH com máscara de RhoHV | operador / usuário | baixa |
| Chuva fraca ausente; só aparecem núcleos de 30–50 dBZ | sensibilidade ~25–35 dB abaixo do esperado (seção 2.2) | diagnóstico do transmissor, da compressão de pulso, das perdas e do receptor; recalibração | fabricante | **média a alta, depende da causa** |
| RhoHV baixo em chuva; ZDR negativo; ΦDP ruidoso | SNR de 5–8 dB mesmo em chuva moderada; ZDR sem calibração (seções 2.2 e 4.2) | corrigir a sensibilidade; varredura vertical (birdbath) para o ZDR | fabricante / operador | média |
| Disco de ~74 dBZ em volta do radar | zona cega de 2,2 km: o receptor capta o próprio pulso (seção 2) | pulso curto de preenchimento, se o equipamento tiver; senão, descartar os 2,2 km | fabricante / usuário | baixa |
| Setor oeste (interior, Serra Geral) quase sem eco a 0,5° e 1,4° | mata do Morro dos Conventos e do entorno da antena (seções 4 e 4.1) | poda perto da antena (paliativo); torre de 25 m (definitivo) | Defesa Civil | média (obra e licença ambiental) |
| Eco fixo forte a 268–271° (Araranguá, Serra Geral) | clutter visto por uma abertura na mata (seção 3) | filtro de clutter funcionando (depende da PRF) ou mapa de clutter fixo | operador | baixa |
| Séries com buracos | no FTP faltam volumes: em 8 h de 20/11, 7 lacunas de mais de 15 min somam 3 h (37% do tempo) | rever a transmissão e o envio ao FTP | Defesa Civil / TI | baixa |
| Posição e altitude erradas nos arquivos | metadado com a posição 21 m deslocada e altitude de 46 m; a antena fica a ~71 m (seção 1) | corrigir a configuração do site | operador | baixa |
| Azimutes possivelmente deslocados | a janela simulada fica 2–4° antes da observada (seção 4.1) | varredura do Sol | operador | baixa |

### Exemplo: Laguna, 20/11/2026, 8–9 h

Em Laguna foi relatada **chuva extrema** entre 8 e 9 h. Ela corresponde à chegada da **piscina fria** (*cold pool*) de um **Complexo Convectivo de Mesoescala (CCM)**. Nas imagens de satélite, o CCM aparece com um número excepcional de descargas elétricas. É exatamente o tipo de evento que um radar costeiro deveria acompanhar.

![Refletividade do radar de Araranguá na chegada da chuva a Laguna](figuras/laguna_20261120_refletividade.png)

O que o radar de Araranguá mostra:
- **08:18:** chuva de 40–55 dBZ ao sul de Laguna, numa faixa ao longo da costa entre Jaguaruna e Laguna, além da área de chuva sobre o mar a leste do radar.
- **08:57:** um núcleo de **55–65 dBZ** a 1,4°, encostado em Laguna pelo sul, com ~15 × 20 km.

O que ele não mostra:
- **O intervalo decisivo.** O FTP não tem volumes entre 08:21 e 08:57, justamente quando o núcleo entrava na cidade.
- **A chuva estratiforme e a frente de rajada.** Laguna fica a 76 km, onde o radar só detecta ecos acima de ~45 dBZ (~25 mm/h). A chuva estratiforme do CCM e a linha fina da frente de rajada da piscina fria, tipicamente com 10–30 dBZ, ficam invisíveis. O radar mostra só o núcleo, isolado.
- **O interior.** As faixas radiais a noroeste e a oeste, o "pente", são o bloqueio e o filtro de clutter: o CCM vinha do continente, e o radar não o acompanhou até a costa.
- **A intensidade real.** Em banda X, a chuva intensa entre o radar e Laguna atenua o sinal, e o ΦDP é ruidoso demais para corrigir isso.

Também não havia medida em solo: os 5 pluviômetros do Cemaden em Laguna estavam sem dados naquele dia. Resultado: não houve como saber quanto choveu, nem acompanhar a evolução do sistema pelo radar (`chuva_ponto.py`, `figura_laguna.py`, `chuva/Laguna_2026-11-20.*`).

**Então, tem solução?** Sim, e quase tudo sai barato:
- **Configuração (sem obra):** PRF, envio ao FTP, metadados, calibração do ZDR e varredura do Sol resolvem a maior parte das inconsistências que um usuário percebe.
- **Bloqueio a oeste:** tem solução definitiva com a torre de 25 m no lugar atual.

O ponto em aberto é a **sensibilidade**. Ela está 22–29 dB abaixo da especificação publicada pelo próprio fabricante (18 dBZ a 50 km no protótipo de 100 W), o que torna mais provável um defeito ou erro de configuração que um limite do equipamento (seção 2.2):
- **Se for defeito** (compressão de pulso desligada, transmissor com pouca potência, perda na junta rotativa ou no guia de onda), conserta-se, e o radar passa a ver a chuva fraca até ~60–80 km.
- **Se for o limite do próprio equipamento**, o radar continua útil para chuva moderada a forte até ~40–50 km, como complemento local dos radares de banda S (Morro da Igreja), mas não como radar de cobertura regional.

Por isso o primeiro passo é pedir ao fabricante a especificação de sensibilidade (Zmin a 1 km ou a 50 km) e um teste de potência e de ruído. Só depois disso dá para dizer se vale a obra da torre.

**Enquanto isso, para quem usa os dados:**
- usar TH, não DBZH, com máscara de RhoHV ≥ 0,8 suavizado;
- descartar os 2,2 km iniciais;
- não usar a velocidade;
- não usar o ZDR sem corrigir o deslocamento;
- tratar o setor de 240–340° a 0,5° e 1,4° como bloqueado;
- lembrar que "sem eco" além de ~20 km não quer dizer "sem chuva".

## Resumo

1. **A configuração do radar inutiliza o Doppler.** A PRF de 400/267 Hz em banda X dá velocidade de Nyquist de 6,4 m/s. A velocidade sai aleatória e o filtro de clutter, que depende dela, apaga raios inteiros de chuva. A recomendação é passar para **1200/900 Hz**: Nyquist estendido de ~29 m/s e 125 km de alcance sem ambiguidade, que cobre os 120 km processados (seção 2.1).
2. **Quem bloqueia o oeste é a mata do Morro dos Conventos, não o relevo.** No MDT, o topo do morro fica só 1,4 m acima do chão do radar, e só com o terreno o oeste fica livre a 1,4°. Com 15–20 m de mata sobre o terreno, a simulação reproduz o que os volumes mostram: no setor oeste (240–340°), a 30 km, 74–80% do feixe de 1,4° e 87–90% do de 0,5° ficam bloqueados. É a direção do interior e da Serra Geral. O MDS confirma que é mata: 10–17 m de árvores na crista a NW e no topo do morro (em 2012). Mas a mata de 2012 sozinha explica só parte da falta de eco a 1,4°; a de hoje é mais alta, ou há obstáculos a menos de 100 m da antena (seção 4.1).
3. **Araranguá aparece como eco de clutter, não como bloqueio.** Há eco forte e fixo a 268–271°, de 2 a 14 km (planície, estrada e cidade) e de 42 a 58 km (Serra Geral). Ele só aparece por uma "janela" de ~4°, provavelmente a abertura da estrada na mata. Prédios a 12 km não bloqueiam o feixe de forma relevante: mesmo um prédio de 80 m taparia no máximo ~32% do feixe de 0,5° e ~8% do de 1,4°, num azimute estreito. No MDS, os prédios mais altos no caminho do feixe têm 35–40 m (a 10–12 km) e tapam no máximo ~13% do feixe de 0,5° e nada do de 1,4°.
4. **Uma torre de 25 m resolve o oeste, inclusive no lugar atual.** No MDT, o chão do radar (67,8 m), o topo do Morro dos Conventos (69,2 m) e o topo da colina a NW (67,2 m) estão praticamente na mesma altura. O que bloqueia é a mata, então basta pôr a antena **25 m acima do chão** (pelo menos 5 m acima de mata de 20 m), em qualquer um desses pontos. A 30 km, no setor oeste, o bloqueio a 1,4° cai de 74% para 0–1%.

   | Antena 25 m acima do chão, mata de 15 m | Média, 30 km (0,5° / 1,4°) | Média, 60 km (0,5° / 1,4°) | Oeste, 30 km (0,5° / 1,4°) |
   |---|---|---|---|
   | Atual, -28,93455, -49,36249, antena como está hoje (~3 m) | 42% / 28% | 47% / 31% | 87% / 74% |
   | **Atual, -28,93455, -49,36249, com torre de 25 m** | **14% / 0%** | **32% / 7%** | **18% / 0%** |
   | Topo da colina a NW, -28,92524, -49,37070 | 15% / 0% | 33% / 8% | 19% / 0% |
   | Topo do Morro dos Conventos, -28,93725, -49,36762 | 14% / 0% | 32% / 8% | 17% / 0% |
   | Morro das Antenas, -28,84387, -49,39876 | 6% / 0% | 30% / 9% | 15% / 1% |

   Erguer a antena no lugar atual é a opção mais simples: dá o mesmo resultado que ir para a colina ou para o topo do Conventos, e a 25 m a antena também fica acima do farol. O Morro das Antenas (255 m, 10,7 km a 341° do radar atual) é um pouco melhor perto do radar e, pelo nome, provavelmente já tem acesso e energia (a confirmar). Lá, a torre do radar precisa ficar longe das torres de comunicação existentes, ou acima delas, porque elas também bloqueiam o feixe. O topo do Morro dos Conventos fica a 580 m do radar atual, no mesmo terreno.

5. **O radar quase não detecta ecos fracos.** Em 47 volumes, a menor refletividade detectada é de ~30 dBZ a 20 km, ~38 dBZ a 40 km e ~48 dBZ a 80 km, o que equivale a ~5–10 dBZ a 1 km. Um radar de banda X costuma detectar algo da ordem de −20 a −30 dBZ a 1 km. A chuva fraca e estratiforme (abaixo de 30 dBZ) fica invisível além de ~20 km. Mesmo em chuva de 35–45 dBZ, a relação sinal-ruído fica em 5–8 dB, e por isso o RhoHV sai baixo e o ZDR negativo. Isso precisa ser verificado com o fabricante: potência transmitida, compressão de pulso, nível de ruído e calibração (seção 2.2).
6. **KDP e ZDR ainda não servem para medir o bloqueio.** O método de autoconsistência Z–ΦDP foi aplicado, mas com sinal-ruído tão baixo o resultado é ruído de ±5–10 dB por setor. O ZDR em chuva tem mediana de −0,3 a −1,3 dB, quando deveria ser positivo: precisa de calibração (seção 4.2).

## 1. O radar

| Item | Valor (metadados ODIM) |
|---|---|
| Equipamento | EEC Ranger, software EDGE 6.2.3, banda X (λ = 3,19 cm) |
| Feixe | 2,18° (H) × 2,20° (V); ganho 36,2 dB; potência nominal 410 W |
| Varredura | 5 elevações (0,5°, 1,4°, 2,4°, 3,4°, 4,5°), 360 raios × 3840 bins de 31,25 m (120 km), a cada ~5 min |
| PRF | 400 / 267 Hz (dual-PRF 3:2), Nyquist 6,38 m/s |
| Posição real | -28,934548, -49,362490 |
| Posição nos arquivos | -28,9346, -49,3627 (21 m da real); altitude declarada 46 m |
| Chão no MDT do SIGSC | 67,8 m; o melhor ajuste aos volumes põe a antena ~3 m acima dele |

As altitudes medidas no Google Earth (antena a 49 m, colina a 57 m) ficam ~10–19 m abaixo do MDT nos mesmos pontos. O relatório usa o MDT do SIGSC, que é o levantamento oficial com precisão altimétrica de 1 m.

## 2. Problemas de configuração e processamento

**PRF baixa.** Com PRF de 400 Hz em banda X, mesmo uma chuva com largura espectral de 1,5–2 m/s dá SQI de 0,1–0,3. Nos ecos de chuva (RhoHV ≥ 0,95 e SNR ≥ 20 dB), a velocidade varia entre raios vizinhos tanto quanto um valor sorteado (mediana de 2,7–3,7 m/s, contra 3,7 m/s de um valor aleatório). O filtro de clutter Doppler remove 73% do eco bruto a 0,5° e 25% a 2,4–4,5°, onde quase não há clutter. A PRF de 400 Hz dá 375 km de alcance sem ambiguidade, mas o radar processa só 120 km.

**Zona cega de 2,2 km.** Até 2,17 km todos os raios, em todas as direções, ficam saturados em ~74 dBZ. É o receptor captando o pulso transmitido (14,3 µs de ida e volta). Não há medida real nesse disco.

**Clutter.** Os ecos de 30 dBZ ou mais têm RhoHV mediano de 0,54–0,71 a 0,5°, valor de mar e relevo, não de chuva.

### 2.1 Por que mudar a PRF, e para quanto

A PRF (frequência de repetição de pulsos) define três coisas ao mesmo tempo: a maior velocidade que o radar mede sem ambiguidade, o alcance máximo sem ambiguidade e quantos pulsos entram em cada raio. Em banda X (λ = 3,19 cm), as fórmulas são:

- velocidade de Nyquist: V = λ · PRF / 4;
- alcance sem ambiguidade: R = c / (2 · PRF);
- coerência entre pulsos (SQI) para uma chuva com largura espectral σ: SQI ≈ exp(−8 π² σ² / (λ · PRF)²).

| | Hoje: 400 / 267 Hz | Recomendado: 1200 / 900 Hz |
|---|---|---|
| Nyquist de cada PRF | 3,2 / 2,1 m/s | 9,6 / 7,2 m/s |
| Nyquist estendido (dual-PRF) | 6,4 m/s | ~29 m/s |
| Alcance sem ambiguidade | 375 / 562 km | 125 / 167 km |
| SQI com σ = 1,5 m/s | 0,34 | 0,94 |
| SQI com σ = 2 m/s | 0,14 | 0,81 |
| Pulsos por raio (mesma rotação) | 1× | 3× |

**O problema da PRF atual.** Com 400 Hz em banda X, a velocidade de Nyquist (3,2 m/s em cada PRF) é menor que a própria largura espectral de uma chuva comum, que fica entre 1 e 3 m/s. O espectro ocupa todo o intervalo de Nyquist e os pulsos sucessivos ficam praticamente descorrelacionados. Isso tem três efeitos:

1. **A velocidade sai aleatória.** O SQI fica em 0,1–0,3, como medido nos volumes, e a velocidade varia entre raios vizinhos tanto quanto um valor sorteado. Ventos de 10–40 m/s dobram várias vezes, e nem a extensão dual-PRF (6,4 m/s) consegue desdobrá-los.
2. **O filtro de clutter apaga chuva.** O filtro Doppler remove o que tem velocidade perto de zero. Com um intervalo de Nyquist tão estreito, o entalhe do filtro ocupa boa parte dele, e a chuva dobrada para perto de zero também é apagada. Isso explica os 73% de eco removidos a 0,5° e os 25% removidos a 2,4–4,5°, onde quase não há clutter.
3. **O alcance sobra.** Os 375 km sem ambiguidade são três vezes o que o radar processa (120 km). A PRF baixa não traz nenhuma vantagem aqui.

**Para quanto mudar.** O critério é usar a maior PRF cujo alcance sem ambiguidade ainda cubra os 120 km processados. Com 1200 Hz, ele é de 125 km. Para o modo dual-PRF, a razão 4:3 (1200/900 Hz) dá ~29 m/s de Nyquist estendido, o bastante para os ventos de tempestade da região; a 3:2 (1200/800 Hz) daria só ~19 m/s.

- Ecos de segunda volta, de alvos além de 125 km, ficam fracos em banda X por atenuação e altura do feixe. Mesmo assim, convém ligar a supressão de segunda volta por fase, se o equipamento tiver.
- Com o triplo de pulsos por raio, o ruído das estimativas também cai.

**A confirmar com o fabricante.** A potência de 410 W indica transmissor de estado sólido com compressão de pulso. Se for o caso, a zona cega de 2,2 km (14,3 µs) é a duração do pulso longo, e o ciclo de trabalho a 1200 Hz (~1,7%) deve estar dentro do limite. Esses equipamentos costumam ter um pulso curto de preenchimento para cobrir a zona cega, e vale verificar se ele está ligado.

### 2.2 Sensibilidade muito baixa

A menor refletividade que o radar detecta (Zmin = TH − SNR) foi medida em 47 volumes de 16 a 20/11, a 2,4°, onde há pouco clutter (`sensibilidade_alcance.csv`):

| Distância | Menor TH detectado (1% dos gates) | Zmin | Zmin reduzido a 1 km |
|---|---|---|---|
| 5 km | 27 dBZ | 24 dBZ | 10 dBZ |
| 10 km | 34 dBZ | 31 dBZ | 11 dBZ |
| 20 km | 32 dBZ | 30 dBZ | 4 dBZ |
| 40 km | 39 dBZ | 38 dBZ | 6 dBZ |
| 60 km | 45 dBZ | 44 dBZ | 8 dBZ |
| 100 km | 53 dBZ | 52 dBZ | 12 dBZ |

O Zmin cresce com o quadrado da distância, como esperado; o problema é o nível. Um radar meteorológico de banda X costuma detectar da ordem de −20 a −30 dBZ a 1 km. Aqui o limite é de ~5–10 dBZ, cerca de **25–35 dB a menos**. Os dados mostram isso independentemente do campo SNR: quase não há gates com TH abaixo de 30 dBZ além de 10 km.

**Comparação com a especificação do fabricante.** A EEC publicou as especificações do protótipo Ranger-X1 (artigo da AMS, 94ª reunião anual, 2014):

| Item | Especificação do protótipo | Este radar |
|---|---|---|
| Potência | 100 W | 410 W |
| Forma de onda | pulso longo LFM de 67 µs, comprimido, mais um pulso curto de preenchimento de 2 µs | — |
| Sensibilidade | **18 dBZ a 50 km com SNR de 0 dB** | **~41 dBZ a 50 km com SNR de 0 dB** (medido) |
| PRF | 200 a 2400 Hz | 400 / 267 Hz |

- **Sensibilidade.** Com 410 W, o mesmo projeto deveria chegar a ~12 dBZ a 50 km. Mesmo descontando a diferença entre o pulso de 67 µs do protótipo e o de ~14 µs que a zona cega deste radar sugere, ficaria em ~19 dBZ. O medido fica **22–29 dB abaixo** do que o próprio fabricante especifica. Isso aponta para defeito ou configuração, como compressão de pulso desligada, perdas ou receptor, e não para limite do equipamento.
- **Zona cega.** O pulso de preenchimento existe justamente para cobrir a zona cega do pulso longo. Neste radar, os primeiros 2,2 km saem saturados, o que indica que o pulso de preenchimento não está ativo ou não está funcionando.
- **PRF.** A faixa de 200–2400 Hz comporta os 1200/900 Hz recomendados.

**Consequências:**
- chuva fraca e estratiforme (< 30 dBZ) não aparece além de ~20 km, nem a de 40 dBZ além de ~40 km;
- mesmo em chuva de 35–45 dBZ, o SNR fica em 5–8 dB. Com esse SNR, o RhoHV cai (mediana de 0,88–0,93 em chuva, quando deveria passar de 0,97), o ZDR fica enviesado e o ΦDP fica ruidoso. Parte do "RhoHV de clutter" da seção 2 vem disso;
- a máscara de RhoHV ≥ 0,8 usada nas imagens apaga também chuva fraca de baixo SNR.

**Causas possíveis, a verificar com o fabricante:**
- potência transmitida abaixo dos 410 W nominais;
- compressão de pulso desligada ou com defeito, o que num transmissor de estado sólido custa 20–30 dB;
- perdas no guia de onda ou na junta rotativa;
- ruído do receptor alto;
- constante de calibração errada.

Uma comparação com o radar de Chapecó, ou com o radar do GPM, em chuva comum, separa a calibração de Z da sensibilidade.

## 3. Bloqueios e ecos fixos observados

Fração de pontos com eco (TH ≥ 10 dBZ, 5–40 km), média dos 7 volumes:

| Setor | 0,5° | 1,4° | 2,4° | 3,4° | 4,5° | Causa provável |
|---|---|---|---|---|---|---|
| ~215–300° | sem eco ou forte falta | 60–100% de falta em 255–310° | falta em 295–305° | — | — | mata do topo do Morro dos Conventos |
| 321–324° | 2–5% (vizinhos 40–90%) | 0–1% | 0–1% | 0–2% | 6–7% (vizinhos 8–9%) | mata alta na colina a 1,3 km, ou objeto perto da antena |
| 352–356° | 59–78% (vizinhos 95%) | 0–0,5% (vizinhos 9–21%) | normal | normal | normal | não explicado (vila e árvores ficam abaixo do feixe) |
| a partir de 146° | 0% (antes 8–18%) | — | — | — | — | farol (15 m, topo 8 m acima da antena); depois vem o mar sem eco |

**Ecos fixos a 268–271°** (≥ 35 dBZ em 6 dos 7 volumes):

| Distância | 0,5° | 1,4° | 2,4° | O que é |
|---|---|---|---|---|
| 2–14 km | 91–100% dos pontos | 70–100% | ~0% | planície, Rua Morro dos Conventos, rede elétrica e cidade de Araranguá (centro a 270°, 12 km) |
| 14–42 km | 0–20% | 0% | 0% | — |
| 42–58 km | 49–100% | 32–100% | 0% | escarpa da Serra Geral |

Nesses pontos o RhoHV mediano é de 0,81–0,87 e o SQI de 0,11: alvos fixos, não chuva. Não é interferência de transmissor, que apareceria em todo o alcance. Nos setores vizinhos quase não há eco fixo (0,0–0,7%). A explicação mais provável é uma abertura na mata do morro, na direção da estrada (a Rua Morro dos Conventos sai a ~264°), que deixa o feixe passar só ali.

![Validação por azimute (MDT + mata)](figuras/v2_validacao_azimute.png)

### 3.1 Por que os setores sem eco mudam de um dia para outro

O bloqueio pelo relevo e pela mata é fixo e não muda entre horários. Se as imagens de um dia mostram mais setores "bloqueados" que as de outro, a causa é outra. Volume a volume, em 47 volumes de 16 a 20/11 (`setores_por_volume.py`, `setores_por_volume.csv`):

| Causa | 0,5° | 1,4° |
|---|---|---|
| **Raios com chuva no TH e apagados no DBZH pelo filtro de clutter** | mediana de 37 raios por volume (44% dos raios com chuva), até 58 | mediana de 9 (21%), até 15 |
| Sombras de atenuação (a chuva termina atrás de um núcleo ≥ 45 dBZ enquanto os vizinhos seguem) | mediana de 6, até 17 | mediana de 1, até 21 |
| Volumes com chuva sobre o radar (radome molhado) | 18 de 47 | — |

![Raios apagados pelo filtro, por volume](figuras/v3_setores_por_volume.png)

1. **O filtro de clutter é o principal responsável.** Ele apaga raios inteiros de chuva onde há algum clutter: no setor norte e nordeste (300–50°, terra e a direção de Criciúma e Laguna) e na janela de 268–271°. Como a velocidade é aleatória (seção 2.1), os raios apagados mudam a cada volume. Em produtos feitos com o DBZH, como os de sites públicos de radar, isso aparece como setores "bloqueados" que vão e vêm. Corrige-se com a nova PRF; até lá, usando o TH com máscara de RhoHV.
2. **Atenuação em banda X.** Uma célula forte perto do radar apaga o que está atrás dela, em forma de cunha. Em dias de chuva forte, há mais cunhas.
3. **Radome molhado.** Com chuva sobre o radar, a água no radome atenua o sinal em todas as direções, tipicamente alguns dB em banda X. Somado à sensibilidade já baixa (seção 2.2), isso some com a chuva moderada a dezenas de quilômetros.
4. **Sensibilidade.** A 76 km, onde fica Laguna, só aparecem ecos acima de ~45 dBZ. Num dia de chuva forte, a imagem mostra a célula intensa e quase nada em volta. No mesmo lugar, um dia de chuva moderada parece "sem eco".

### 3.2 Um volume, raio a raio: 19/11/2026, 17:16 UTC

Classificação dos raios desse volume (`raios_bloqueados.py`; linhas para o Google Earth em `kml/raios_20261119_1716_05.kml` e `_14.kml`):

| Classe | 0,5° | 1,4° |
|---|---|---|
| Raios com chuva no TH | 154 | 137 |
| Apagados pelo filtro de clutter (chuva no TH, < 20% dela no DBZH) | 30 | 9 |
| Sem eco, com os vizinhos com chuva, e bloqueio simulado ≥ 50% | 21 | 5 |
| Sem eco, com os vizinhos com chuva, sem bloqueio simulado | 7 | 17 |
| Sombra de atenuação (a chuva termina logo após um núcleo ≥ 45 dBZ) | 10 | 6 |

![Raios classificados, 0,5°](figuras/raios_20261119_1716_05.png)

**As faixas radiais a noroeste e ao norte.** São chuva vista só em raios isolados: alguns passam pelos vãos da mata e dos obstáculos perto da antena, e os vizinhos são bloqueados ou apagados pelo filtro. Com o bloqueio fixo e o filtro somados, a chuva vira um "pente". Os 21 raios sem eco a 0,5° (O e NO) coincidem com o bloqueio simulado pela mata. Os 7 a 0,5° e os 17 a 1,4° sem bloqueio simulado indicam obstáculos que a simulação não vê, porque ficam a menos de 100 m da antena (seção 3.3).

### 3.3 O local da antena: radar móvel ao lado do farol

Uma foto do local mostra o que a simulação não alcança:
- **O radar é uma unidade móvel.** O radome fica sobre um reboque, e a antena está a ~3–4 m do chão. Isso confirma a calibração da seção 4, que pôs a antena ~3 m acima do chão.
- **O farol está a ~15 m da antena, a 147°.** Ele tem uns 3 m de diâmetro e uns 15 m de altura, mais os mastros. Visto da antena, ocupa ~12° de azimute (de ~141° a ~153°), e o topo fica a ~35–45° de elevação. Ele bloqueia esse setor em **todas** as elevações, e é a "sombra a partir de 146°" da seção 3.
- **Poste e fios da rede elétrica passam ao lado do radome.** Um poste a poucos metros bloqueia por completo um setor de alguns graus, e os fios cruzam o feixe. São os candidatos para os setores 321–324° e 352–356°, que nem o MDS explica (seção 4.1), e para os raios isolados sem eco.
- **A mata em volta tem a altura do radome ou mais**, como a calibração já indicava.

**Consequência para a solução.** Por ser um radar móvel, a mudança de lugar sai muito mais barata que uma obra:
- **No mesmo terreno:** afastar o reboque do farol e do poste. O farol bloqueia todos os ângulos até ~40° de elevação, e por isso o radar precisa ficar a pelo menos ~50–100 m dele, num ponto sem fios por perto.
- **Erguer o reboque:** pô-lo numa plataforma ou torre baixa já tira a antena da sombra do poste e dos fios e de parte da mata. A antena só fica totalmente livre a oeste com ~25 m (seção 5).
- **Mudar de lugar:** como é móvel, ele pode ir para uma posição mais alta e livre, como o Morro das Antenas, sem obra civil grande, só com energia e comunicação.

Para posicionar o reboque, é preciso medir no local o azimute e a distância do poste e de cada fio, a partir da antena. Com eles, o mesmo cálculo da seção 4 diz quantos metros de afastamento bastam.

## 4. Simulação do bloqueio

Método: bloqueio parcial do feixe (Bech et al., 2003), com Terra de raio efetivo 4/3, feixe de 2,2° e bloqueio acumulado ao longo do raio.

**Relevo:**
- MDT de 1 m do SIGSC nos primeiros 2 km de cada posição.
- O mesmo MDT reduzido a 5 m, guardando o máximo de cada bloco (o lado seguro), no resto das três folhas.
- SRTM de 30 m fora delas.

As folhas 1:10.000 do SIGSC não declaram nodata e têm nas bordas uma moldura de 0 e −9999 m que se sobrepõe ~270 m à folha vizinha. Na primeira montagem, essa moldura aparecia como uma faixa de 0 m cortando o morro a −49,376° (emenda entre SH-22-X-B-IV-3-SO-D e SE-C). O mosaico agora usa o maior valor nas sobreposições, o que elimina a faixa. Refeitas as contas, nenhum número do relatório mudou: a faixa era um vale falso e ficava fora dos caminhos que bloqueiam o feixe.

Mata e casas entram como altura somada ao terreno em terra firme. Os primeiros 100 m não entram: ali o feixe ainda está em campo próximo.

**Calibração com os volumes observados:**

| Antena acima do chão / mata | Oeste a 30 km, simulado (0,5° / 1,4° / 2,4°) | Correlação com a falta de eco (0,5° / 1,4° / 2,4°) |
|---|---|---|
| 3 m / sem mata | 20% / 0% / 0% | 0,11 / −0,09 / — |
| 3 m / 10 m | 81% / 59% / 41% | 0,29 / 0,19 / — |
| **3 m / 15 m** | **87% / 74% / 63%** | **0,33 / 0,28 / 0,35** |
| 3 m / 20 m | 90% / 80% / 73% | 0,35 / 0,24 / 0,17 |

Sem mata, o MDT não explica a falta de eco a oeste. Com 15–20 m de mata, explica. A correlação de ~0,3 é modesta, porque os 7 volumes têm chuva em lugares diferentes. O setor 321–324° só chega perto do observado (92% a 1,4°) com mata de 25 m na colina (60–75%).

**Curvatura da Terra, refração e difração.** A altura do feixe já inclui a curvatura da Terra e a refração padrão (raio efetivo k·R com k = 4/3). Como a costa tem com frequência super-refração (ar frio e úmido sobre o mar), a simulação foi repetida com k = 1 (sem refração), 2 e 4 (`sensibilidade_refracao.csv`, figura `v2_refracao.png`). Na posição atual, o bloqueio médio a 30 km varia de 41% a 44% a 0,5° e fica em 28% a 1,4°; o do setor oeste não muda (87% / 74%), e a correlação com o observado fica em 0,33–0,34. O motivo é que o bloqueio vem da mata a menos de 1 km, onde a curvatura do feixe é de centímetros. Nas posições novas, a super-refração forte (k = 4) aumenta o bloqueio médio a 60 km e 0,5° em 4–5 pontos (o feixe passa ~100 m mais baixo a 50 km). A difração não está no modelo: na banda X, a 1ª zona de Fresnel tem 4–6 m de raio a 0,6–1,1 km, contra 11–21 m de raio do feixe, então ela só suaviza a borda da sombra.

![Bloqueio a 40 km para cada raio efetivo](figuras/v2_refracao.png)

**Prédios.** O MDT não tem prédios, mas a geometria limita o efeito deles. O centro de Araranguá fica a 12 km, a 11 m de altitude, e a Terra curva ~8,5 m nessa distância. Um prédio de H metros tapa esta fração do feixe:

| Altura do prédio | Topo visto da antena | Feixe de 0,5° | Feixe de 1,4° |
|---|---|---|---|
| 30 m | −0,18° | ~23% | ~5% |
| 50 m | −0,09° | ~26% | ~6% |
| 80 m | +0,06° | ~32% | ~8% |

Cada prédio ocupa uma fração pequena de grau em azimute (20 m a 12 km dá 0,1°). O efeito médio é pequeno; o que os prédios causam é clutter (seção 3).

![Bloqueio simulado: posição atual e as duas alternativas](figuras/v2_pbb_posicoes.png)

## 4.1 Com o MDS: mata e prédios reais

O MDS (modelo digital de superfície) inclui árvores e construções. MDS − MDT dá a altura de cada uma, com 1 m de resolução. Na simulação, a superfície passou a ser o próprio MDS, com filtro mediano 3×3 contra picos isolados (fios, aves, ruído). Fora das folhas do MDS, continua o MDT + 15 m de mata. Script: `analise_mds.py`.

![Altura da mata e das construções (MDS − MDT)](figuras/v3_altura_superficie.png)

**Cuidado com as falésias.** Na falésia do Morro dos Conventos, voltada para o mar, o MDS mostra a parede quase vertical: cai de ~60 m para ~20 m em 10 m. O MDT suaviza a mesma parede numa rampa de ~25 m. A diferença MDS − MDT chega a 40 m e aparecia no mapa como uma faixa verde-escura ao longo da encosta leste, mas não é mata nem construção.

A correção compara o MDS com o terreno mais alto num raio de 3 m, e de 15 m perto de encostas com mais de 30° (`mapa_altura_superficie.py`). Com ela, a mediana da "altura" nas encostas íngremes cai de 7,3 m para zero, e o percentil 95 cai de 21 para 6 m.

A simulação não é afetada pelo artefato, porque usa o próprio MDS, que tem a falésia certa. Só o teste de "crescimento da mata" soma 6 m também nessas paredes, o que superestima um pouco o bloqueio para 200–240°, na direção do mar.

**Altura da superfície nos pontos estudados (2010–2012, corrigida; `mds_altura_pontos.csv`):**

| Ponto | Altura no ponto | Maior valor num raio de 40 m | Sem correção (raio de 40 m) |
|---|---|---|---|
| Radar atual | 2,9 m | 8,7 m | 21,7 m (falésia) |
| Topo da colina a NW | 8,2 m | 14,9 m | 15,4 m |
| Topo do Morro dos Conventos | 4,5 m | 8,9 m | 9,1 m |
| Vila (352–356°) | 0,2 m | 12,2 m | 12,2 m |
| Morro das Antenas | 0,0 m | 13,2 m (torres) | — |
| Centro de Araranguá | 10,4 m | 21,1 m (prédios) | — |

Os topos do morro e da colina estão a ~67–69 m de altitude, quase a mesma do chão do radar (67,8 m). Nenhum ponto do Morro dos Conventos chega perto de 500 m. Onde o relatório fala em 500–700 m, trata-se de **distância** da antena.

O levantamento é de 2010–2012, anterior ao radar: a torre atual não aparece, e a mata cresceu desde então. Por isso a calibração testou um crescimento de 0, 3 e 6 m onde havia vegetação ou construção (`mds_calibracao.csv`):

| Mata | Antena acima do chão | Começo da simulação | Oeste a 30 km (0,5° / 1,4° / 2,4°) | Correlação com o observado (0,5° / 1,4° / 2,4°) |
|---|---|---|---|---|
| MDS de 2012 | 3 m | 100 m | 37% / 8% / 1% | 0,26 / 0,19 / 0,12 |
| MDS + 3 m | 3 m | 100 m | 57% / 19% / 4% | 0,35 / 0,30 / 0,09 |
| **MDS + 6 m** | **3 m** | **100 m** | **72% / 39% / 13%** | **0,36 / 0,34 / 0,23** |
| MDS + 3 m | 3 m | 50 m | 90% / 71% / 46% | 0,32 / 0,19 / 0,19 |
| MDS + 6 m | 10 m | 100 m | 33% / 6% / 1% | 0,24 / 0,15 / — |

![Validação com o MDS](figuras/v3_validacao_azimute.png)

**O que o MDS mostra:**

- **A mata de 2012 não basta.** Ela bloqueia só 8% do feixe de 1,4° no oeste, contra 60–100% de falta de eco observada. O melhor ajuste usa a mata 6 m mais alta que em 2012, com a antena ~3 m acima do chão, e chega a 39%. Para chegar perto do observado (71%), é preciso incluir obstáculos entre 50 e 100 m da antena. A simulação normalmente começa a 100 m, porque mais perto o feixe ainda está em campo próximo. Isso indica que **árvores no entorno imediato do radar** também tapam o feixe, além da mata da crista.
- **"Janela" de 268–271°.** O MDS mostra mata mais baixa (9–14 m, a 270–350 m da antena) na direção da estrada, e a simulação abre uma fresta a 0,5° entre ~262° e 268°. A falta de eco observada abre em 268–271°, 2–4° adiante. Isso confirma que a janela é uma abertura na mata. A diferença de 2–4° pode ser um erro de alinhamento do radar com o norte, a verificar com uma varredura do Sol.
- **Setor 321–324°.** A 0,5°, o feixe é bloqueado a 640–750 m da antena, por mata de 10–17 m na crista que liga o radar à colina, e não pelo topo da colina (1,3 km). A 1,4°, a mata de 2012 não bloqueia (14%). O eco quase nulo observado (0–1%) pede algo mais alto hoje: árvores que cresceram ou um objeto perto da antena.
- **Setor 352–356°.** O MDS não explica o setor: a vila e as árvores em volta (até 12 m) ficam abaixo do feixe. A causa mais provável é um objeto a menos de 100 m da antena, fora do alcance da simulação, como um poste, um mastro, para-raios ou uma árvore no terreno do radar. Precisa de verificação no local.
- **Prédios de Araranguá.** Os mais altos no caminho do feixe (255–285°, 9–15 km) têm 35–40 m, como a 271° e 12,4 km (topo a 41 m de altitude) e a 284° e 10,2 km (44 m). Vistos da antena, ficam 0,7° abaixo do centro do feixe de 0,5°: tapam no máximo ~13% dele e nada do de 1,4°, em faixas de décimos de grau. Pesa mais um morro com mata a 10–11 km, a 266–268° (topo a ~82 m), que tapa ~20–30% do feixe de 0,5° (`mds_cidade.csv`). Os prédios explicam o clutter, não a falta de eco.

![Torre de 25 m com o MDS](figuras/v3_pbb_posicoes.png)

## 4.2 Bloqueio pelos dados polarimétricos (KDP e ZDR)

**Ideia.** A fase diferencial ΦDP (e o KDP, sua derivada) não depende da potência recebida. Quando parte do feixe é bloqueada, a refletividade cai, mas o ΔΦDP acumulado na chuva continua o mesmo. Na chuva, KDP ≈ c·Z^b. Comparando o ΔΦDP medido com o esperado pela refletividade, num azimute bloqueado e num livre, obtém-se a perda de potência em cada azimute: é o método de autoconsistência (Giangrande & Ryzhkov, 2005; Lang et al., 2009). O ZDR serve para outra coisa: em chuva fraca ele vale ~0,2–0,5 dB, então desvios por azimute indicam bloqueio diferencial entre H e V, e o desvio médio indica erro de calibração.

**Aplicação.** Script `analise_polarimetrica.py`, sobre 47 volumes de 16 a 20/11, com as seguintes escolhas:
- gates de chuva com RhoHV ≥ 0,95 e SNR ≥ 10 dB;
- atenuação corrigida com α = 0,28 dB/° e β = 0,04 dB/°;
- b = 0,8;
- referência nos azimutes de 30–200°, a 1,4° e 2,4°.

**Resultado: inconclusivo.** Só 2.173 raios tiveram chuva suficiente (ΔΦDP ≥ 4°), poucos por setor de 5°. A perda estimada oscila de −10 a +7 dB entre setores vizinhos, sem relação com os bloqueios conhecidos (`polarimetria_azimute.csv`, figura `v3_polarimetria.png`). O motivo é o SNR baixo da seção 2.2: o ΦDP tem textura mediana de 4° e cauda de 14°, e vem quantizado em passos de 1,4°. Não houve gates de chuva fraca (20–30 dBZ) com SNR ≥ 10 dB e RhoHV ≥ 0,95, então não foi possível medir o ZDR por azimute.

**ZDR descalibrado.** Na chuva de 35–45 dBZ, o ZDR mediano é de −0,3 a −0,4 dB, quando deveria ser de +0,5 a +1,5 dB. Na de 25–30 dBZ, é de −1,2 dB. Há um erro de calibração de pelo menos ~1 dB, somado ao viés do SNR baixo. A correção é uma **varredura vertical (birdbath)** em chuva fraca, onde o ZDR verdadeiro é zero.

**Quando volta a servir.** Com a sensibilidade corrigida e o ZDR calibrado, o mesmo script mede o bloqueio real de cada azimute a partir de um dia de chuva estratiforme espalhada. É a melhor validação das simulações deste relatório e da correção de bloqueio no produto de chuva.

## 4.3 Chuva forte sobre o radome: a solução é o KDP e o ZDR, que hoje não funcionam

**O problema.** Em banda X, a chuva forte é exatamente quando o radar mais falha:
- a água no radome atenua o sinal em todas as direções;
- cada célula intensa apaga o que está atrás dela;
- a refletividade passa a subestimar a chuva justamente nos eventos extremos.

Foi o que aconteceu na manhã de 20/11, com o CCM sobre o litoral sul: em 18 dos 47 volumes analisados chovia sobre o próprio radar.

**A solução conhecida é a polarimetria.** É para isso que um radar de banda X de dupla polarização existe:
- O **ΦDP**, e o **KDP**, que é a sua derivada, medem fase e não potência. Não são afetados pela atenuação no caminho, pelo radome molhado, pela calibração de Z nem pelo bloqueio parcial do feixe.
- Com o ΦDP, corrige-se a atenuação de Z e de ZDR ao longo do raio (ΔZ ≈ 0,28·ΔΦDP em banda X).
- Com o KDP, estima-se a chuva forte diretamente (R ≈ 19,6·KDP^0,82 mm/h).
- O **ZDR** calibrado completa a estimativa e separa chuva de granizo.

Ou seja, a resposta à chuva forte sobre o radome é **fazer o KDP e o ZDR funcionarem**.

**Por que hoje não dá: o volume de 20/11, 11:20 UTC (08:20 local), com chuva sobre o radar** (`figura_polarimetria_volume.py`, `polarimetria_20261120_1120.csv`):

![Variáveis polarimétricas com chuva sobre o radar](figuras/polarimetria_20261120_1120.png)

| Indicador, em 203 mil gates de chuva de 35–55 dBZ a 0,5° | Medido | Esperado num radar em ordem |
|---|---|---|
| SNR mediano | 8,6 dB | > 20–30 dB |
| RhoHV mediano | 0,94 | ≥ 0,97–0,99 |
| ZDR mediano | 0,0 dB (49% dos gates negativos) | +0,5 a +2 dB, quase nunca negativo |
| KDP mediano medido | 0,24 °/km (19% negativo) | ~0,57 °/km para essa refletividade |
| Ruído do ΦDP (mediana do desvio) | 2,8° | < 1–2° |

No perfil do raio de 82°, com 40–50 dBZ por 50 km, a refletividade pede um ΦDP subindo ~105°. O ΦDP medido sobe só ~20°, e o ZDR fica em torno de zero o caminho inteiro.

**O que não tem conserto em processamento:**
- **O ΦDP e o Z não fecham entre si.** Ou o Z está calibrado alto, ~5 dB pela diferença de KDP, ou o ΦDP é subestimado ou mal processado. Sem saber qual dos dois está errado, nenhuma correção de atenuação é confiável.
- **O ZDR tem desvio desconhecido**, e o viés do SNR baixo varia de gate para gate. Não existe uma constante que o corrija.
- **Com SNR de ~8 dB**, o ruído das estimativas é grande demais para a derivada do ΦDP. O KDP sai negativo em quase um quinto da chuva.
- **A PRF baixa dá poucos pulsos por raio,** o que aumenta o ruído de todas as estimativas.

Nenhum algoritmo aplicado aos arquivos atuais recupera o que o radar não mediu. Isso inclui suavizar mais, mascarar ou trocar os coeficientes. **A correção precisa ser feita no equipamento:**
1. Recuperar a sensibilidade (seção 2.2), para levar o SNR em chuva a 20–30 dB.
2. PRF de 1200/900 Hz (seção 2.1), com o triplo de pulsos por raio.
3. Calibração do ZDR por varredura vertical e conferência da constante de Z.
4. Revisão do processamento do ΦDP no EDGE: fase do sistema, filtragem e cálculo do KDP.

Feito isso, o KDP passa a ser a melhor estimativa de chuva forte desse radar, imune ao radome molhado e ao bloqueio parcial. O script `analise_polarimetrica.py` já está pronto para medir o bloqueio e a calibração assim que os dados permitirem.

## 5. Posições alternativas

Posições estudadas (WGS84; chão pelo MDT do SIGSC; distância e azimute a partir do radar atual):

| Posição | Latitude | Longitude | Chão no MDT | Distância / azimute |
|---|---|---|---|---|
| Atual (radar) | -28,934548 | -49,362490 | 67,8 m | — |
| Topo da colina a NW | -28,925236 | -49,370698 | 67,2 m | 1,31 km / 322° |
| Topo do Morro dos Conventos | -28,937250 | -49,367620 | 69,2 m | 0,58 km / 239° |
| Morro das Antenas | -28,843869 | -49,398756 | 255,1 m | 10,66 km / 341° |

Bloqueio médio, MDT + mata (sensibilidade completa em `sensibilidade_v2.csv` e `sensibilidade_colina.csv`):

| Posição | Antena acima do chão | Mata | Média, 30 km (0,5° / 1,4°) | Média, 60 km (0,5° / 1,4° / 2,4°) | Oeste, 30 km (0,5° / 1,4°) |
|---|---|---|---|---|---|
| Atual | 3 m | 15 m | 42% / 28% | 47% / 31% / 24% | 87% / 74% |
| Atual | 15 m | 20 m | 36% / 17% | 43% / 21% / — | 74% / 46% |
| **Atual** | **25 m** | 10–20 m | **14–15% / 0%** | **32% / 7–8% / —** | **17–19% / 0%** |
| Topo da colina a NW | 15 m | 20 m | 26% / 7% | 43% / 15% / — | 22% / 0% |
| Topo da colina a NW | 25 m | 10–20 m | 15–16% / 0% | 33–34% / 8% / — | 19–20% / 0% |
| Topo do Conventos | 15 m | 20 m | 44% / 24% | 61% / 32% / 16% | 19% / 0% |
| Topo do Conventos | **25 m** | 10–20 m | 14% / 0% | 32% / 8% / 0% | 17% / 0% |
| Morro das Antenas | 15 m | 20 m | 26% / 15% | 46% / 24% / 9% | 16% / 1% |
| **Morro das Antenas** | **25 m** | 10–20 m | **6–7% / 0%** | **29–30% / 9% / 0%** | 15% / 1% |

- **A torre de 15 m falha se a mata em volta tiver 20 m. A de 25 m dá o mesmo resultado com mata de 10 a 20 m.** Acima de 25 m o ganho é desprezível.
- A 60 km, metade do bloqueio que resta a 0,5° vem do próprio feixe, cuja parte de baixo já aponta abaixo do horizonte (9% até sobre mar plano). O resto vem do relevo distante a oeste e noroeste, até a Serra Geral, igual nas duas posições. Nesse setor, o produto de chuva deve usar 1,4° ou 2,4°.
- **Morro das Antenas:** 255 m, provavelmente com acesso e energia (a confirmar), e é um pouco melhor nos primeiros 30 km. As torres de comunicação existentes também bloqueiam o feixe: o radar precisa ficar acima delas ou longe delas. A antena tem ~1 m de diâmetro, e até ~60 m dela (o campo próximo) uma estrutura dessa largura bloqueia o feixe inteiro.
- **Torre no lugar atual:** a colina de 57 m (Google Earth) a NW tem no MDT 67,2 m, a mesma altura do chão do radar. Ela não é obstáculo de relevo; o que bloqueia é a mata em cima dela e no topo do morro. Por isso, levar o radar para a colina não ganha nada sobre erguer a antena onde está. Com 25 m, a antena fica também acima do farol, que hoje tem o topo 8 m acima dela e faz sombra a partir de 146°. É a opção com menos mudança: mesmo terreno, mesma energia e comunicação.
- **Topo do Morro dos Conventos:** fica a 580 m do radar atual, no mesmo morro, e a mudança é menor. A torre precisa passar a mata em volta.
- **Alternativa sem mudar o radar:** manejar a mata do topo do Morro dos Conventos, numa faixa a 500–700 m **de distância** da antena, a sudoeste e oeste. O topo do morro tem ~69 m de altitude, quase a mesma do chão do radar. Isso precisa de avaliação ambiental, porque a área tem vegetação nativa.

**Com o MDS** (mata de 2012 + 6 m; `mds_posicoes.csv`):

| Posição | Torre | Média, 30 km (0,5° / 1,4°) | Média, 60 km (0,5° / 1,4°) | Oeste, 30 km (0,5° / 1,4°) |
|---|---|---|---|---|
| Atual, antena como está (~3 m) | — | 37% / 18% | 45% / 21% | 72% / 39% |
| Atual | 15 m | 17% / 0% | 33% / 8% | 23% / 1% |
| **Atual** | **25 m** | **14% / 0%** | **32% / 7%** | **18% / 0%** |
| Topo da colina a NW | 25 m | 15% / 0% | 33% / 8% | 19% / 0% |
| Topo do Morro dos Conventos | 25 m | 14% / 0% | 32% / 8% | 17% / 0% |
| Morro das Antenas | 15 m | 15% / 8% | 37% / 17% | 16% / 1% |
| Morro das Antenas | 25 m | 9% / 1% | 32% / 10% | 15% / 1% |
| Morro das Antenas | 35 m | 6% / 0% | 29% / 9% | 14% / 1% |

O MDS confirma a conclusão do MDT: **com 25 m, o lugar atual equivale às outras posições do Morro dos Conventos.** No Morro das Antenas, há estruturas de até 13 m num raio de 40 m (as torres existentes). Lá, a torre do radar precisa de 25–35 m para passar por elas.

![Torre de 25 m: atual, colina, Conventos e Morro das Antenas](figuras/v2_pbb_colina.png)

Nas três posições do Morro dos Conventos, mesmo com torre de 25 m, sobra uma cunha bloqueada a ~335–342°, a partir de ~11 km. É o próprio Morro das Antenas (255 m, a 341°), que nenhuma torre baixa na costa consegue passar.

![Morro dos Conventos no MDT de 1 m](figuras/v2_mapa_mdt.png)

### 5.1 Posições, obstáculos e teste das duas propostas

**Coordenadas** (WGS84). Altitudes do SIGSC: MDT é o terreno e MDS é a superfície, com mata e construções de 2010–2012. Distância e azimute são medidos a partir da antena atual (`posicoes_obstaculos.csv`).

| # | Posição ou obstáculo | Latitude | Longitude | Terreno (MDT) | Superfície (MDS) | Altura do objeto | Distância / azimute |
|---|---|---|---|---|---|---|---|
| — | **Radar atual** (reboque, antena ~3 m) | -28,934548 | -49,362490 | 67,7 m | 71,1 m | 3 m | — |
| — | **Proposta 1: topo do Morro dos Conventos** (torre de 25 m) | -28,937250 | -49,367620 | 69,2 m | 74,9 m | 25 m | 583 m / 239° |
| — | **Proposta 2: Morro das Antenas** (torre de 25 m) | -28,843869 | -49,398756 | 255,1 m | 255,6 m | 25 m | 10,66 km / 341° |
| 1 | Farol do Morro dos Conventos | -28,934662 | -49,362405 | 68,5 m | 72,5 m | ~15 m | 15 m / 147° |
| 2 | Poste e fios da rede elétrica | a medir | a medir | | | | ao lado do radome |
| 3 | Crista com mata (setor 321–324°) | -28,929587 | -49,366918 | 65,7 m | 69,9 m | 10–17 m | 699 m / 322° |
| 4 | Colina a NW, com mata | -28,925236 | -49,370698 | 67,4 m | 75,4 m | 8–15 m | 1,31 km / 322° |
| 5 | Vila (setor 352–356°) | -28,922000 | -49,363759 | 1,7 m | 1,8 m | até ~12 m | 1,40 km / 355° |
| 6 | Mata do topo do Morro dos Conventos | -28,937250 | -49,367620 | 69,2 m | 74,9 m | ~5–10 m | 583 m / 239° |
| 7 | Morro com mata a oeste | -28,939924 | -49,471553 | 66,9 m | 81,8 m | ~15 m | 10,65 km / 267° |
| 8 | Prédio mais alto de Araranguá (271°) | -28,932546 | -49,489633 | 2,7 m | 40,6 m | ~38 m | 12,40 km / 271° |
| 9 | Prédio mais alto de Araranguá (284°) | -28,912340 | -49,464070 | 3,2 m | 43,9 m | ~40 m | 10,21 km / 284° |
| 10 | Torres e mata do Morro das Antenas | em volta da proposta 2 | | 255 m | até ~276 m | até ~21 m | 250 m a NNE da proposta 2 |

**Teste das posições.** A simulação usa o MDS + 6 m de mata, por azimute, a cada 1° (`dem/pbb_posicoes_mds.npz`):

| Posição | 0,5°, média a 10 / 30 / 60 km | 0,5°, oeste a 30 / 60 km | 1,4°, média a 30 / 60 km | 1,4°, oeste a 30 / 60 km | Raios ≥ 50% bloqueados a 30 km (0,5° / 1,4°) |
|---|---|---|---|---|---|
| Atual (antena ~3 m) | 31% / 37% / 45% | 72% / 90% | 18% / 21% | 39% / 51% | 107 / 62 |
| **Proposta 1** (topo do Conventos, 25 m) | 3% / 14% / 32% | 17% / 71% | 0% / 8% | 0% / 25% | 5 / 0 |
| **Proposta 2** (Morro das Antenas, 25 m) | 4% / 9% / 32% | 15% / 76% | 1% / 10% | 1% / 29% | 17 / 3 |

![Posições, obstáculos e raios bloqueados (planta)](figuras/v3_posicoes_planta.png)

![Vista 3D das posições e dos obstáculos](figuras/v3_mapa3d_posicoes.png)

**Do litoral à Serra Geral.** O centro do feixe de 0,5° da posição atual, a ~71 m de altitude, foi seguido raio a raio sobre o SRTM até tocar o relevo. Esse cálculo considera só o relevo, sem a mata perto da antena:

| Azimute | Onde o centro do feixe de 0,5° toca o relevo |
|---|---|
| 230–245° (SW, Sombrio e Praia Grande) | não toca até 80 km |
| 250–290° (W, Turvo, Jacinto Machado, Timbé do Sul) | escarpa da Serra Geral, a 53–64 km (700–1.050 m) |
| 295–335° (NW, Criciúma, Urussanga, Lauro Müller) | morros e sopé da Serra, a 35–50 km (520–710 m) |
| 340° | Morro das Antenas, a 10 km |

Por isso, mesmo com a antena livre da mata, a 0,5° o radar só vê até ~50–60 km a oeste. Além disso só restam a elevação de 1,4° e as mais altas, que passam sobre a Serra.

![Do litoral à Serra Geral em 3D](figuras/v3_mapa3d_serra_geral.png)

No Google Earth (`kml/morro_conventos_3d.kmz`), a pasta "Visadas do feixe de 0,5° até a Serra Geral" mostra essas linhas sobre o relevo e as imagens do Google, a cada 5° de azimute. A pasta tem também uma vista pronta do radar para a Serra. Os nomes de todos os locais (radar, propostas e obstáculos) trazem as coordenadas.

**O que o teste mostra:**
- **As duas propostas eliminam o bloqueio próximo.** A 30 km, o feixe de 1,4° fica livre em praticamente todas as direções, e o de 0,5° passa de 107 raios muito bloqueados para 5 na proposta 1 e 17 na proposta 2. O que sobra a 60 km a oeste (71–76% a 0,5°) é a Serra Geral, igual para as duas. Nessa direção, o produto deve usar 1,4° ou mais.
- **Proposta 1 (topo do Conventos).** O único setor bloqueado a 30 km é o de 342–346°, onde fica o próprio Morro das Antenas, a ~11 km. Fica a 583 m do radar atual: o reboque pode ser levado para lá numa torre ou plataforma de 25 m, longe do farol e da rede elétrica.
- **Proposta 2 (Morro das Antenas).** É a melhor a 30 km em média (9% a 0,5°), mas há dois setores bloqueados:
  - **15–30°:** estruturas de ~21 m (em 2012) a 250 m a NNE, provavelmente as torres de comunicação existentes ou mata alta. Com o crescimento da mata, passam da antena de 25 m. Ali é preciso uma torre de **30–35 m**, ou um ponto mais afastado delas.
  - **312–322°:** relevo, a mais de 10 km.
- **O teste confirma a escolha:** como o radar é móvel, a proposta 1 é a de menor custo, porque fica no mesmo morro, perto da energia e da comunicação atuais. A proposta 2 dá a melhor cobertura, mas exige torre mais alta e acerto com os donos das torres existentes.

No Google Earth, o KMZ (`kml/morro_conventos_3d.kmz`) tem as pastas "Posições propostas", com os feixes de 0,5° e 1,4° de cada proposta coloridos pelo bloqueio, e "Obstáculos", com os pontos numerados da tabela acima.

## 6. Limitações

- O MDS é de 2010–2012: a mata cresceu, e o crescimento (6 m no ajuste) é uniforme na simulação. Construções posteriores, inclusive a torre do radar, não aparecem nele.
- A simulação começa a 100 m da antena. Obstáculos mais perto (árvores do terreno, mastros, o farol) só podem ser avaliados no local.
- A validação usa 7 volumes. Com mais horários de chuva bem distribuída, a comparação fica mais firme.
- Para o Morro das Antenas, a simulação não inclui as torres de comunicação existentes.
- As posições precisam de visita: acesso, posse da área, energia, comunicação, vegetação real e torres vizinhas.

## 7. Próximos passos

1. **Pedir ao fabricante a revisão da PRF** para 1200/900 Hz (seção 2.1). É a mudança de maior efeito e não exige obra.
2. **Pedir ao fabricante a verificação da sensibilidade** (seção 2.2): potência transmitida, compressão de pulso, perdas, ruído do receptor e constante de calibração. Comparar a refletividade com Chapecó ou com o GPM.
3. **Calibrar o ZDR** com varredura vertical (birdbath) em chuva fraca, e **conferir o alinhamento em azimute** com varredura do Sol (a janela simulada fica 2–4° antes da observada).
4. **Vistoria no local:** medir a altura da antena acima do chão e fotografar, a partir dela, os setores 321–324°, 352–356° e 260–300°, num raio de 300 m. Procurar árvores, mastros e postes perto da antena.
5. **Poda ou manejo da mata a menos de ~300 m da antena**, se a vistoria confirmar. Fica sujeito a avaliação ambiental.
6. **Torre de 25 m no lugar atual**, a solução definitiva para o oeste.
7. Depois dos itens 1–3, rodar `analise_polarimetrica.py` num dia de chuva espalhada, para medir o bloqueio real pelo ΦDP.
8. Se quiser um levantamento atual da vegetação: MDS mais recente (LiDAR ou drone) num raio de 1 km.

## 8. Como reproduzir

Scripts em `radar-sc/`:

| Script | Função |
|---|---|
| `baixar_ftp_sc.py --amostra ARA --quantas N` | baixa volumes de amostra do FTP |
| `diagnostico_odim.py` | qualidade por elevação (filtro, RhoHV, velocidade, SQI) |
| `comparar_azimutes.py` | falhas fixas x falhas que mudam entre horários |
| `relevo.py`, `relevo_sigsc.py`, `simular_bloqueio.py` | relevo (SRTM e MDT do SIGSC) e simulação do bloqueio |
| `buscar_posicao.py` | busca de posições (versão 1, SRTM) |
| `chuva_ponto.py --lat --lon --nome --data --das --ate` | taxa de chuva num ponto pelo radar (R(Z) e R(KDP)), série e mapa em `chuva/` |
| `analise_polarimetrica.py` | bloqueio pela autoconsistência Z–ΦDP, ZDR por azimute e sensibilidade por distância (`polarimetria_azimute.csv`, `sensibilidade_alcance.csv`, `v3_polarimetria.png`) |
| `mapa_altura_superficie.py` | altura da mata e das construções (MDS − MDT) com correção das falésias (`v3_altura_superficie.png`, `mds_altura_pontos.csv`) |
| `mapa3d_serra_geral.py` | mapa 3D do litoral à Serra Geral (SRTM, cores hipsométricas) com as posições e o feixe de 0,5° |
| `figuras_posicoes_latlon.py` | bloqueio por posição e mapa 3D do Morro dos Conventos, com lat/lon |
| `figura_polarimetria_volume.py ARQUIVO.hdf` | TH, ZDR, ΦDP, KDP, RhoHV e SNR de um volume; ΦDP medido x esperado; diagnósticos |
| `posicoes_obstaculos.py` | coordenadas do radar, das propostas e dos obstáculos; bloqueio por azimute nas três posições; planta e vista 3D |
| `raios_bloqueados.py ARQUIVO.hdf --elev 0.5` | classifica os raios de um volume (filtro, bloqueio, atenuação); figura, CSV e KML |
| `setores_por_volume.py` | raios apagados pelo filtro, sombras de atenuação e chuva sobre o radar, volume a volume (`setores_por_volume.csv`, `v3_setores_por_volume.png`) |
| `analise_mds.py` | versão 3: MDS do SIGSC, calibração, setores, prédios e torres (`mds_*.csv`, `v3_*.png`) |
| `figuras_relatorio_v2.py` | figuras e `sensibilidade_v2.csv` (versão 2, MDT) |
| `posicao_colina.py` | torre no lugar atual e no topo da colina; `sensibilidade_colina.csv`, `v2_pbb_colina.png` |
| `sensibilidade_refracao.py` | bloqueio com k = 1, 4/3, 2 e 4; `sensibilidade_refracao.csv`, `v2_refracao.png` |
| `figuras_relatorio_ararangua.py` | figuras da versão 1 (SRTM) |
| `gerar_kml_bloqueio.py` | KML para conferência no Google Earth |

O MDT do SIGSC é lido de `C:\Users\haas\github\SIGSC\raster\mdt_sigsc` (`ACERVO` em `relevo_sigsc.py`).

Referência: Bech, J., Codina, B., Lorente, J., Bebbington, D. (2003). The sensitivity of single polarization weather radar beam blockage correction to variability in the vertical refractivity gradient. *J. Atmos. Oceanic Technol.*, 20, 845–855.
