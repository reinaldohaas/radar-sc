# -*- coding: utf-8 -*-
"""Baixa as imagens de radar do DECEA (API REDEMET) das últimas N horas, de agora para trás.

Radares (código REDEMET):
  mi = Morro da Igreja, Urubici (SC)
  sg = Santiago (RS)
  ct = Curitiba / Teixeira Soares (PR)

Requer a chave da API em REDEMET_KEY (https://api-redemet.decea.mil.br). A chave nunca é gravada.
Saída: recentes/<radar>/<produto>/AAAAMMDD_HHMMSS.png e quadros.csv. Quadros mais antigos que a janela são apagados.

Uso:
  $env:REDEMET_KEY = "..."
  python baixar_recentes.py                      # últimas 6 h, Urubici e Santiago, maxcappi
  python baixar_recentes.py --horas 6 --radares mi sg ct --produto maxcappi
  python gerar_pagina.py                         # atualiza a página
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


def baixar(url, destino=None):
    cmd = [CURL, "-s", "-f", "-m", "120", "-A", "Mozilla/5.0", url]
    if destino:
        cmd[1:1] = ["-o", str(destino)]
    for _ in range(3):
        r = subprocess.run(cmd, capture_output=True)
        if not r.returncode:
            return r.stdout
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--horas", type=float, default=6)
    ap.add_argument("--radares", nargs="+", default=["mi", "sg"])
    ap.add_argument("--produto", default="maxcappi")
    a = ap.parse_args()
    key = os.environ.get("REDEMET_KEY")
    if not key:
        raise SystemExit("Defina a variável de ambiente REDEMET_KEY com a chave da API REDEMET.")

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio = agora - timedelta(hours=a.horas)
    for area in a.radares:
        pasta = AQUI / "recentes" / area / a.produto
        pasta.mkdir(parents=True, exist_ok=True)
        quadros = {}
        h = inicio.replace(minute=0, second=0, microsecond=0)
        while h <= agora:
            raw = baixar(API.format(tipo=a.produto, key=key, data=h.strftime("%Y%m%d%H"), area=area))
            try:
                for grupo in (json.loads(raw).get("data", {}).get("radar", []) if raw else []):
                    for r in grupo:
                        if r.get("localidade") == area and r.get("path"):
                            t = datetime.strptime(r["data"], "%Y-%m-%d %H:%M:%S")
                            if inicio <= t <= agora:
                                quadros[r["data"]] = r
            except (ValueError, AttributeError, TypeError):
                pass
            h += timedelta(hours=1)

        manter = set()
        with open(pasta / "quadros.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["data_utc", "arquivo", "lon_min", "lon_max", "lat_min", "lat_max", "lat_center", "lon_center", "url"])
            for data in sorted(quadros):
                r = quadros[data]
                nome = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d_%H%M%S") + ".png"
                destino = pasta / nome
                if not destino.exists() and baixar(r["path"], destino) is None:
                    continue
                manter.add(nome)
                w.writerow([data, nome, r["lon_min"], r["lon_max"], r["lat_min"], r["lat_max"],
                            r["lat_center"], r["lon_center"], r["path"]])
        for velho in pasta.glob("*.png"):
            if velho.name not in manter:
                velho.unlink()
        print(f"{area} {a.produto}: {len(manter)} quadros de {inicio:%d/%m %H:%M} a {agora:%H:%M} UTC em {pasta}")


if __name__ == "__main__":
    main()
