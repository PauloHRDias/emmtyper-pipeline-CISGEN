#!/usr/bin/env python3
"""Gera banco_dados/brasil_geo.json: estados + municípios de todo o Brasil.

Uso:
    python3 scripts/preparar_mapa_brasil.py /tmp/geo_br

Espera `estados.json` (estados do Brasil) e `mun_<codigo>.json` (um por UF,
do projeto tbrugz/geodata-br) no diretório informado. O resultado é embutido
no dashboard pelo scripts/relatorio_html.py.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from preparar_mapa import centroid, norm, rdp  # noqa: E402

UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}


def lipoly(feat, eps):
    """Maior anel de um Polygon/MultiPolygon, simplificado."""
    geom = feat.get("geometry") or {}
    if geom.get("type") not in {"Polygon", "MultiPolygon"}:
        return None
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    candidatos = [p[0] for p in polys if p]
    if not candidatos:
        return None
    ring = rdp([tuple(p) for p in max(candidatos, key=len)], eps)
    if len(ring) < 4:
        return None
    pts = [[round(x, 4), round(y, 4)] for x, y in ring]
    return pts, [round(v, 4) for v in centroid(pts)]


def nome_feature(feat):
    p = feat.get("properties", {})
    for chave in ("name", "NAME", "Nome", "NM_UF", "nome"):
        if p.get(chave):
            return str(p[chave]).strip()
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pasta")
    ap.add_argument("--eps-estado", type=float, default=0.035)
    ap.add_argument("--eps-municipio", type=float, default=0.025)
    ap.add_argument("--saida", default="banco_dados/brasil_geo.json")
    args = ap.parse_args()

    pasta = Path(args.pasta)
    estados_raw = json.loads((pasta / "estados.json").read_text(encoding="utf-8"))
    estados = []
    for feat in estados_raw.get("features", []):
        resultado = lipoly(feat, args.eps_estado)
        if not resultado:
            continue
        ring, centro = resultado
        nome = nome_feature(feat)
        sigla = ""
        p = feat.get("properties", {})
        for chave in ("sigla", "abbreviation", "code", "uf"):
            if p.get(chave):
                sigla = str(p[chave]).strip().upper()[:2]
                break
        estados.append({"nome": nome, "sigla": sigla, "norm": norm(nome),
                        "centro": centro, "ring": ring})

    municipios = {}
    for codigo, sigla in UF.items():
        arquivo = pasta / f"mun_{codigo}.json"
        if not arquivo.is_file():
            continue
        geo = json.loads(arquivo.read_text(encoding="utf-8"))
        lista = []
        for feat in geo.get("features", []):
            resultado = lipoly(feat, args.eps_municipio)
            if not resultado:
                continue
            ring, centro = resultado
            nome = nome_feature(feat)
            if not nome:
                continue
            lista.append({"nome": nome, "norm": norm(nome),
                          "centro": centro, "ring": ring})
        municipios[sigla] = lista

    if not estados:
        raise SystemExit("nenhum estado processado")
    lons = [p[0] for e in estados for p in e["ring"]]
    lats = [p[1] for e in estados for p in e["ring"]]
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "bounds": [[min(lons), min(lats)], [max(lons), max(lats)]],
        "estados": estados,
        "municipios": municipios,
    }
    saida.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    total_mun = sum(len(v) for v in municipios.values())
    total_pts = sum(len(e["ring"]) for e in estados) + sum(len(m["ring"]) for v in municipios.values() for m in v)
    print(f"Estados: {len(estados)} | municípios: {total_mun} | pontos: {total_pts}")
    print(f"UFs com sigla: {[e['sigla'] for e in estados if e['sigla']]}")
    print(f"Saída: {saida} ({saida.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
