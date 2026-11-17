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
@media print{.scan{display:none}header{box-shadow:none}.controles{display:none}body{background:#fff}}
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
  render();
});
"""


def gerar_html(dados, caminho_tabela, caminho_laudos, minimo_genes, minimo_cov):
    payload = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
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
<header><div class="overline">CIGenS // Módulo de vigilância genômica · SYS.01</div>
<h1>VIGILÂNCIA DE <i>STREPTOCOCCUS PYOGENES</i></h1>
<p>PAINEL DE LEITURA EPIDEMIOLÓGICA · GERADO EM {agora} · FONTE: {html.escape(Path(caminho_tabela).name).upper()}{modelo.upper()}</p>
<div class="status"><b></b>SISTEMA ONLINE</div><div class="hud-line"></div></header>
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
<div class="panel"><h2><span class="id">05</span> Amostras · clique para abrir o laudo</h2>
<table><thead><tr><th>ID</th><th>emm</th><th>Município</th><th>Data</th><th>Sítio</th>
<th>Desfecho</th><th>Genes</th><th>QC</th><th>Alerta</th></tr></thead>
<tbody id="corpo"></tbody></table></div>
<footer>emmtyper 0.2.0 (BLAST) · VFDB S. pyogenes · identidade ≥ {minimo_genes}% · cobertura ≥ {minimo_cov}% ·
classificação de alerta determinística; laudos via Ollama são apoio à interpretação, não diagnóstico.
Dados clínicos anonimizados.</footer>
</main>
<script id="dados" type="application/json">{payload}</script>
<script>{JS}</script></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabela", default="resultados_consolidados/epibuilder_completo.tsv")
    parser.add_argument("--laudos", default="resultados_consolidados/laudos.txt")
    parser.add_argument("--vfdb", default="banco_dados/VFDB_S.pyogenes.fas")
    parser.add_argument("--saida", default="resultados_consolidados/dashboard.html")
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
    dados = construir_dados(carregar_tabela(tabela), carregar_laudos(laudos), carregar_vfdb(args.vfdb))
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(gerar_html(dados, tabela, laudos, args.min_pident, args.min_qcov), encoding="utf-8")
    print(f"Dashboard gerado: {saida}")
    print(f"Amostras: {len(dados)} | com laudo: {sum(1 for d in dados if d['laudo'])}")


if __name__ == "__main__":
    main()
