# -*- coding: utf-8 -*-
"""Baixa do FTP da Defesa Civil de SC os volumes de refletividade das últimas N horas e desenha as imagens.

Para cada radar do FTP, baixa os volumes da janela, desenha o PPI de refletividade da elevação mais baixa e grava
recentes/<sigla>/ppi/AAAAMMDD_HHMMSS.png com quadros.csv. No fim, atualiza index.html.
  /<SIGLA>/VOL   Rainbow5, AAAAMMDDHHMMSS00dBZ.vol      (Chapecó)
  /<SIGLA>/HDF5  ODIM_H5, ...-PPIVol-AAAAMMDD-HHMMSS-0000.hdf  (Araranguá, Joinville)

Credenciais (nunca gravadas pelo script), lidas do ambiente ou do arquivo .env desta pasta:
  SDC_FTP_HOST=...
  SDC_FTP_USER=...
  SDC_FTP_PASS=...
O .env está no .gitignore.

Uso:
  python baixar_ftp_sc.py --listar                 # mostra os radares e o último arquivo de cada
  python baixar_ftp_sc.py                          # últimas 6 h de todos os radares
  python baixar_ftp_sc.py --horas 3 --radares CHP
"""
import argparse
import csv
import ftplib
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CACHE = AQUI / "cache_vol"
# Formatos por subpasta: Rainbow5 (Chapecó) e ODIM_H5 (Araranguá, Joinville)
FORMATOS = {
    "VOL": (re.compile(r"^(\d{14})\d{2}dBZ\.vol$"), "%Y%m%d%H%M%S"),
    "HDF5": (re.compile(r"-(\d{8}-\d{6})-\d+\.(?:hdf|h5)$"), "%Y%m%d-%H%M%S"),
}
NOMES = {"CHP": "Chapecó", "LON": "Lontras", "ARA": "Araranguá", "JVE": "Joinville"}


def credenciais():
    env = {}
    arq = AQUI / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8-sig").splitlines():
            if "=" in linha and not linha.lstrip().startswith("#"):
                k, v = linha.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    pegar = lambda k: os.environ.get(k) or env.get(k)
    host, user, senha = pegar("SDC_FTP_HOST"), pegar("SDC_FTP_USER"), pegar("SDC_FTP_PASS")
    if not (host and user and senha):
        raise SystemExit("Faltam credenciais: defina SDC_FTP_HOST, SDC_FTP_USER e SDC_FTP_PASS no ambiente ou em .env")
    return host, user, senha


def radares_no_ftp(ftp, siglas=None):
    """[(sigla, subpasta)] das pastas da raiz que têm subpasta VOL ou HDF5."""
    achados = []
    for nome, eh_pasta in sorted(listar(ftp, "/")):
        if not eh_pasta or (siglas and nome.upper() not in siglas):
            continue
        try:
            subs = {n for n, d in listar(ftp, f"/{nome}") if d}
        except ftplib.all_errors:
            continue
        achados += [(nome, sub) for sub in FORMATOS if sub in subs]
    return achados


def listar(ftp, pasta):
    """[(nome, é_pasta)] numa única chamada: MLSD; em servidores antigos, LIST no formato Unix ou DOS."""
    try:
        return [(n, f.get("type") == "dir") for n, f in ftp.mlsd(pasta, facts=["type"]) if n not in (".", "..")]
    except ftplib.error_perm:
        pass
    linhas = []
    ftp.dir(pasta, linhas.append)
    saida = []
    for ln in linhas:
        partes = ln.split(None, 8)
        if ln[:1] in "d-l" and len(partes) == 9:          # Unix: drwxr-xr-x ... nome
            saida.append((partes[8], ln[0] == "d"))
        elif len(partes) >= 4 and partes[0][:1].isdigit():  # DOS: 11-19-26 10:00PM <DIR> nome
            nome = ln.split(None, 3)[3]
            saida.append((nome, partes[2] == "<DIR>"))
    return [(n, d) for n, d in saida if n not in (".", "..")]


def arvore(ftp,pasta="/", prof=0, saida=None, max_prof=3):
    """Pastas até max_prof níveis; em cada uma, total de arquivos e os 3 primeiros e 3 últimos nomes."""
    raiz = saida is None
    if raiz:
        saida = open(AQUI / "ftp_arvore.txt", "w", encoding="utf-8")
    pastas, arquivos = [], []
    try:
        for n, eh_pasta in listar(ftp, pasta):
            (pastas if eh_pasta else arquivos).append(n)
    except ftplib.all_errors as e:
        saida.write(f"{'  ' * prof}{pasta}  ! {e}\n")
    pastas = [f"{pasta.rstrip('/')}/{n}" for n in sorted(pastas)]
    arquivos.sort()
    amostra = arquivos[:3] + (["..."] + arquivos[-3:] if len(arquivos) > 6 else arquivos[3:])
    saida.write(f"{'  ' * prof}{pasta}  [{len(pastas)} pastas, {len(arquivos)} arquivos] {' '.join(amostra)}\n")
    saida.flush()
    print(f"  {pasta}: {len(pastas)} pastas, {len(arquivos)} arquivos", flush=True)
    if prof < max_prof:
        for p in pastas[:40]:
            arvore(ftp, p, prof + 1, saida, max_prof)
    if raiz:
        saida.close()
        print(f"Estrutura gravada em {AQUI / 'ftp_arvore.txt'}")


def amostra(ftp, sigla):
    """Baixa o arquivo mais recente de /SIGLA/HDF5 e grava a árvore HDF (grupos, datasets, atributos)."""
    import h5py
    import numpy as np
    nomes = sorted(n for n, d in listar(ftp, f"/{sigla}/HDF5") if not d)
    if not nomes:
        raise SystemExit(f"/{sigla}/HDF5 está vazia")
    destino = AQUI / "amostras" / sigla / nomes[-1]  # fora do cache: o fluxo normal apaga o que está em cache_vol
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "wb") as f:
        ftp.retrbinary(f"RETR /{sigla}/HDF5/{nomes[-1]}", f.write)
    linhas = [f"arquivo: {nomes[-1]} ({destino.stat().st_size} bytes)"]

    def attrs(obj, ind):
        for k, v in obj.attrs.items():
            v = v.decode(errors="replace") if isinstance(v, bytes) else v
            if isinstance(v, np.ndarray) and v.size > 8:
                v = f"array{v.shape} {v.dtype} min={np.nanmin(v) if v.dtype.kind in 'fiu' else '-'}"
            linhas.append(f"{ind}  @{k} = {str(v)[:200]}")

    def visitar(nome, obj):
        ind = "  " * nome.count("/")
        if isinstance(obj, h5py.Dataset):
            linhas.append(f"{ind}{nome}  dataset {obj.shape} {obj.dtype}")
        else:
            linhas.append(f"{ind}{nome}/")
        attrs(obj, ind)

    with h5py.File(destino, "r") as h:
        attrs(h, "")
        h.visititems(visitar)
    saida = AQUI / f"amostra_{sigla}.txt"
    saida.write_text("\n".join(linhas[:3000]), encoding="utf-8")
    print(f"{len(linhas)} linhas em {saida}")


def hora_do_arquivo(sub, nome):
    rx, fmt = FORMATOS[sub]
    m = rx.search(nome)
    return datetime.strptime(m.group(1), fmt) if m else None


def volumes(ftp, sigla, sub, inicio, fim):
    """[(datetime UTC, nome)] dos volumes de refletividade na janela."""
    saida = []
    for caminho in ftp.nlst(f"/{sigla}/{sub}"):
        nome = caminho.rsplit("/", 1)[-1]
        t = hora_do_arquivo(sub, nome)
        if t and inicio <= t <= fim:
            saida.append((t, nome))
    return sorted(saida)


def baixar(ftp, sigla, sub, nome):
    destino = CACHE / sigla / nome
    if destino.exists() and destino.stat().st_size > 1000:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    with open(parcial, "wb") as f:
        ftp.retrbinary(f"RETR /{sigla}/{sub}/{nome}", f.write)
    parcial.replace(destino)
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--horas", type=float, default=6)
    ap.add_argument("--radares", nargs="+", help="siglas do FTP (padrão: todas as pastas com VOL ou HDF5)")
    ap.add_argument("--alcance", type=float, default=250, help="raio da imagem em km")
    ap.add_argument("--listar", action="store_true", help="só lista radares e o último volume de cada")
    ap.add_argument("--arvore", action="store_true",
                    help="grava ftp_arvore.txt com as pastas do servidor e alguns arquivos de cada (diagnóstico)")
    ap.add_argument("--amostra", metavar="SIGLA",
                    help="baixa o HDF mais recente de /SIGLA/HDF5 e descreve sua estrutura em amostra_SIGLA.txt")
    a = ap.parse_args()

    host, user, senha = credenciais()
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio = agora - timedelta(hours=a.horas)
    with ftplib.FTP(host, timeout=60) as ftp:
        ftp.login(user, senha)
        del senha
        if a.arvore:
            arvore(ftp)
            return
        if a.amostra:
            amostra(ftp, a.amostra.upper())
            return
        radares = radares_no_ftp(ftp, {r.upper() for r in a.radares} if a.radares else None)
        print(f"Radares: {', '.join(f'{s}/{sub}' for s, sub in radares) or 'nenhum'}")
        print(f"Janela: {inicio:%d/%m %H:%M} a {agora:%d/%m %H:%M} UTC")
        if a.listar:
            for s, sub in radares:
                todos = volumes(ftp, s, sub, datetime(2000, 1, 1), agora + timedelta(days=1))
                ult = todos[-1][1] if todos else "nenhum"
                print(f"  {s}: {len(todos)} volumes dBZ, último {ult}")
            return

        from desenhar_ppi import desenhar  # matplotlib só quando for desenhar
        for s, sub in radares:
            alvos = volumes(ftp, s, sub, inicio, agora)
            pasta = AQUI / "recentes" / s.lower() / "ppi"
            pasta.mkdir(parents=True, exist_ok=True)
            linhas, manter = [], set()
            for i, (t, nome) in enumerate(alvos, 1):
                png = pasta / f"{t:%Y%m%d_%H%M%S}.png"
                try:
                    if not png.exists():
                        vol = baixar(ftp, s, sub, nome)
                        desenhar(vol, png, f"{NOMES.get(s, s)} ({s})", t, a.alcance)
                        vol.unlink()  # a imagem basta; o volume bruto ocupa até 26 MB
                except Exception as e:  # um volume ruim não interrompe os outros
                    print(f"  ! {s} {nome}: {e}")
                    continue
                manter.add(png.name)
                linhas.append([f"{t:%Y-%m-%d %H:%M:%S}", png.name])
                print(f"  {s} [{i}/{len(alvos)}] {t:%H:%M} UTC", flush=True)
            with open(pasta / "quadros.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["data_utc", "arquivo"])
                w.writerows(linhas)
            for velho in pasta.glob("*.png"):
                if velho.name not in manter:
                    velho.unlink()
            for velho in (CACHE / s).glob("*") if (CACHE / s).exists() else []:
                t = hora_do_arquivo(sub, velho.name)
                if t is None or t < inicio:
                    velho.unlink()
            print(f"{s}: {len(linhas)} imagens")

    import gerar_pagina
    gerar_pagina.main()


if __name__ == "__main__":
    main()
