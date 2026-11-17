#!/usr/bin/env python3
"""Prepara o vetor simplificado dos municípios de SC para o dashboard 3D.

Uso (uma vez, com o GeoJSON baixado):
    python3 scripts/preparar_mapa.py /tmp/sc_tbrugz.json

Gera banco_dados/sc_municipios.json com polígonos simplificados e centroides.
O arquivo é lido por scripts/relatorio_html.py e embutido no dashboard,
mantendo a geração offline.
"""

import argparse
import json
import math
import unicodedata
from pathlib import Path


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("_", " ").strip()


def rdp(points, eps):
    """Simplificação Ramer-Douglas-Peucker."""
    if len(points) <= 3:
        return points
    x1, y1 = points[0]
    x2, y2 = points[-1]
    dx, dy = x2 - x1, y2 - y1
    den = math.hypot(dx, dy)
    best, idx = -1, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if den == 0:
            d = math.hypot(px - x1, py - y1)
        else:
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / den
        if d > best:
            best, idx = d, i
    if best > eps:
        return rdp(points[:idx + 1], eps)[:-1] + rdp(points[idx:], eps)
    return [points[0], points[-1]]


def centroid(ring):
    """Centroide ponderado pela área do anel externo."""
    area = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area) < 1e-12:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]
    return [cx / (3 * area), cy / (3 * area)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geojson")
    parser.add_argument("--saida", default="banco_dados/sc_municipios.json")
    parser.add_argument("--eps", type=float, default=0.012)
    args = parser.parse_args()

    geo = json.loads(Path(args.geojson).read_text(encoding="utf-8"))
    features = geo.get("features", [])
    mun = []
    for feat in features:
        props = feat.get("properties", {})
        nome = (props.get("name") or props.get("Nome") or props.get("municipio")
                or props.get("NM_MUN") or "").strip()
        geom = feat.get("geometry") or {}
        if not nome or geom.get("type") not in {"Polygon", "MultiPolygon"}:
            continue
        poligonos = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        maior = max((p[0] for p in poligonos if p), key=len)
        simplificado = rdp([tuple(p) for p in maior], args.eps)
        if len(simplificado) < 4:
            continue
        ring = [[round(x, 4), round(y, 4)] for x, y in simplificado]
        mun.append({
            "nome": nome,
            "norm": norm(nome),
            "centro": [round(v, 4) for v in centroid(ring)],
            "ring": ring,
        })

    lons = [p[0] for m in mun for p in m["ring"]]
    lats = [p[1] for m in mun for p in m["ring"]]
    dados = {
        "bounds": [[min(lons), min(lats)], [max(lons), max(lats)]],
        "municipios": mun,
    }
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Municípios: {len(mun)} | pontos: {sum(len(m['ring']) for m in mun)}")
    print(f"Saída: {saida} ({saida.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
