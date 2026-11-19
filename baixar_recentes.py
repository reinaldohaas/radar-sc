# -*- coding: utf-8 -*-
"""Baixa as imagens de radar do DECEA (API REDEMET) das últimas N horas e atualiza index.html.

Radares (código REDEMET):
  mi = Morro da Igreja, Urubici (SC)
  sg = Santiago (RS)
  ct = Curitiba / Teixeira Soares (PR)

A chave da API vem de REDEMET_KEY (variável de ambiente) ou de uma linha REDEMET_KEY=... no arquivo .env
desta pasta. O .env está no .gitignore; a chave nunca é gravada pelo script.

Saída: recentes/<radar>/<produto>/AAAAMMDD_HHMMSS.png e quadros.csv. Quadros fora da janela são apagados.

Uso:
  python baixar_recentes.py                          # últimas 6 h, Urubici e Santiago, maxcappi
  python baixar_recentes.py --horas 6 --radares mi sg ct
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
API = "https://api-redemet.decea.mil.br/produtos/radar/{tipo}?api_key={key}&data={data}&area={area}&anima=15"
CURL = shutil.which("curl") or r"C:\Windows\System32\curl.exe"


def chave():
    if os.environ.get("REDEMET_KEY"):
        return os.environ["REDEMET_KEY"].strip()
    env = AQUI / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("REDEMET_KEY="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("Chave ausente: defina $env:REDEMET_KEY ou crie .env com REDEMET_KEY=sua_chave")


def requisitar(url, destino=None):
    """Retorna (código HTTP, corpo). Com destino, grava o corpo no arquivo."""
    cmd = [CURL, "-s", "-m", "120", "-A", "Mozilla/5.0", "-w", "\n%{http_code}", url]
    if destino:
        cmd[1:1] = ["-o", str(destino)]
    for _ in range(3):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            corpo, _, codigo = r.stdout.rpartition(b"\n")
            return int(codigo or 0), corpo
    return 0, b""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--horas", type=float, default=6)
    ap.add_argument("--radares", nargs="+", default=["mi", "sg"])
    ap.add_argument("--produto", default="maxcappi")
    a = ap.parse_args()
    key = chave()

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio = agora - timedelta(hours=a.horas)
    print(f"Janela: {inicio:%d/%m %H:%M} a {agora:%d/%m %H:%M} UTC")
    for area in a.radares:
        pasta = AQUI / "recentes" / area / a.produto
        pasta.mkdir(parents=True, exist_ok=True)
        quadros, erros = {}, []
        h = inicio.replace(minute=0, second=0, microsecond=0)
        while h <= agora + timedelta(hours=1):
            codigo, corpo = requisitar(API.format(tipo=a.produto, key=key, data=h.strftime("%Y%m%d%H"), area=area))
            try:
                resp = json.loads(corpo)
            except ValueError:
                resp = None
            if codigo != 200 or not isinstance(resp, dict):
                msg = resp.get("message") if isinstance(resp, dict) else corpo[:120].decode("utf-8", "replace")
                erros.append(f"{h:%H} UTC: HTTP {codigo} {msg}")
            else:
                for grupo in (resp.get("data") or {}).get("radar") or []:
                    for r in grupo or []:
                        if r.get("localidade") == area and r.get("path"):
                            t = datetime.strptime(r["data"], "%Y-%m-%d %H:%M:%S")
                            if inicio <= t <= agora:
                                quadros[r["data"]] = r
            h += timedelta(hours=1)

        manter = set()
        with open(pasta / "quadros.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["data_utc", "arquivo", "lon_min", "lon_max", "lat_min", "lat_max", "lat_center", "lon_center", "url"])
            for data in sorted(quadros):
                r = quadros[data]
                nome = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d_%H%M%S") + ".png"
                destino = pasta / nome
                if not destino.exists():
                    codigo, _ = requisitar(r["path"], destino)
                    if codigo != 200:
                        destino.unlink(missing_ok=True)
                        erros.append(f"imagem {nome}: HTTP {codigo}")
                        continue
                manter.add(nome)
                w.writerow([data, nome, r["lon_min"], r["lon_max"], r["lat_min"], r["lat_max"],
                            r["lat_center"], r["lon_center"], r["path"]])
        for velho in pasta.glob("*.png"):
            if velho.name not in manter:
                velho.unlink()
        print(f"{area} {a.produto}: {len(manter)} quadros")
        for e in erros[:5]:
            print("   ", e)
        if len(erros) > 5:
            print(f"    ... e mais {len(erros) - 5} erros")

    import gerar_pagina
    gerar_pagina.main()


if __name__ == "__main__":
    main()
