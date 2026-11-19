#!/usr/bin/env python3
"""Gera um dashboard HTML autocontido a partir dos resultados da pipeline.

Lê a tabela consolidada (com ou sem metadados), os laudos do Ollama e o FASTA
do VFDB, e produz um único arquivo HTML com CSS e JavaScript embutidos.
Funciona offline e pode ser aberto diretamente no navegador ou anexado a um
e-mail. Nenhuma dependência externa é necessária.
"""

import argparse
import csv
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

TAGS = {
    "VERMELHO": "[ALERTA VERMELHO]",
    "AMARELO": "[ALERTA AMARELO]",
    "PADRAO": "[PERFIL ENDÉMICO PADRÃO]",
}


def carregar_tabela(caminho):
    with open(caminho, newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def carregar_laudos(caminho):
    """Extrai {ID_Amostra: {tag, texto}} do arquivo de laudos em texto."""
    laudos = {}
    if not caminho or not Path(caminho).is_file():
        return laudos
    linhas = Path(caminho).read_text(encoding="utf-8", errors="replace").splitlines()
    atual = None
    for i, linha in enumerate(linhas):
        match = re.search(r"PROCESSANDO AMOSTRA \(\d+/\d+\):\s*(\S+)", linha)
        if match:
            atual = match.group(1)
            laudos[atual] = {"tag": "", "texto": ""}
            continue
        if atual is None:
            continue
        for chave, tag in TAGS.items():
            if linha.startswith(tag):
                partes = [linha[len(tag):].strip()]
                for seguinte in linhas[i + 1:]:
                    if (not seguinte.strip() or seguinte.startswith("=" * 20)
                            or seguinte.startswith("[Tempo") or "PROCESSANDO AMOSTRA" in seguinte):
                        break
                    partes.append(seguinte.strip())
                laudos[atual] = {
                    "tag": chave,
                    "texto": " ".join(p for p in partes if p).strip(),
                }
                break
    return laudos


def carregar_vfdb(caminho):
    """Mapeia VFG -> (gene, descricao, categoria funcional) a partir do FASTA."""
    banco = {}
    if not caminho or not Path(caminho).is_file():
        return banco
    for linha in Path(caminho).read_text(encoding="utf-8", errors="replace").splitlines():
        if not linha.startswith(">"):
            continue
        cabecalho = linha[1:].strip()
        match_id = re.match(r"^(VFG\d+)", cabecalho)
        if not match_id:
            continue
        vfg = match_id.group(1)
        gene = ""
        match_gene = re.match(r"^VFG\d+(?:\([^)]*\))?\s+\(([^)]+)\)", cabecalho)
        if match_gene:
            gene = match_gene.group(1)
        descricao = cabecalho
        match_desc = re.search(r"\)\s+([^\[]+?)\s*\[", cabecalho)
        if match_desc:
            descricao = match_desc.group(1).strip()
        categoria = "Outros"
        match_cat = re.search(r"\s-\s([^\[\]()]+?)\s*\([A-Z]+\d+\)", cabecalho)
        if match_cat:
            categoria = match_cat.group(1).strip()
        banco[vfg] = {"gene": gene, "descricao": descricao, "categoria": categoria}
    return banco


def valor(row, *chaves, padrao="NA"):
    for chave in chaves:
        val = (row.get(chave) or "").strip()
        if val and val.lower() not in {"nan", "none"}:
            return val
    return padrao


def construir_dados(linhas, laudos, vfdb):
    dados = []
    for row in linhas:
        ident = valor(row, "ID_Amostra", "Amostra")
        genes = [g.strip() for g in valor(row, "Perfil_Virulencia", padrao="").split(";") if g.strip()]
        categorias = Counter()
        for gene in genes:
            info = vfdb.get(gene, {})
            categorias[info.get("categoria", "Outros")] += 1
        data_coleta = valor(row, "Data_Coleta", "Data", padrao="")
        match_mes = re.search(r"(\d{4}-\d{2})", data_coleta)
        mes = match_mes.group(1) if match_mes else "Sem data"
        laudo = laudos.get(ident, {"tag": "", "texto": ""})
        tag = laudo["tag"]
        if not tag:
            emm = valor(row, "Tipo_EMM", padrao="")
            tag = "PADRAO" if emm.startswith("EMM") else "SEM_LAUDO"
        style_qc = valor(row, "Status", padrao="")
        dados.append({
            "id": ident,
            "emm": valor(row, "Tipo_EMM"),
            "n_genes": len(genes),
            "genes": genes[:40],
            "categorias": dict(categorias),
            "municipio": valor(row, "Municipio", "Município"),
            "uf": valor(row, "UF", "UF_Amostra"),
            "data": data_coleta or "NA",
            "mes": mes,
            "sitio": valor(row, "Sitio_Anatomico", "Sítio_Anatomico"),
            "desfecho": valor(row, "Desfecho"),
            "idade": valor(row, "Idade"),
            "sexo": valor(row, "Sexo"),
            "qc": style_qc,
            "contigs": valor(row, "Contigs"),
            "comprimento": valor(row, "Comprimento_Total"),
            "n50": valor(row, "N50"),
            "gc": valor(row, "GC_pct"),
            "tag": tag,
            "laudo": laudo["texto"],
        })
    return dados


CSS = """
:root{--bg:#f3f8fd;--surface:#fff;--ink:#0b2b45;--muted:#6e8ba3;--line:#cfe3f2;
--blue:#0a7fd4;--cyan:#00b8e6;--red:#e8343c;--amber:#f08a24;--green:#00a86b;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);
font:13px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
body{background-image:linear-gradient(rgba(10,127,212,.035) 1px,transparent 1px),
linear-gradient(90deg,rgba(10,127,212,.035) 1px,transparent 1px);background-size:34px 34px}
.scan{position:fixed;inset:0;pointer-events:none;z-index:99;
background:repeating-linear-gradient(0deg,rgba(0,184,230,.022) 0 1px,transparent 1px 4px)}
::selection{background:#bfeaff;color:#062238}
header{position:relative;background:var(--surface);border-bottom:2px solid var(--cyan);
padding:18px 28px 16px;box-shadow:0 2px 14px rgba(10,80,140,.07)}
.cabecalho-conteudo{display:flex;align-items:center;gap:18px}
.logo-ufsc{width:62px;height:62px;flex:none;filter:drop-shadow(0 0 6px rgba(0,184,230,.45))}
.logo-ufsc svg{display:block;width:100%;height:100%}
header .overline{font:10px/1 var(--mono);letter-spacing:2.4px;color:var(--blue);text-transform:uppercase}
header h1{margin:9px 0 4px;font-size:20px;font-weight:600;letter-spacing:.3px}
header h1 i{font-weight:400;color:var(--blue)}
header p{margin:0;color:var(--muted);font:11px/1.5 var(--mono)}
.status{position:absolute;right:28px;top:20px;font:10px var(--mono);letter-spacing:1.5px;color:var(--green)}
.status b{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);
box-shadow:0 0 8px var(--green);margin-right:7px;animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.35;box-shadow:0 0 2px var(--green)}}
.hud-line{height:1px;background:linear-gradient(90deg,var(--cyan),transparent);margin-top:12px}
main{max-width:1240px;margin:22px auto;padding:0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:13px;margin-bottom:18px}
.card{position:relative;background:var(--surface);border:1px solid var(--line);padding:16px 18px;
box-shadow:0 2px 10px rgba(10,80,140,.05)}
.card::before,.card::after{content:"";position:absolute;width:9px;height:9px;border-color:var(--cyan);border-style:solid}
.card::before{left:-1px;top:-1px;border-width:2px 0 0 2px}
.card::after{right:-1px;bottom:-1px;border-width:0 2px 2px 0}
.card .num{font:600 30px/1.1 var(--mono);color:#072f52;letter-spacing:-1px;text-shadow:0 0 12px rgba(0,184,230,.28)}
.card .lbl{font:10px/1.3 var(--mono);letter-spacing:1.6px;color:var(--muted);text-transform:uppercase;margin-top:8px}
.card.red .num{color:var(--red);text-shadow:0 0 12px rgba(232,52,60,.25)}
.card.green .num{color:var(--green)}
.panel{position:relative;background:var(--surface);border:1px solid var(--line);padding:18px 20px;margin-bottom:16px;
box-shadow:0 2px 10px rgba(10,80,140,.05)}
.panel h2{margin:0 0 14px;font:11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:2px;color:#0a4f85;
display:flex;align-items:center;gap:9px}
.panel h2 .id{display:inline-grid;place-items:center;width:20px;height:20px;background:#e6f6ff;
border:1px solid var(--cyan);color:var(--blue);font:10px var(--mono);letter-spacing:0}
.controles{display:flex;flex-wrap:wrap;gap:9px;align-items:center}
.controles input,.controles select,button{font:12px var(--mono);padding:8px 10px;border:1px solid var(--line);
border-radius:0;background:#fff;color:var(--ink);outline:none}
.controles input:focus,.controles select:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(0,184,230,.12)}
button{cursor:pointer;text-transform:uppercase;letter-spacing:1.2px;font-size:10px;border-color:var(--blue);color:var(--blue)}
button:hover{background:#e9f7ff;box-shadow:0 0 10px rgba(0,184,230,.22)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:840px){.grid2{grid-template-columns:1fr}header .status{position:static;display:block;margin-top:10px}}
svg{width:100%;height:auto;max-height:280px;overflow:visible}
.bar-label{font:10px var(--mono);fill:#17486e}.bar-val{font:10px var(--mono);fill:#5c7f99}
rect.bar{filter:drop-shadow(0 0 4px rgba(0,184,230,.35))}
table{width:100%;border-collapse:collapse;font:12px/1.5 -apple-system,"Segoe UI",Roboto,Arial,sans-serif}
th,td{text-align:left;padding:9px 8px;border-bottom:1px solid #e3eef7;vertical-align:top}
th{background:#eef7ff;color:#0a4f85;font:10px var(--mono);text-transform:uppercase;letter-spacing:1.3px;
border-bottom:1px solid var(--cyan);white-space:nowrap}
tr.amostra:hover{background:#f2fbff}
td:first-child{font:12px var(--mono);color:#073d6b;font-weight:600}
.tag{padding:3px 8px;border:1px solid currentColor;border-radius:2px;font:10px var(--mono);
letter-spacing:.8px;text-transform:uppercase;white-space:nowrap;background:#fff}
.tag.VERMELHO{color:var(--red);box-shadow:0 0 8px rgba(232,52,60,.18)}
.tag.AMARELO{color:var(--amber);box-shadow:0 0 8px rgba(240,138,36,.18)}
.tag.PADRAO{color:var(--green);box-shadow:0 0 8px rgba(0,168,107,.18)}
.tag.SEM_LAUDO{color:var(--muted)}
.detail td{background:#f8fdff;border-left:2px solid var(--cyan)}
.detail .laudo{line-height:1.7;font-size:12px}
.gene{display:inline-block;background:#f0faff;border:1px solid #bfe6f5;color:#0a5f8a;
padding:1px 5px;margin:2px;font:10px var(--mono)}
footer{font:10px/1.6 var(--mono);letter-spacing:.6px;color:var(--muted);text-transform:uppercase;
margin:22px 0;padding-top:12px;border-top:1px solid var(--cyan)}
/* mapa tatico 3D (estilo iDroid / MGSV) */
.panel h2 .expandir{margin-left:auto;border-color:var(--cyan);color:var(--cyan)}
.mapa-panel.expandido{position:fixed;inset:0;z-index:1000;margin:0;overflow:auto;border-radius:0;
box-shadow:0 0 0 100vmax rgba(4,28,48,.55)}
.mapa-panel.expandido .mapa-canvas{height:calc(100vh - 230px)}
.mapa-panel.expandido #mapa{height:100%}
.mapa-controles{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:center;margin-bottom:10px}
.mapa-controles button{min-width:64px}
.mapa-controles input[type=range]{width:190px;accent-color:var(--cyan);padding:0;border:none;background:transparent}
.mapa-status{font:9px var(--mono);letter-spacing:1.2px;color:var(--muted);margin-left:auto;text-transform:uppercase}
.mapa-wrap{position:relative;display:block}
.mapa-palco{position:relative}
.mapa-canvas{position:relative;background:linear-gradient(180deg,#f5fbff,#e4f2ff);
border:1px solid var(--line);overflow:hidden;cursor:grab;height:min(84vh,900px);min-height:620px}
.mapa-canvas:active{cursor:grabbing}
#mapa{height:100%;max-height:none}
.estado{stroke:#79bfe8;stroke-width:1;fill:rgba(10,127,212,.06);cursor:pointer;transition:fill .18s,stroke .18s}
.estado:hover{fill:rgba(0,184,230,.22);stroke:#00b8e6}
.estado.ativo{fill:rgba(0,184,230,.30);stroke:#00b8e6;stroke-width:2;filter:drop-shadow(0 0 7px rgba(0,184,230,.55))}
.estado.inativo{opacity:.28}
.rotulo-estado{font:19px var(--mono);font-weight:700;fill:#0a4f85;pointer-events:none;
paint-order:stroke;stroke:#fff;stroke-width:3px}
/* transicao Brasil -> estado (zoom-blur) */
#cam{transition:transform .55s cubic-bezier(.2,.8,.2,1),filter .55s ease}
.estado{transition:filter .45s ease,opacity .45s ease}
.estado-blur{filter:blur(2.5px);opacity:.28}
.marker-blur{filter:blur(2px);opacity:.3;transition:filter .45s,opacity .45s}
.estado-topo{fill:rgba(0,184,230,.32);stroke:#00b8e6;stroke-width:2;
filter:drop-shadow(0 0 9px rgba(0,184,230,.7))}
.estado-rising{animation:subir 520ms cubic-bezier(.2,.8,.2,1) forwards}
@keyframes subir{from{transform:translateY(0)}to{transform:translateY(-28px)}}
.estado-selecionado polygon:first-child{animation:baseFade 520ms ease-out forwards}
@keyframes baseFade{to{opacity:.35}}
.mun-rise{animation:subirMun 520ms cubic-bezier(.2,.8,.2,1) both}
@keyframes subirMun{from{transform:translateY(0);opacity:0}to{transform:translateY(-28px);opacity:1}}
.faces{animation:facesIn 520ms ease-out both}
@keyframes facesIn{from{opacity:0}to{opacity:1}}
.estado-entrando{animation:entrarFade .5s ease-out both}
@keyframes entrarFade{from{opacity:0}to{opacity:1}}
.legenda{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px;padding:10px;background:#f8fcff;
border:1px solid var(--line)}
.legenda .chip{font:10px var(--mono);letter-spacing:.3px;padding:5px 8px;background:#fff;
border:1px solid #cfe6f5;color:#0a4f85;cursor:pointer;white-space:nowrap}
.legenda .chip:hover{background:#e9f7ff;border-color:var(--cyan);box-shadow:0 0 8px rgba(0,184,230,.25)}
.legenda .chip b{color:#073d6b}
.mapa-canvas::after{content:"";position:absolute;inset:0;pointer-events:none;
background:repeating-linear-gradient(0deg,rgba(0,184,230,.035) 0 1px,transparent 1px 5px)}
.mapa-canvas::before{content:"TOP VIEW // SC-3D // ESCALA TATICA";position:absolute;left:10px;top:8px;
font:9px var(--mono);letter-spacing:1.6px;color:#5f89a6;z-index:2}
#mapa{display:block;width:100%;height:auto}
.mun{stroke:#7abfe6;stroke-width:1;fill:rgba(10,127,212,.05)}
.mun.ativo{fill:rgba(0,184,230,.18);stroke:#00b8e6;stroke-width:1.8}
.mun-side{fill:rgba(0,152,200,.22);stroke:none}
.mun-top{fill:rgba(255,255,255,.78);stroke:#00a8d8;stroke-width:1.4}
.grid-linha{stroke:rgba(10,127,212,.14);stroke-width:.8}
.marker{cursor:pointer}
.marker line{stroke:#00b8e6;stroke-width:1.8}
.marker polygon{fill:#00b8e6;filter:drop-shadow(0 0 5px #00d9ff)}
.marker text{font:16px var(--mono);fill:#073d6b;paint-order:stroke;stroke:#fff;stroke-width:3px}
.marker:hover polygon{fill:#e8343c;filter:drop-shadow(0 0 7px #e8343c)}
.info-box{background:#fff;border:1px solid var(--cyan);padding:14px 14px 14px 16px;
font:11px/1.6 var(--mono);position:absolute;right:12px;top:12px;width:300px;z-index:5;
max-height:calc(100% - 24px);overflow:auto;box-shadow:inset 3px 0 0 var(--cyan),0 4px 18px rgba(4,52,88,.18)}
.info-box.hidden{display:none}
.info-box h3{margin:0 0 10px;font:11px var(--mono);letter-spacing:1.4px;color:#0a4f85;text-transform:uppercase}
.info-box .fechar{position:absolute;right:8px;top:8px;border:1px solid var(--line);background:#fff;
padding:2px 7px;cursor:pointer;font:9px var(--mono)}
.info-box .linha{display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid #e3eef7;padding:3px 0}
.info-box .linha span:first-child{color:var(--muted);text-transform:uppercase;font-size:9px;letter-spacing:1px}
.info-box .laudo{font:11px/1.65 -apple-system,"Segoe UI",sans-serif;margin-top:10px;color:#25455f}
@media print{.scan{display:none}header{box-shadow:none}.controles{display:none}.info-box{display:none}body{background:#fff}}
"""

JS = r"""
const DADOS = JSON.parse(document.getElementById('dados').textContent);
const estado = {q:'', emm:'', municipio:'', alerta:''};
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function popular(id, campo, label){
  const sel = document.getElementById(id);
  const valores = [...new Set(DADOS.map(r => r[campo]))].sort();
  sel.innerHTML = '<option value="">Todos</option>' + valores.map(v => `<option value="${esc(v)}">${esc(v === 'NA' ? label+' não informado' : v)}</option>`).join('');
}

function filtrar(){
  const q = estado.q.toLowerCase();
  return DADOS.filter(r => {
    if (q && !Object.values(r).join(' ').toLowerCase().includes(q)) return false;
    if (estado.emm && r.emm !== estado.emm) return false;
    if (estado.municipio && r.municipio !== estado.municipio) return false;
    if (estado.alerta && r.tag !== estado.alerta) return false;
    return true;
  });
}

function contar(rows, fn){
  const c = {};
  rows.forEach(r => { const k = fn(r); c[k] = (c[k]||0)+1; });
  return Object.entries(c).sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0]));
}

function barras(id, pares, cor){
  if(!pares.length){ document.getElementById(id).innerHTML='<p style="color:#667">Sem dados.</p>'; return; }
  pares = pares.slice(0,12);
  const max = Math.max(...pares.map(p => p[1]));
  const linha = 26, W = 300, L = 96;
  let svg = `<svg viewBox="0 0 ${W} ${pares.length*linha+8}" role="img">`;
  pares.forEach(([rot, val], i) => {
    const w = Math.max(2, (val/max)*(W-L-34));
    const y = i*linha+4;
    svg += `<text x="0" y="${y+13}" class="bar-label">${esc(rot.length>15?rot.slice(0,14)+'…':rot)}</text>`;
    svg += `<rect class="bar" x="${L}" y="${y+3}" width="${w}" height="13" rx="1" fill="${cor}"/>`;
    svg += `<text x="${L+w+4}" y="${y+14}" class="bar-val">${val}</text>`;
  });
  document.getElementById(id).innerHTML = svg + '</svg>';
}

function linha(id, pares){
  pares = pares.filter(p => /^\d{4}-\d{2}$/.test(p[0])).sort((a,b)=>a[0].localeCompare(b[0]));
  if(!pares.length){ document.getElementById(id).innerHTML='<p style="color:#667">Sem datas informadas.</p>'; return; }
  const W=300,H=170,pad=28,max=Math.max(...pares.map(p=>p[1]),1);
  const pts=pares.map((p,i)=>[pad+i*((W-2*pad)/Math.max(1,pares.length-1)), H-pad-(p[1]/max)*(H-2*pad)]);
  let svg=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
  for(let g=0;g<=2;g++){const y=pad+g*(H-2*pad)/2;svg+=`<line x1="${pad}" y1="${y}" x2="${W-pad}" y2="${y}" stroke="#e3e8ee"/>`;}
  svg+='<polyline fill="none" stroke="#0a7fd4" stroke-width="2" points="'+pts.map(p=>p.join(',')).join(' ')+'" style="filter:drop-shadow(0 0 4px rgba(0,184,230,.5))"/>';
  pts.forEach((p,i)=>{svg+=`<circle cx="${p[0]}" cy="${p[1]}" r="3" fill="#00b8e6"/><text x="${p[0]}" y="${H-8}" text-anchor="middle" class="bar-val">${esc(pares[i][0].slice(2))}</text>`;});
  document.getElementById(id).innerHTML=svg+'</svg>';
}

function tabela(rows){
  const corpo=document.getElementById('corpo');
  let out='';
  rows.forEach(r=>{
    out+=`<tr class="amostra" onclick="abrir('${esc(r.id)}')"><td><b>${esc(r.id)}</b></td><td>${esc(r.emm)}</td>`+
      `<td>${esc(r.municipio)}</td><td>${esc(r.data)}</td><td>${esc(r.sitio)}</td><td>${esc(r.desfecho)}</td>`+
      `<td>${r.n_genes}</td><td>${esc(r.qc)}</td><td><span class="tag ${esc(r.tag)}">${esc(r.tag==='PADRAO'?'Padrão':r.tag)}</span></td></tr>`;
    out+=`<tr class="detail" id="d-${esc(r.id)}" style="display:none"><td colspan="9">`+
      `<div class="laudo"><b>Linhagem ${esc(r.emm)}</b> · ${esc(r.n_genes)} genes VFDB · QC ${esc(r.qc)} · `+
      `contigs ${esc(r.contigs)} · ${esc(r.comprimento)} pb · GC ${esc(r.gc)}%<br><br>`+
      (r.laudo?esc(r.laudo):'<i>Sem laudo disponível.</i>')+
      `<br><br><b>Categorias VFDB:</b> `+Object.entries(r.categorias).map(([k,v])=>`${esc(k)} (${v})`).join(' · ')+
      `<br><br><b>Genes:</b> `+r.genes.map(g=>`<span class="gene">${esc(g)}</span>`).join('')+`</div></td></tr>`;
  });
  corpo.innerHTML=out || '<tr><td colspan="9">Nenhuma amostra corresponde aos filtros.</td></tr>';
  document.getElementById('contador').textContent=`${rows.length} de ${DADOS.length} amostras`;
}

function abrir(id){
  const el=document.getElementById('d-'+id);
  if(el) el.style.display = el.style.display==='none' ? 'table-row' : 'none';
}

/* ---- Mapa tatico 3D: Brasil -> estado (estilo iDroid / MGSV) ---- */
const GEO = JSON.parse(document.getElementById('geo').textContent || '{}');
const ELEV = 28;
let rot = 0, zoom = 1, ufAtiva = null, animarSubida = false, zoomBlurAtivo = false;
let boundsAtuais = GEO.bounds || [[-74,-34],[-34,5]];
const CX = 650, CY = 460, MW = 700, MH = 700;
function normNome(s){
  return String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/_/g,' ').trim();
}
function project(lon,lat,z){
  const b=boundsAtuais;
  const u=(lon-b[0][0])/(b[1][0]-b[0][0]);
  const v=(b[1][1]-lat)/(b[1][1]-b[0][1]);
  const dx=(u-0.5)*MW, dy=(v-0.5)*MH;
  const a=rot*Math.PI/180;
  const rx=dx*Math.cos(a)-dy*Math.sin(a);
  const ry=dx*Math.sin(a)+dy*Math.cos(a);
  return [CX+(rx-ry)*0.78, CY+(rx+ry)*0.38-(z||0)];
}
function anel(ring,z){return ring.map(p=>project(p[0],p[1],z));}
function ptsStr(arr){return arr.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');}
function estadoPorSigla(sigla){return (GEO.estados||[]).find(e=>e.sigla===sigla);}
function boundsDoEstado(sigla){
  const e=estadoPorSigla(sigla);
  if(!e) return GEO.bounds;
  const xs=e.ring.map(p=>p[0]), ys=e.ring.map(p=>p[1]);
  return [[Math.min.apply(null,xs),Math.min.apply(null,ys)],[Math.max.apply(null,xs),Math.max.apply(null,ys)]];
}
function ufDaAmostra(r){
  if(r.uf && r.uf!=='NA') return String(r.uf).toUpperCase().slice(0,2);
  const k=normNome(r.municipio);
  for(const sigla in (GEO.municipios||{})){
    if(((GEO.municipios||{})[sigla]||[]).some(m=>m.norm===k)) return sigla;
  }
  return '';
}
function municipioDaAmostra(r,sigla){
  const k=normNome(r.municipio);
  return (((GEO.municipios||{})[sigla]||[]).find(m=>m.norm===k)) || null;
}
function marcador(r,centro,indice,uf){
  const p=project(centro[0],centro[1],ELEV);
  const bx=p[0], by=p[1], ty=by-42-indice*38;
  const cor=r.tag==='VERMELHO'?'#e8343c':r.tag==='AMARELO'?'#f08a24':'#00a86b';
  return `<g class="marker" data-uf="${esc(uf||'')}" onclick="abrirInfo('${esc(r.id)}')">`+
    `<line x1="${bx}" y1="${by}" x2="${bx}" y2="${ty+8}"/>`+
    `<polygon points="${bx},${ty-8} ${bx+8},${ty} ${bx},${ty+8} ${bx-8},${ty}"/>`+
    `<text x="${bx+14}" y="${ty-2}">${esc(r.id)}</text>`+
    `<text class="tag-label" style="fill:${cor};font-weight:700" x="${bx+14}" y="${ty+17}">[${esc(r.tag)}]</text>`+
    `</g>`;
}

function desenharMapa(rows){
  const svg=document.getElementById('mapa');
  if(!svg || !GEO.estados) return;
  boundsAtuais = ufAtiva ? boundsDoEstado(ufAtiva) : GEO.bounds;
  const b=boundsAtuais;
  let s='';
  for(let i=0;i<=10;i++){
    const lon=b[0][0]+i/10*(b[1][0]-b[0][0]);
    const lat=b[0][1]+i/10*(b[1][1]-b[0][1]);
    const a=project(lon,b[0][1],-8),c=project(lon,b[1][1],-8);
    const d=project(b[0][0],lat,-8),e=project(b[1][0],lat,-8);
    s+=`<line class="grid-linha" x1="${a[0]}" y1="${a[1]}" x2="${c[0]}" y2="${c[1]}"/>`;
    s+=`<line class="grid-linha" x1="${d[0]}" y1="${d[1]}" x2="${e[0]}" y2="${e[1]}"/>`;
  }
  if(!ufAtiva){
    const porUF={};
    rows.forEach(r=>{const uf=ufDaAmostra(r); if(uf){(porUF[uf]=porUF[uf]||[]).push(r);}});
    GEO.estados.forEach(e=>{
      const pt=project(e.centro[0],e.centro[1],0);
      s+=`<g class="estado${(porUF[e.sigla]||[]).length?' ativo':''}" data-sigla="${e.sigla}" onclick="entrarEstado('${e.sigla}')">`+
         `<polygon points="${ptsStr(anel(e.ring,0))}"/>`+
         `<text class="rotulo-estado" x="${pt[0]}" y="${pt[1]}">${esc(e.sigla)}</text></g>`;
    });
    const porCidade={};
    rows.forEach(r=>{
      const uf=ufDaAmostra(r);
      const m=municipioDaAmostra(r,uf);
      const e=estadoPorSigla(uf);
      const centro=m?m.centro:(e?e.centro:null);
      if(!centro) return;
      const k=uf+'|'+normNome(r.municipio);
      (porCidade[k]=porCidade[k]||{centro:centro,amostras:[]}).amostras.push(r);
    });
    Object.keys(porCidade).forEach(k=>{
      porCidade[k].amostras.slice(0,4).forEach((r,i)=>{s+=marcador(r,porCidade[k].centro,i,ufDaAmostra(r));});
    });
  } else {
    const muns=(GEO.municipios||{})[ufAtiva]||[];
    const porCidade={};
    rows.filter(r=>ufDaAmostra(r)===ufAtiva).forEach(r=>{
      const k=normNome(r.municipio);
      (porCidade[k]=porCidade[k]||[]).push(r);
    });
    let idxAtivo=0;
    muns.forEach(m=>{
      const ativos=porCidade[m.norm]||[];
      const base=anel(m.ring,0);
      const topoGeo=anel(m.ring,ELEV);
      const atraso=idxAtivo*70;
      let lados='';
      if(ativos.length){
        for(let i=0;i<base.length-1;i++){
          lados+=`<polygon class="mun-side${animarSubida?' faces':''}" style="animation-delay:${atraso}ms" points="${ptsStr([base[i],base[i+1],topoGeo[i+1],topoGeo[i]])}"/>`;
        }
      }
      const topo=ativos.length&&animarSubida?base:topoGeo;
      s+=`<g>${lados}<polygon class="mun${ativos.length?' ativo':''}" points="${ptsStr(base)}"/>`;
      if(ativos.length) s+=`<polygon class="mun-top${animarSubida?' mun-rise':''}" style="animation-delay:${atraso}ms" points="${ptsStr(topo)}"/>`;
      s+='</g>';
      if(ativos.length) idxAtivo++;
    });
    Object.keys(porCidade).forEach(k=>{
      const m=muns.find(x=>x.norm===k);
      if(!m) return;
      porCidade[k].slice(0,4).forEach((r,i)=>{s+=marcador(r,m.centro,i,ufAtiva);});
    });
  }
  const eSel=ufAtiva?estadoPorSigla(ufAtiva):null;
  const org=eSel?project(eSel.centro[0],eSel.centro[1],0)
                :project((b[0][0]+b[1][0])/2,(b[0][1]+b[1][1])/2,0);
  const escala=zoomBlurAtivo?zoom*1.8:zoom;
  const blr=zoomBlurAtivo?5:0;
  svg.innerHTML='<g id="cam" style="transform-box:view-box;transform-origin:'+org[0].toFixed(1)+'px '+org[1].toFixed(1)+'px;transform:scale('+escala+');filter:blur('+blr+'px)">'+s+'</g>';
}

function animarSelecaoEstado(sigla){
  const svg=document.getElementById('mapa');
  if(!svg){ finalizarEntrada(sigla); return; }
  const grupos=svg.querySelectorAll('.estado');
  for(let i=0;i<grupos.length;i++){
    const g=grupos[i];
    if(g.getAttribute('data-sigla')===sigla){
      g.classList.add('estado-selecionado');
      const poly=g.querySelector('polygon');
      if(poly){
        const topo=poly.cloneNode(true);
        topo.setAttribute('class','estado-topo estado-rising');
        g.appendChild(topo);
      }
      const rotulo=g.querySelector('.rotulo-estado');
      if(rotulo) rotulo.setAttribute('class','rotulo-estado estado-rising');
    } else {
      g.classList.add('estado-blur');
    }
  }
  const marks=svg.querySelectorAll('.marker');
  for(let i=0;i<marks.length;i++){
    if(marks[i].getAttribute('data-uf')!==sigla) marks[i].classList.add('marker-blur');
  }
  const eSel=estadoPorSigla(sigla);
  if(eSel){
    const cam=svg.querySelector('#cam');
    if(cam){
      const o=project(eSel.centro[0],eSel.centro[1],0);
      cam.style.transition='transform .5s cubic-bezier(.2,.8,.2,1), filter .5s ease';
      cam.style.transformBox='view-box';
      cam.style.transformOrigin=o[0].toFixed(1)+'px '+o[1].toFixed(1)+'px';
      void cam.getBoundingClientRect();
      cam.style.transform='scale(1.8)';
      cam.style.filter='blur(5px)';
    }
  }
  setTimeout(()=>finalizarEntrada(sigla),520);
}
function assentarMapa(){
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const cam=document.getElementById('cam');
    if(cam){ cam.style.transform='scale(1)'; cam.style.filter='blur(0px)'; }
    zoomBlurAtivo=false;
  }));
}
function finalizarEntrada(sigla){
  ufAtiva=sigla; rot=0; zoom=1; animarSubida=true; zoomBlurAtivo=true;
  const sl=document.getElementById('rot'); if(sl) sl.value=0;
  const b=document.getElementById('voltar'); if(b) b.style.display='inline-block';
  renderMapa();
  assentarMapa();
  setTimeout(()=>{animarSubida=false;},1500);
}
function entrarEstado(sigla){
  if(ufAtiva) return;
  animarSelecaoEstado(sigla);
}
function voltarBrasil(){
  ufAtiva=null; rot=0; zoom=1; animarSubida=false; zoomBlurAtivo=true;
  const sl=document.getElementById('rot'); if(sl) sl.value=0;
  const b=document.getElementById('voltar'); if(b) b.style.display='none';
  renderMapa();
  assentarMapa();
  const svg=document.getElementById('mapa');
  if(svg){
    const gs=svg.querySelectorAll('.estado');
    for(let i=0;i<gs.length;i++) gs[i].classList.add('estado-entrando');
  }
}
function statusMapa(){
  const el=document.getElementById('mapa-status');
  if(el) el.textContent=(ufAtiva?('VISÃO '+ufAtiva):'VISÃO BRASIL')+
    ' · ROT '+Math.round(rot)+'° · ZOOM '+zoom.toFixed(2)+'x · '+
    (ufAtiva?'CLIQUE NA LEGENDA':'CLIQUE NUM ESTADO');
}
function renderMapa(){
  desenharMapa(filtrar());
  statusMapa();
}
let pendenteMapa=false;
function agendarMapa(){
  if(pendenteMapa) return;
  pendenteMapa=true;
  requestAnimationFrame(()=>{pendenteMapa=false;renderMapa();});
}
function girar(graus){
  rot=(rot+graus+360)%360;
  const sl=document.getElementById('rot'); if(sl) sl.value=rot;
  agendarMapa();
}
function zoomMapa(fator){
  zoom=Math.max(0.5,Math.min(6,zoom*fator));
  agendarMapa();
}
function toggleExpandir(){
  const p=document.getElementById('painel-mapa');
  if(!p) return;
  const aberto=p.classList.toggle('expandido');
  const b=p.querySelector('.expandir');
  if(b) b.textContent=aberto?'⛶ REDUZIR':'⛶ EXPANDIR';
}
function resetMapa(){
  rot=0; zoom=1;
  const sl=document.getElementById('rot'); if(sl) sl.value=0;
  renderMapa();
}
function desenharLegenda(rows){
  const el=document.getElementById('legenda');
  if(!el) return;
  const itens=rows.filter(r=>r.municipio && r.municipio!=='NA');
  el.innerHTML=itens.length
    ? itens.map(r=>{
        const cor=r.tag==='VERMELHO'?'#e8343c':r.tag==='AMARELO'?'#f08a24':'#00a86b';
        return '<button class="chip" onclick="abrirInfo(\''+esc(r.id)+'\')">'+
          '<b style="color:'+cor+'">●</b> '+esc(r.id)+' · '+esc(r.emm)+' · '+esc(r.municipio)+'</button>';
      }).join('')
    : '<span style="font:10px var(--mono);color:#6e8ba3">Nenhuma amostra com município informado.</span>';
}

function abrirInfo(id){
  const r=DADOS.find(x=>x.id===id);
  if(!r) return;
  document.getElementById('ib-titulo').textContent=r.id+' // '+r.emm;
  document.getElementById('ib-conteudo').innerHTML=
    '<div class="linha"><span>Município</span><b>'+esc(r.municipio)+'</b></div>'+
    '<div class="linha"><span>Data coleta</span><b>'+esc(r.data)+'</b></div>'+
    '<div class="linha"><span>Sítio</span><b>'+esc(r.sitio)+'</b></div>'+
    '<div class="linha"><span>Desfecho</span><b>'+esc(r.desfecho)+'</b></div>'+
    '<div class="linha"><span>QC</span><b>'+esc(r.qc)+'</b></div>'+
    '<div class="linha"><span>Genes VFDB</span><b>'+r.n_genes+'</b></div>'+
    '<div class="linha"><span>Alerta</span><b>'+esc(r.tag)+'</b></div>'+
    '<div class="laudo">'+(r.laudo?esc(r.laudo):'<i>Sem laudo disponível.</i>')+'</div>';
  document.getElementById('info-box').classList.remove('hidden');
}
function fecharInfo(){document.getElementById('info-box').classList.add('hidden');}

function render(){
  const rows=filtrar();
  document.getElementById('k-amostras').textContent=rows.length;
  document.getElementById('k-emm').textContent=new Set(rows.map(r=>r.emm)).size;
  document.getElementById('k-vermelho').textContent=rows.filter(r=>r.tag==='VERMELHO').length;
  document.getElementById('k-qc').textContent=rows.filter(r=>r.qc==='OK').length+'/'+rows.length;
  barras('c-emm',contar(rows,r=>r.emm),'#0a7fd4');
  linha('c-tempo',contar(rows,r=>r.mes));
  barras('c-municipio',contar(rows,r=>r.municipio).filter(p=>p[0]!=='NA'),'#00b8e6');
  const cat={};
  rows.forEach(r=>Object.entries(r.categorias).forEach(([k,v])=>cat[k]=(cat[k]||0)+v));
  barras('c-categorias',Object.entries(cat).sort((a,b)=>b[1]-a[1]),'#0090c8');
  desenharMapa(rows);
  statusMapa();
  desenharLegenda(rows);
  tabela(rows);
}

function exportar(){
  const rows=filtrar();
  const cols=['id','emm','n_genes','municipio','data','sitio','desfecho','qc','tag'];
  const csv=[cols.join('\t'),...rows.map(r=>cols.map(c=>r[c]).join('\t'))].join('\n');
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([csv],{type:'text/tab-separated-values'}));
  a.download='amostras_filtradas.tsv'; a.click(); URL.revokeObjectURL(a.href);
}

window.addEventListener('DOMContentLoaded',()=>{
  popular('f-emm','emm','Tipo emm');popular('f-municipio','municipio','Município');
  ['q','emm','municipio','alerta'].forEach(k=>{
    const el=document.getElementById('f-'+k);
    el.addEventListener(k==='q'?'input':'change',()=>{estado[k]=el.value;render();});
  });
  document.getElementById('limpar').addEventListener('click',()=>{
    ['q','emm','municipio','alerta'].forEach(k=>{document.getElementById('f-'+k).value='';estado[k]='';});
    render();
  });
  document.getElementById('exportar').addEventListener('click',exportar);
  const sl=document.getElementById('rot');
  if(sl) sl.addEventListener('input',()=>{rot=Number(sl.value);agendarMapa();});
  const canvas=document.querySelector('.mapa-canvas');
  if(canvas){
    let arrastando=false, ultimoX=0;
    canvas.addEventListener('mousedown',e=>{arrastando=true;ultimoX=e.clientX;});
    window.addEventListener('mousemove',e=>{
      if(!arrastando) return;
      rot=(rot+(e.clientX-ultimoX)*0.5+360)%360;
      ultimoX=e.clientX;
      if(sl) sl.value=rot;
      agendarMapa();
    });
    window.addEventListener('mouseup',()=>{arrastando=false;});
    canvas.addEventListener('wheel',e=>{
      e.preventDefault();
      zoomMapa(e.deltaY<0?1.12:1/1.12);
    },{passive:false});
    let ultimoTouchX=0;
    canvas.addEventListener('touchstart',e=>{ultimoTouchX=e.touches[0].clientX;},{passive:true});
    canvas.addEventListener('touchmove',e=>{
      rot=(rot+(e.touches[0].clientX-ultimoTouchX)*0.5+360)%360;
      ultimoTouchX=e.touches[0].clientX;
      if(sl) sl.value=rot;
      agendarMapa();
      e.preventDefault();
    },{passive:false});
  }
  render();
});
"""


PIPELINE_CSS = """
.nav-btn{position:absolute;right:150px;top:20px;border:1px solid var(--cyan);color:var(--cyan);
padding:7px 11px;font:10px var(--mono);letter-spacing:1.2px;text-decoration:none;background:#fff}
.nav-btn:hover{background:#e9f7ff;box-shadow:0 0 10px rgba(0,184,230,.25)}
.nav-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.nav-bar a{font:11px var(--mono);letter-spacing:1.4px;color:var(--blue);text-decoration:none;
border:1px solid var(--line);padding:8px 12px;background:#fff}
.nav-bar a:hover{border-color:var(--cyan);background:#e9f7ff}
.grupo-titulo{font:10px var(--mono);letter-spacing:2px;color:var(--muted);text-transform:uppercase;
margin:16px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
.fluxo{display:flex;flex-wrap:wrap;align-items:stretch;gap:7px}
.etapa{flex:1 1 130px;min-width:120px;border:1px solid var(--line);background:#f8fcff;padding:10px;
position:relative}
.etapa::before{content:"";position:absolute;left:-1px;top:-1px;width:8px;height:8px;
border-left:2px solid var(--cyan);border-top:2px solid var(--cyan)}
.etapa b{display:block;font:11px var(--mono);letter-spacing:1px;color:#0a4f85;margin-bottom:4px}
.etapa span{font:10px/1.5 -apple-system,"Segoe UI",sans-serif;color:var(--muted)}
.seta{align-self:center;color:var(--cyan);font:16px var(--mono)}
.cmd{position:relative;margin:12px 0 18px}
.cmd .copiar{position:absolute;right:8px;top:8px;z-index:2;font:9px var(--mono);letter-spacing:1.2px;
border:1px solid var(--cyan);color:var(--cyan);background:#fff;padding:4px 8px;cursor:pointer}
.cmd pre{margin:0;background:#f2f8fd;border:1px solid var(--line);border-left:3px solid var(--cyan);
padding:14px 14px 14px 16px;overflow:auto;font:11px/1.7 var(--mono);color:#0b2b45}
.cmd code{white-space:pre}
.nota{font:11px/1.7 -apple-system,"Segoe UI",sans-serif;color:var(--muted);margin:8px 0 0}
.docs-tabela{width:100%;border-collapse:collapse;font:11px/1.6 -apple-system,"Segoe UI",sans-serif}
.docs-tabela th,.docs-tabela td{border-bottom:1px solid #e3eef7;padding:7px 9px;text-align:left;vertical-align:top}
.docs-tabela th{font:10px var(--mono);letter-spacing:1.2px;color:#0a4f85;background:#eef7ff}
@media(max-width:760px){.nav-btn{position:static;display:inline-block;margin-top:8px}}
"""

PIPELINE_JS = r"""
function copiar(btn){
  const codigo=btn.parentNode.querySelector('code').textContent;
  function ok(){btn.textContent='✓ COPIADO';setTimeout(()=>{btn.textContent='COPIAR';},1600);}
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(codigo).then(ok).catch(()=>fallback(codigo,ok));
  } else { fallback(codigo,ok); }
}
function fallback(txt,ok){
  const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);
  ta.select();try{document.execCommand('copy');ok();}catch(e){}document.body.removeChild(ta);
}
"""


def gerar_html_pipeline(logo, dashboard_url, pipeline_url):
    """Segunda página: fluxo analítico e comandos operacionais, no mesmo estilo HUD."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    def cmd(titulo, texto):
        return (f'<h2><span class="id">{titulo}</span></h2>'
                f'<div class="cmd"><button class="copiar" onclick="copiar(this)">COPIAR</button>'
                f'<pre><code>{html.escape(texto.strip())}</code></pre></div>')
    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CIGenS/SC — Pipeline analítica</title>
<style>{CSS}{PIPELINE_CSS}</style></head><body>
<div class="scan"></div>
<header><div class="cabecalho-conteudo">
<div class="logo-ufsc" title="Universidade Federal de Santa Catarina">{logo}</div>
<div><div class="overline">CIGenS // Documentação operacional · SYS.02</div>
<h1>PIPELINE <i>ANALÍTICA COMPLETA</i></h1>
<p>FLUXO DE PROCESSAMENTO E COMANDOS DE EXECUÇÃO · ATUALIZADO EM {agora}</p></div>
</div><div class="status"><b></b>SISTEMA ONLINE</div>
<a class="nav-btn" href="{html.escape(dashboard_url)}">← DASHBOARD</a><div class="hud-line"></div></header>
<main>
<div class="nav-bar"><a href="{html.escape(dashboard_url)}">← VOLTAR AO DASHBOARD DE RESULTADOS</a>
<span class="lbl">PÁGINA 02 / 02 · OPERAÇÃO E REPRODUÇÃO</span></div>

<div class="panel"><h2><span class="id">00</span> Fluxo analítico completo</h2>
<div class="grupo-titulo">A montante · sequenciamento → assembly (fora do repositório)</div>
<div class="fluxo">
 <div class="etapa"><b>01 CORTE / DNA</b><span>Nanopore MinION · Rapid Barcoding SQK-RBK114.24 · cells R10.4.1</span></div><div class="seta">▸</div>
 <div class="etapa"><b>02 DORADO</b><span>basecalling e controle de qualidade das leituras</span></div><div class="seta">▸</div>
 <div class="etapa"><b>03 FLYE</b><span>montagem de novo do genoma</span></div><div class="seta">▸</div>
 <div class="etapa"><b>04 MEDAKA</b><span>polishing da montagem</span></div><div class="seta">▸</div>
 <div class="etapa"><b>05 QUAST / NANOPLOT</b><span>N50, GC, cobertura e métricas de qualidade</span></div><div class="seta">▸</div>
 <div class="etapa"><b>06 PROKKA</b><span>anotação gênica (CDS, proteínas, elementos não codificantes)</span></div>
</div>
<div class="grupo-titulo">Núcleo do repositório · assembly → resultado publicável</div>
<div class="fluxo">
 <div class="etapa"><b>07 QC</b><span>qc_montagem.py · contigs, tamanho, N50, GC, Ns</span></div><div class="seta">▸</div>
 <div class="etapa"><b>08 EMMTYPER</b><span>emmtyper 0.2.0, workflow BLAST, banco emm.fna → tipo/subtipo emm</span></div><div class="seta">▸</div>
 <div class="etapa"><b>09 VFDB</b><span>blastn × VFDB S. pyogenes · identidade ≥ 90% · cobertura ≥ 70%</span></div><div class="seta">▸</div>
 <div class="etapa"><b>10 CONSOLIDAÇÃO</b><span>consolidar_lote.py → epibuilder_metadata.tsv</span></div><div class="seta">▸</div>
 <div class="etapa"><b>11 METADADOS</b><span>juntar_metadados.py → epibuilder_completo.tsv (+ QC e dados clínicos)</span></div><div class="seta">▸</div>
 <div class="etapa"><b>12 LAUDOS</b><span>vigilancia_bot.py + Ollama llama3:8b → laudos.txt</span></div><div class="seta">▸</div>
 <div class="etapa"><b>13 RELATÓRIO</b><span>relatorio_lote.py → relatorio_lote.md</span></div><div class="seta">▸</div>
 <div class="etapa"><b>14 DASHBOARD</b><span>relatorio_html.py → dashboard.html (mapa 3D + gráficos + laudos)</span></div>
</div>
<p class="nota"><b>Importante:</b> as etapas 01–06 (<b>Dorado</b>, Flye, Medaka, QUAST/NanoPlot,
Prokka) são <b>a montante</b> e <b>não são executadas por este repositório</b>.
Neste servidor, o Dorado <b>não está instalado</b> (verificado em 19/11/2026: ausente no PATH
e sem imagem Docker); os comandos abaixo são a documentação do fluxo descrito no TCC,
para serem executados no laboratório de sequenciamento/bioinformática. Existem dados FAST5
antigos em <code>/resultados/Analises_Paulo/fast5_pass</code> (barcode01–05, jun/2025),
mas eles <b>não</b> foram usados nesta validação — os 30 assemblies vieram do NCBI RefSeq.
Este repositório começa no assembly FASTA depositado em <code>entrada/</code>.</p>
</div>

<div class="panel"><h2><span class="id">01</span> Pré-requisitos do ambiente</h2>
<table class="docs-tabela"><thead><tr><th>Item</th><th>Local / versão</th><th>Verificação</th></tr></thead><tbody>
<tr><td>micromamba</td><td><code>/resultados/Analises_Paulo/micromamba</code></td><td><code>micromamba env list</code></td></tr>
<tr><td>Ambiente <code>emmtyper</code></td><td>emmtyper 0.2.0 · blastn · isPcr</td><td><code>source config.sh &amp;&amp; emmtyper --version</code></td></tr>
<tr><td>Docker / Ollama</td><td>container <code>ollama</code> · modelo <code>llama3:8b</code></td><td><code>docker exec ollama ollama list</code></td></tr>
<tr><td>Bancos locais</td><td><code>emm.fna</code>, <code>VFDB_S.pyogenes.fas</code> + índice BLAST</td><td><code>ls banco_dados/</code></td></tr>
<tr><td>Vetor do mapa</td><td><code>banco_dados/brasil_geo.json</code> (27 estados, 5.523 municípios)</td><td><code>ls -lh banco_dados/brasil_geo.json</code></td></tr>
</tbody></table>
{cmd('02', '''
cd ~/teste_emmtyper
source config.sh
# Em outro clone: cp config.example.sh config.sh e ajuste os caminhos
micromamba env list
emmtyper --version
docker exec ollama ollama list
''')}
</div>

<div class="panel"><h2><span class="id">03</span> Comando principal · lote completo</h2>
{cmd('', '''
cd ~/teste_emmtyper
./pipeline_principal.sh --metadados docs/metadados_exemplo.tsv
''')}
<p class="nota">Executa, em ordem: QC → emmtyper (BLAST) → blastn VFDB → consolidação → junção de metadados → laudos Ollama → relatório → dashboard. Substitua o TSV de metadados pelo arquivo anonimizado real quando as amostras chegarem.</p>
{cmd('04', '''
# Teste rápido (sem Ollama): 30/30 amostras, 0 falhas, 18 tipos emm
./pipeline_principal.sh --sem-laudos --metadados docs/metadados_exemplo.tsv

# Uma amostra específica
./pipeline_principal.sh --amostra entrada/GCF_000006785.2_ASM678v2_genomic.fna

# Incluir PCR in silico (conferência complementar)
./pipeline_principal.sh --pcr

# Pular QC ou relatório
./pipeline_principal.sh --sem-qc
./pipeline_principal.sh --sem-relatorio
./pipeline_principal.sh --sem-html
''')}
</div>

<div class="panel"><h2><span class="id">05</span> Ollama e laudos</h2>
{cmd('', '''
docker start ollama                       # se o contêiner estiver parado
docker exec ollama ollama pull llama3:8b  # se o modelo não estiver baixado
source config.sh
"$CONDA_PREFIX/bin/python" scripts/testar_ollama.py
"$CONDA_PREFIX/bin/python" scripts/vigilancia_bot.py
''')}
<p class="nota">A classificação do alerta é determinística (calculada em Python); o modelo apenas redige a narrativa. Laudos são apoio à interpretação, nunca diagnóstico.</p>
</div>

<div class="panel"><h2><span class="id">06</span> Visualização e páginas do site</h2>
{cmd('', '''
# Regera apenas os dois HTMLs a partir dos resultados já calculados
source config.sh
"$CONDA_PREFIX/bin/python" scripts/relatorio_html.py

# Saídas:
#   resultados_consolidados/dashboard.html  → página 01 (resultados e mapa 3D)
#   resultados_consolidados/pipeline.html   → página 02 (esta página)
''')}
{cmd('07', '''
# Atualizar o vetor geográfico (execução única, se necessário)
python3 scripts/preparar_mapa_brasil.py /caminho/da/pasta_com_geojson

# Publicar no servidor local (rede interna)
cd resultados_consolidados && python3 -m http.server 8080 --bind 0.0.0.0
''')}
</div>

<div class="panel"><h2><span class="id">08</span> Análise separada de epítopos (EpiBuilder)</h2>
<p class="nota">Fora do escopo da vigilância: predição de epítopos lineares de células B nos genes de virulência — perspectiva futura da pesquisa.</p>
{cmd('', '''
source config.sh
"$CONDA_PREFIX/bin/python" scripts/preparar_epitopos.py
# gera analises/epibuilder/VFDB_S_pyogenes_proteins.fasta (333 proteínas)

docker run --rm --entrypoint sh -v epibuilder-data:/tmp/epibuilder \\
  -v "$PWD/analises/epibuilder":/entrada:ro bioinfoufsc/epibuilder-core:latest \\
  -c 'cp /entrada/VFDB_S_pyogenes_proteins.fasta /tmp/epibuilder/'

docker run --rm --sysctl net.ipv6.conf.all.disable_ipv6=1 \\
  --dns 150.162.1.1 --dns 150.162.2.2 \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  -v epibuilder-data:/tmp/epibuilder -e EPIBUILDER_VOLUME=epibuilder-data \\
  bioinfoufsc/epibuilder-core:latest epibuilder \\
  --input_file /tmp/epibuilder/VFDB_S_pyogenes_proteins.fasta \\
  --output /tmp/epibuilder/resultado_vfdb --loc gram_pos
''')}
</div>

<div class="panel"><h2><span class="id">09</span> Saídas e reprodutibilidade</h2>
<table class="docs-tabela"><thead><tr><th>Arquivo</th><th>Conteúdo</th></tr></thead><tbody>
<tr><td><code>qc_montagem.tsv</code></td><td>métricas de qualidade por assembly</td></tr>
<tr><td><code>&lt;ID&gt;_emm.stdout.log</code> + <code>&lt;ID&gt;.blast.raw.tsv</code></td><td>tipo emm e alinhamento BLAST bruto preservado</td></tr>
<tr><td><code>&lt;ID&gt;_vfdb.tsv</code></td><td>hits tabulares do blastn contra VFDB</td></tr>
<tr><td><code>epibuilder_metadata.tsv</code></td><td>tabela genômica consolidada (ID, emm, virulência)</td></tr>
<tr><td><code>epibuilder_completo.tsv</code></td><td>tabela + QC + metadados clínicos/epidemiológicos</td></tr>
<tr><td><code>laudos.txt</code></td><td>laudos individuais via Ollama</td></tr>
<tr><td><code>relatorio_lote.md</code></td><td>resumo do lote (emm, virulência, alertas, agregações)</td></tr>
<tr><td><code>dashboard.html</code> / <code>pipeline.html</code></td><td>páginas 01 e 02 do site</td></tr>
</tbody></table>
{cmd('10', '''
cd ~/teste_emmtyper
emmtyper --version > resultados/emmtyper_version.txt
micromamba list -n emmtyper > resultados/ambiente_emmtyper.txt
sha256sum banco_dados/VFDB_S.pyogenes.fas > resultados/vfdb.sha256
date -Is > resultados/data_execucao.txt
''')}
<p class="nota">Validação atual: 30 assemblies RefSeq de S. pyogenes (taxon 1314), 18 tipos emm, 30/30 processadas, 0 falhas, 0 não-alvo. Metadados clínicos de exemplo são sintéticos.</p>
</div>

<div class="panel"><h2><span class="id">11</span> Etapas a montante em detalhe — NÃO executadas neste repositório</h2>
<table class="docs-tabela"><thead><tr><th>Ferramenta</th><th>Função</th><th>Entrada → saída</th><th>Status aqui</th></tr></thead><tbody>
<tr><td><b>Dorado</b></td><td>basecalling Nanopore + demultiplexação</td><td>POD5/FAST5 → BAM/FASTQ</td><td>❌ não instalado; documentado conforme metodologia do TCC</td></tr>
<tr><td><b>Flye</b></td><td>montagem de novo (leituras longas)</td><td>FASTQ → assembly.fasta</td><td>⚠️ a montante, fora do repo</td></tr>
<tr><td><b>Medaka</b></td><td>polishing da montagem</td><td>assembly + reads → consensus.fasta</td><td>⚠️ a montante, fora do repo</td></tr>
<tr><td><b>QUAST / NanoPlot</b></td><td>métricas de qualidade</td><td>FASTA/FASTQ → relatórios</td><td>⚠️ a montante (o QC deste repo é próprio)</td></tr>
<tr><td><b>Prokka</b></td><td>anotação gênica</td><td>consensus.fasta → GFF/GBK/FAA/FNA</td><td>⚠️ a montante, fora do repo</td></tr>
</tbody></table>
{cmd('', '''
# 1) instalar e baixar o modelo Dorado (R10.4.1, precisão "sup")
micromamba install -c bioconda -c conda-forge dorado samtools
dorado download --model dna_r10.4.1_e8.2_400bps_sup@v5.0.0

# 2) converter FAST5 antigo em POD5 (se necessário)
pod5 convert fast5 /resultados/Analises_Paulo/fast5_pass/ --output /caminho/pod5/

# 3) basecalling (GPU) e demultiplexação (kit Rapid Barcoding SQK-RBK114.24)
dorado basecaller --device cuda:0 \\
  dna_r10.4.1_e8.2_400bps_sup@v5.0.0 /caminho/pod5/ > calls.bam
dorado demux --output-dir /caminho/demux \\
  --kit-name SQK-RBK114-24 calls.bam

# 4) FASTQ por barcode → entra em Flye
samtools fastq -T '*' /caminho/demux/barcode01.fastq.gz > barcode01.fastq
''')}
<p class="nota">Os comandos acima são <b>modelo</b>: o nome do modelo, o kit e o diretório devem ser ajustados ao run real. O Dorado <b>não</b> participou dos 30 assemblies desta validação — eles foram baixados prontos do NCBI RefSeq.</p>
{cmd('', '''
# Montagem, polishing e anotação (exemplo para um barcode)
flye --nano-hq barcode01.fastq --out-dir flye_barcode01 \\
  --threads 16 --genome-size 1.9m
medaka_consensus -i barcode01.fastq -d flye_barcode01/assembly.fasta \\
  -o medaka_barcode01 -m r10_min_high_accuracy -t 16
quast.py medaka_barcode01/consensus.fasta -o quast_barcode01
NanoPlot --fastq barcode01.fastq -o nanoplot_barcode01
prokka medaka_barcode01/consensus.fasta --outdir prokka_barcode01 \\
  --prefix AMOSTRA_01

# O FASTA final (consensus.fasta / .fna) é o que entra em entrada/
''')}
</div>

<div class="panel"><h2><span class="id">13</span> Pipeline ATUAL em produção — etapas executadas aqui</h2>
<p class="nota">Esta é a sequência que efetivamente roda hoje, validada em 30 assemblies (30/30 processadas, 0 falhas, 18 tipos emm). Os comandos abaixo são os mesmos do <code>pipeline_principal.sh</code>.</p>
<table class="docs-tabela"><thead><tr><th>Etapa</th><th>Comando / ferramenta</th><th>Parâmetros e regras</th><th>Produto</th></tr></thead><tbody>
<tr><td>QC de montagem</td><td><code>scripts/qc_montagem.py</code></td><td>1,5–2,5 Mb · ≤500 contigs · GC 35–42% · Ns ≤1%</td><td><code>qc_montagem.tsv</code></td></tr>
<tr><td>Tipagem emm</td><td><code>emmtyper --workflow blast</code> v0.2.0</td><td>banco interno <code>emm.fna</code>; <code>--keep</code> preserva o BLAST bruto</td><td><code>&lt;ID&gt;_emm.stdout.log</code> + <code>.blast.raw.tsv</code></td></tr>
<tr><td>Virulência</td><td><code>blastn</code> × VFDB</td><td>outfmt <code>6 qseqid sseqid pident length slen qcovhsp</code>; <code>-max_target_seqs 5000</code>; pident ≥ 90%; cobertura do gene <code>length/slen</code> ≥ 70%</td><td><code>&lt;ID&gt;_vfdb.tsv</code></td></tr>
<tr><td>Consolidação</td><td><code>scripts/consolidar_lote.py</code></td><td>parse real de emm + VFDB (sem dados simulados); exclui não-alvo</td><td><code>epibuilder_metadata.tsv</code></td></tr>
<tr><td>Metadados</td><td><code>scripts/juntar_metadados.py</code></td><td>join por <code>ID_Amostra</code>; amostras sem metadata recebem <code>NA</code></td><td><code>epibuilder_completo.tsv</code></td></tr>
<tr><td>Laudos</td><td><code>scripts/vigilancia_bot.py</code> + Ollama</td><td><code>llama3:8b</code>, temperatura 0; alerta determinístico em Python; vermelho = toxina superantigênica (speA/C/D/G/H/I/J/K/L/M/ssa/smeZ), amarelo = evasão/adesão, padrão = basal</td><td><code>laudos.txt</code></td></tr>
<tr><td>Relatório</td><td><code>scripts/relatorio_lote.py</code></td><td>agregações por emm, VFDB, alerta, mês, município, sítio e desfecho</td><td><code>relatorio_lote.md</code></td></tr>
<tr><td>Páginas HTML</td><td><code>scripts/relatorio_html.py</code></td><td>dashboard com mapa 3D + página de comandos; vetores e CSS/JS embutidos</td><td><code>dashboard.html</code> + <code>pipeline.html</code></td></tr>
</tbody></table>
{cmd('', '''
cd ~/teste_emmtyper && source config.sh
PY="$CONDA_PREFIX/bin/python"

# 1) QC de montagem (todas as amostras de entrada/*.fna)
"$PY" scripts/qc_montagem.py --saida resultados_consolidados/qc_montagem.tsv entrada/*.fna

# 2) Tipagem emm — por amostra, dentro de resultados_blast/.work/<ID>/
emmtyper --workflow blast --blast_db "$EMMTYPER_DB" --keep \\
  --output "resultados_blast/${ID}_emm.stdout.log" "$GENOMA_ABS"

# 3) Virulência VFDB — por amostra
blastn -query "$GENOMA_ABS" -db "$VFDB_DB" \\
  -outfmt "6 qseqid sseqid pident length slen qcovhsp" \\
  -max_target_seqs 5000 \\
  -out "resultados_consolidados/${ID}_vfdb.tsv"

# 4) PCR in silico (opcional — ativado por --pcr)
emmtyper --workflow pcr --blast_db "$EMMTYPER_DB" \\
  --primer-db "$PRIMER_DB" --ispcr-path "$ISPCR_PATH" --keep \\
  --output "resultados_pcr/${ID}_pcr.stdout.log" "$GENOMA_ABS"

# 5) Consolidação (resultados reais, sem simulação)
"$PY" scripts/consolidar_lote.py --entrada-dir entrada \\
  --resultados-blast resultados_blast \\
  --resultados-vfdb resultados_consolidados \\
  --saida resultados_consolidados/epibuilder_metadata.tsv \\
  --min-pident "$VFDB_MIN_PIDENT" --min-qcov "$VFDB_MIN_QCOV"

# 6) Junção com metadados clínicos (quando --metadados é usado)
"$PY" scripts/juntar_metadados.py \\
  --genomico resultados_consolidados/epibuilder_metadata.tsv \\
  --metadados docs/metadados_exemplo.tsv \\
  --qc resultados_consolidados/qc_montagem.tsv \\
  --saida resultados_consolidados/epibuilder_completo.tsv

# 7) Laudos (quando --sem-laudos NÃO é usado)
"$PY" scripts/vigilancia_bot.py 2>&1 | tee resultados_consolidados/laudos.txt

# 8) Relatório do lote
"$PY" scripts/relatorio_lote.py \\
  --tabela resultados_consolidados/epibuilder_completo.tsv \\
  --laudos resultados_consolidados/laudos.txt \\
  --vfdb banco_dados/VFDB_S.pyogenes.fas \\
  --saida resultados_consolidados/relatorio_lote.md

# 9) As duas páginas HTML (geradas juntas)
"$PY" scripts/relatorio_html.py \\
  --tabela resultados_consolidados/epibuilder_completo.tsv \\
  --laudos resultados_consolidados/laudos.txt \\
  --vfdb banco_dados/VFDB_S.pyogenes.fas \\
  --saida resultados_consolidados/dashboard.html \\
  --min-pident "$VFDB_MIN_PIDENT" --min-qcov "$VFDB_MIN_QCOV"
''')}
</div>
<footer>CIGenS/SC · UFSC · LACEN/SC · DIVE/SC · emmtyper 0.2.0 (BLAST) · VFDB S. pyogenes ·
laudos via Ollama llama3:8b são apoio à interpretação, não diagnóstico.</footer>
</main>
<script>{PIPELINE_JS}</script></body></html>
"""


def gerar_html(dados, caminho_tabela, caminho_laudos, minimo_genes, minimo_cov, geo, logo="", pipeline_url="pipeline.html"):
    payload = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    geo_json = json.dumps(geo, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") if geo else "{}"
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    modelo = ""
    if not any(d["laudo"] for d in dados):
        modelo = " (sem laudos)"
    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CIGenS/SC — Dashboard de vigilância</title>
<style>{CSS}</style></head><body>
<div class="scan"></div>
<header><div class="cabecalho-conteudo">
<div class="logo-ufsc" title="Universidade Federal de Santa Catarina">{logo}</div>
<div><div class="overline">CIGenS // Módulo de vigilância genômica · SYS.01</div>
<h1>VIGILÂNCIA DE <i>STREPTOCOCCUS PYOGENES</i></h1>
<p>PAINEL DE LEITURA EPIDEMIOLÓGICA · GERADO EM {agora} · FONTE: {html.escape(Path(caminho_tabela).name).upper()}{modelo.upper()}</p></div>
</div><div class="status"><b></b>SISTEMA ONLINE</div>
<a class="nav-btn" href="{html.escape(pipeline_url)}">📖 PIPELINE</a><div class="hud-line"></div></header>
<main>
<div class="cards">
 <div class="card"><div class="num" id="k-amostras">0</div><div class="lbl">Amostras no lote</div></div>
 <div class="card"><div class="num" id="k-emm">0</div><div class="lbl">Tipos emm distintos</div></div>
 <div class="card red"><div class="num" id="k-vermelho">0</div><div class="lbl">Alertas vermelhos</div></div>
 <div class="card green"><div class="num" id="k-qc">0</div><div class="lbl">QC aprovado</div></div>
</div>
<div class="panel"><h2><span class="id">00</span> Filtros / consulta</h2><div class="controles">
 <input id="f-q" type="search" placeholder="Buscar ID, gene, município…">
 <select id="f-emm"><option value="">Todos os emm</option></select>
 <select id="f-municipio"><option value="">Todos os municípios</option></select>
 <select id="f-alerta"><option value="">Todos os alertas</option>
  <option value="VERMELHO">🔴 Vermelho</option><option value="AMARELO">🟡 Amarelo</option>
  <option value="PADRAO">⚪ Padrão</option></select>
 <button id="limpar">Limpar</button><button id="exportar">Exportar TSV</button>
 <span id="contador" style="margin-left:auto;color:#667"></span>
</div></div>
<div class="grid2">
 <div class="panel"><h2><span class="id">01</span> Distribuição de tipos emm</h2><div id="c-emm"></div></div>
 <div class="panel"><h2><span class="id">02</span> Evolução mensal</h2><div id="c-tempo"></div></div>
 <div class="panel"><h2><span class="id">03</span> Amostras por município</h2><div id="c-municipio"></div></div>
 <div class="panel"><h2><span class="id">04</span> Categorias funcionais VFDB</h2><div id="c-categorias"></div></div>
</div>
<div class="panel mapa-panel" id="painel-mapa"><h2><span class="id">06</span> Mapa tático 3D · amostras por município
 <button class="expandir" onclick="toggleExpandir()">⛶ EXPANDIR</button></h2>
<div class="mapa-controles">
 <button onclick="girar(-15)">↺ 15°</button>
 <input type="range" id="rot" min="0" max="360" value="0" title="Rotação 0–360°">
 <button onclick="girar(15)">↻ 15°</button>
 <button onclick="zoomMapa(1.25)">+ ZOOM</button>
 <button onclick="zoomMapa(0.8)">− ZOOM</button>
 <button onclick="resetMapa()">RESET</button>
 <button id="voltar" onclick="voltarBrasil()" style="display:none;border-color:var(--cyan);color:var(--cyan)">← VOLTAR AO BRASIL</button>
 <span class="mapa-status" id="mapa-status">VISÃO BRASIL · ROT 0° · ZOOM 1.0x · CLIQUE NUM ESTADO</span>
</div>
<div class="mapa-wrap">
 <div class="mapa-palco">
 <div class="mapa-canvas"><svg id="mapa" viewBox="0 0 1300 980" role="img" aria-label="Mapa 3D do Brasil com amostras"></svg></div>
 <aside class="info-box hidden" id="info-box">
  <button class="fechar" onclick="fecharInfo()">✕ FECHAR</button>
  <h3 id="ib-titulo">AMOSTRA</h3><div id="ib-conteudo"></div>
 </aside>
 </div>
 <div class="legenda" id="legenda"></div>
</div></div>
<div class="panel"><h2><span class="id">05</span> Amostras · clique para abrir o laudo</h2>
<table><thead><tr><th>ID</th><th>emm</th><th>Município</th><th>Data</th><th>Sítio</th>
<th>Desfecho</th><th>Genes</th><th>QC</th><th>Alerta</th></tr></thead>
<tbody id="corpo"></tbody></table></div>
<footer>emmtyper 0.2.0 (BLAST) · VFDB S. pyogenes · identidade ≥ {minimo_genes}% · cobertura ≥ {minimo_cov}% ·
classificação de alerta determinística; laudos via Ollama são apoio à interpretação, não diagnóstico.
Dados clínicos anonimizados.</footer>
</main>
<script id="geo" type="application/json">{geo_json}</script>
<script id="dados" type="application/json">{payload}</script>
<script>{JS}</script></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabela", default="resultados_consolidados/epibuilder_completo.tsv")
    parser.add_argument("--laudos", default="resultados_consolidados/laudos.txt")
    parser.add_argument("--vfdb", default="banco_dados/VFDB_S.pyogenes.fas")
    parser.add_argument("--geo", default="banco_dados/brasil_geo.json")
    parser.add_argument("--logo", default="docs/logo_ufsc.svg")
    parser.add_argument("--saida", default="resultados_consolidados/dashboard.html")
    parser.add_argument("--saida-pipeline", default="resultados_consolidados/pipeline.html")
    parser.add_argument("--dashboard-url", default="dashboard.html")
    parser.add_argument("--pipeline-url", default="pipeline.html")
    parser.add_argument("--min-pident", default="90")
    parser.add_argument("--min-qcov", default="70")
    args = parser.parse_args()

    tabela = Path(args.tabela)
    if not tabela.is_file():
        alternativa = tabela.with_name("epibuilder_metadata.tsv")
        if alternativa.is_file():
            tabela = alternativa
        else:
            parser.error(f"tabela não encontrada: {args.tabela}")
    laudos = args.laudos if Path(args.laudos).is_file() else ""
    geo = {}
    if Path(args.geo).is_file():
        geo = json.loads(Path(args.geo).read_text(encoding="utf-8"))
    logo = Path(args.logo).read_text(encoding="utf-8") if Path(args.logo).is_file() else ""
    dados = construir_dados(carregar_tabela(tabela), carregar_laudos(laudos), carregar_vfdb(args.vfdb))
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(gerar_html(dados, tabela, laudos, args.min_pident, args.min_qcov,
                                geo, logo, args.pipeline_url), encoding="utf-8")
    saida_pipeline = Path(args.saida_pipeline)
    saida_pipeline.parent.mkdir(parents=True, exist_ok=True)
    saida_pipeline.write_text(gerar_html_pipeline(logo, args.dashboard_url, args.pipeline_url), encoding="utf-8")
    print(f"Dashboard gerado: {saida}")
    print(f"Página da pipeline gerada: {saida_pipeline}")
    print(f"Amostras: {len(dados)} | com laudo: {sum(1 for d in dados if d['laudo'])}")


if __name__ == "__main__":
    main()
