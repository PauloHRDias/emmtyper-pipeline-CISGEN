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
:root{--bg:#f4f6f9;--card:#fff;--ink:#16202c;--muted:#66737f;--line:#dfe5ec;
--blue:#1565c0;--red:#c62828;--amber:#ef6c00;--green:#2e7d32;--soft:#eaf1fb}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
header{background:#0d2b45;color:#fff;padding:22px 28px}
header h1{margin:0;font-size:21px}header p{margin:5px 0 0;color:#bcd2e6;font-size:13px}
main{max-width:1220px;margin:20px auto;padding:0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:15px;
box-shadow:0 1px 3px #0000000d}.card .num{font-size:27px;font-weight:700}.card .lbl{color:var(--muted);font-size:12px}
.card.red .num{color:var(--red)}.card.green .num{color:var(--green)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:16px}
.panel h2{margin:0 0 12px;font-size:15px;color:#0d2b45}
.controles{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.controles input,.controles select,button{padding:8px 10px;border:1px solid var(--line);
border-radius:7px;background:#fff;color:var(--ink);font-size:13px}
button{cursor:pointer;background:var(--soft);border-color:#b9d0ec}
button:hover{background:#dbe9fa}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:800px){.grid2{grid-template-columns:1fr}}
svg{width:100%;height:auto;max-height:280px}.bar-label{font-size:11px;fill:var(--ink)}
.bar-val{font-size:11px;fill:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f7f9fc;color:#40525f;cursor:pointer;white-space:nowrap}
tr.amostra:hover{background:#f3f8ff;cursor:pointer}
.tag{padding:2px 7px;border-radius:10px;font-size:11px;font-weight:600;white-space:nowrap}
.tag.VERMELHO{background:#fdecea;color:var(--red)}.tag.AMARELO{background:#fff3e0;color:var(--amber)}
.tag.PADRAO{background:#e8f5e9;color:var(--green)}.tag.SEM_LAUDO{background:#eceff1;color:var(--muted)}
.detail td{background:#f8fafc;white-space:normal}.detail .laudo{line-height:1.65}
.gene{display:inline-block;background:#edf2f7;border-radius:4px;padding:1px 5px;margin:2px;font-size:11px}
footer{color:var(--muted);font-size:12px;margin:22px 0;padding-top:12px;border-top:1px solid var(--line)}
@media print{header{background:#fff;color:#000}body{background:#fff}.panel,.card{box-shadow:none}.controles{display:none}}
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
    svg += `<rect x="${L}" y="${y+3}" width="${w}" height="15" rx="3" fill="${cor}"/>`;
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
  svg+='<polyline fill="none" stroke="#1565c0" stroke-width="2.5" points="'+pts.map(p=>p.join(',')).join(' ')+'"/>';
  pts.forEach((p,i)=>{svg+=`<circle cx="${p[0]}" cy="${p[1]}" r="3" fill="#1565c0"/><text x="${p[0]}" y="${H-8}" text-anchor="middle" class="bar-val">${esc(pares[i][0].slice(2))}</text>`;});
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
  barras('c-emm',contar(rows,r=>r.emm),'#1565c0');
  linha('c-tempo',contar(rows,r=>r.mes));
  barras('c-municipio',contar(rows,r=>r.municipio).filter(p=>p[0]!=='NA'),'#00838f');
  const cat={};
  rows.forEach(r=>Object.entries(r.categorias).forEach(([k,v])=>cat[k]=(cat[k]||0)+v));
  barras('c-categorias',Object.entries(cat).sort((a,b)=>b[1]-a[1]),'#6a1b9a');
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
<header><h1>CIGenS/SC · Vigilância de <i>Streptococcus pyogenes</i></h1>
<p>Painel de leitura epidemiológica · gerado em {agora} · fonte: {html.escape(Path(caminho_tabela).name)}{modelo}</p></header>
<main>
<div class="cards">
 <div class="card"><div class="num" id="k-amostras">0</div><div class="lbl">Amostras no lote</div></div>
 <div class="card"><div class="num" id="k-emm">0</div><div class="lbl">Tipos emm distintos</div></div>
 <div class="card red"><div class="num" id="k-vermelho">0</div><div class="lbl">Alertas vermelhos</div></div>
 <div class="card green"><div class="num" id="k-qc">0</div><div class="lbl">QC aprovado</div></div>
</div>
<div class="panel"><h2>Filtros</h2><div class="controles">
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
 <div class="panel"><h2>Distribuição de tipos emm</h2><div id="c-emm"></div></div>
 <div class="panel"><h2>Evolução mensal</h2><div id="c-tempo"></div></div>
 <div class="panel"><h2>Amostras por município</h2><div id="c-municipio"></div></div>
 <div class="panel"><h2>Categorias funcionais VFDB</h2><div id="c-categorias"></div></div>
</div>
<div class="panel"><h2>Amostras (clique para ver o laudo)</h2>
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
