UNIVERSIDADE FEDERAL DE SANTA CATARINA
CENTRO DE CIÊNCIAS BIOLÓGICAS
DEPARTAMENTO DE CIÊNCIAS BIOLÓGICAS

Tipificação por sequenciamento total de genoma de
Streptococcus pyogenes isolados de infecções invasivas

Paulo Henrique da Rocha Dias
Florianópolis – SC
2026
Paulo Henrique da Rocha Dias

Tipificação por sequenciamento total de genoma de Streptococcus pyogenes isolados de infecções invasivas

Trabalho de Conclusão de Curso apresentado ao Curso de Graduação em Ciências Biológicas da Universidade Federal de Santa Catarina como requisito parcial para a obtenção do título de Bacharel em Ciências Biológicas

Orientador(a): Prof. Dr. Glauber Wagner

Florianópolis – SC
2026
SUMÁRIO

1 INTRODUÇÃO ....................................................................................... 6

2 REVISÃO BIBLIOGRÁFICA ................................................................... 8
2.1 Inteligência artificial aplicada à vigilância genômica .................... 11

3 OBJETIVOS .......................................................................................... 13
3.1 Objetivo geral ................................................................................. 13
3.2 Objetivos específicos ..................................................................... 13

4 MATERIAL E MÉTODOS .................................................................... 14
4.1 Etapas da pipeline .......................................................................... 17

5 CRONOGRAMA .................................................................................. 18

6 RESULTADOS ESPERADOS .............................................................. 19

7 RISCOS E DIFICULDADES ............................................................... 20

8 VIABILIDADE ECONÔMICA DO PROJETO ...................................... 21

9 REFERÊNCIAS .................................................................................. 22

10 APÊNDICE e/ou ANEXO ................................................................. 24

1 INTRODUÇÃO
        As infecções causadas por bactérias patogênicas permanecem entre os principais desafios para a saúde pública, especialmente quando envolvem agentes capazes de provocar quadros invasivos, rápida disseminação e elevado impacto clínico. Nesse contexto, Streptococcus pyogenes do grupo A (EGA) destaca-se por sua relevância epidemiológica (PAHO, 2024), uma vez que pode estar associado a infecções de diferentes gravidades, desde manifestações leves até doenças invasivas graves e potencialmente fatais. Além disso, sua variabilidade genética e a presença de determinantes de virulência tornam esse microrganismo um importante objeto de estudo para a vigilância epidemiológica e genômica (ARCARI et al., 2025; SMEESTERS et al., 2024).
O avanço das tecnologias de sequenciamento e das ferramentas de bioinformática tem possibilitado uma compreensão mais detalhada da diversidade genética de patógenos bacterianos, permitindo a identificação de linhagens circulantes, a caracterização de genes associados à virulência e a investigação de marcadores úteis para o monitoramento de surtos e casos invasivos. A vigilância genômica, nesse sentido, constitui uma estratégia fundamental para integrar dados laboratoriais, clínicos e epidemiológicos (WHO, 2022; BAKER et al., 2023), contribuindo para respostas mais ágeis e qualificadas no âmbito da saúde pública. No caso de S. pyogenes, essa abordagem é especialmente relevante diante da circulação de diferentes genótipos e da necessidade de melhor compreender os fatores relacionados à sua patogenicidade.
É nesse cenário que se insere o projeto “Centro de Inteligência de Dados e Vigilância Genômica em Saúde (CIGenS) de Santa Catarina (Fase I): Vigilância de infecções invasivas por S. pyogenes como modelo para fortalecimento da resposta em saúde pública no Estado de Santa Catarina”, desenvolvido em parceria entre a UFSC, o LACEN/SC e a DIVE/SC. A proposta do projeto é estruturar uma base integrada de vigilância genômica voltada inicialmente para S. pyogenes, com potencial de expansão para outros patógenos, buscando fortalecer a capacidade de resposta do sistema de saúde diante de infecções invasivas e produzir informações aplicáveis à gestão em saúde.
Dentro desse contexto, o presente trabalho de conclusão de curso corresponde a uma etapa específica do projeto maior, tendo como foco a montagem e anotação dos genomas de isolados clínicos de S. pyogenes, a genotipagem das amostras e a identificação dos fatores de virulência presentes nos isolados analisados. A partir de dados obtidos por sequenciamento genômico, serão realizadas análises bioinformáticas voltadas à caracterização molecular dos isolados, incluindo a tipagem emm e a investigação de genes associados à patogenicidade. Dessa forma, pretende-se contribuir para o conhecimento sobre a diversidade genética de S. pyogenes em Santa Catarina e para o fortalecimento das ações de vigilância genômica em saúde pública.

2 REVISÃO BIBLIOGRÁFICA
“O sequenciamento genômico de patógenos durante a pandemia de COVID‑19 ressaltou a importância essencial da vigilância na compreensão da presença duradoura do SARS‑CoV‑2 na população humana, apesar dos níveis elevados de imunidade protetora e das implicações da evolução das variantes circulantes na saúde pública” (LYTRAS et al., 2025, p. 1). Essa afirmativa ilustra como a vigilância genômica se tornou um pilar central para o monitoramento e a tomada de decisão em saúde pública, especialmente em contextos de emergência sanitária. Com quase 20 milhões de genomas de SARS‑CoV‑2 disponíveis no banco de dados GISAID, as iniciativas de sequenciamento iniciadas desde 2020 superaram em volume as de outros patógenos virais, como o vírus influenza e o HIV‑1, reforçando a relevância dos estudos sobre a evolução e a circulação de variantes circulantes.
Partindo desse avanço metodológico, o conceito de inteligência patogênica (pathogen intelligence), proposto por Engelthaler (2024), descreve a transformação de dados genômicos em conhecimento acionável para a saúde pública, organizando essa inteligência em quatro dimensões: epidemiológica, clínica, de epidemia e biológica (ENGELTHALER, 2024). A inteligência epidemiológica permite a epidemiologia genômica, com detecção precoce e precisa de surtos e definição de casos realmente ligados geneticamente, enquanto a inteligência clínica fornece informações sobre resistência antimicrobiana e virulência diretamente a partir de sequenciamento de amostras clínicas, como demonstrado na vigilância genômica do SARS‑CoV‑2 no Brasil durante a pandemia da COVID‑19, em que o sequenciamento permitiu a identificação precoce de variantes de preocupação, como a Gamma/P.1, a Delta e a Ômicron, e a extração de informações sobre escape imunológico, resistência a terapias e alterações de virulência diretamente dos genomas virais (FARIA et al., 2021; MCCRONE et al., 2022; ARANTES et al., 2024), reforçando que a genômica clínica é um pilar da vigilância não apenas para vírus, mas também para bactérias como Streptococcus pyogenes. A inteligência de epidemia destaca o uso de genômica em pandemias, como o H1N1pdm09 e SARS‑CoV‑2, como um sistema de inteligência em tempo quase real para orientar políticas de saúde, ainda que aponte limitações na integração entre sistemas de vigilância.
Já a inteligência biológica (biological intel), foco central deste projeto, enfatiza o estudo do patógeno como um agente biológico em seu ecossistema natural, mostrando como sua biologia e ecologia — e não apenas sua capacidade de causar doença humana — revelam mecanismos evolutivos, e possibilidades de intervenção futura. Diante disso, o presente trabalho propõe aplicar essa mesma abordagem ao estudo de Streptococcus pyogenes, buscando contribuir para a compreensão da dinâmica genômica, da diversidade e da disseminação de linhagens desse micro‑organismo em um contexto regional. 
A pertinência de aplicar a inteligência patogênica ao estudo de Streptococcus pyogenes decorre de sua relevância como um dos principais agentes de doenças infecciosas em humanos, cuja diversidade clínica se estende de infecções de garganta de curso leve até quadros graves, como erisipela, fasciíte necrosante, síndrome do choque tóxico e complicações pós‑infecciosas como a febre reumática e a glomerulonefrite (ARCARI et al., 2025; BONOMO et al., 2025; SMEESTERS et al., 2024).  O S. pyogenes é um estreptococo beta‑hemolítico do grupo A de Lancefield, Gram‑positivo, capaz de colonizar a orofaringe e a pele, sendo transmitido por contato direto com secreções ou lesões cutâneas, o que favorece surtos em ambientes coletivos, como escolas e creches (ARCARI et al., 2025; RÜMKE et al., 2024).
Sua patogenicidade é sustentada por um amplo repertório de fatores de virulência, incluindo a proteína M, cápsula de ácido hialurônico, enzimas hidrolíticas (estreptoquinase, hialuronidase, DNAse) e exotoxinas superantigênicas, que permitem adesão, sobrevivência no hospedeiro, escape fagocítico e intensa resposta inflamatória, por vezes desproporcional às infecções iniciais (ARCARI et al., 2025; BONOMO et al., 2025; SAMBRANO, 2014).  Estudos recentes também destacam a circulação global de linhagens invasivas e o risco de surtos de infecções graves, reforçando a necessidade de estratégias de vigilância que integrem epidemiologia clássica a análises genômicas em tempo quase real, tal como ocorreu com vírus como SARS‑CoV‑2 (DAVIES et al., 2025; VIEIRA et al., 2024; BERNARDI et al., 2026; MARTINI et al., 2023).
Nesse sentido, a inteligência biológica de Streptococcus pyogenes — entendida não apenas como causa de doenças, mas como um micro‑organismo em seu ecossistema de colonização e transmissão — demanda a integração de dados genômicos, clínicos e epidemiológicos, a fim de compreender a diversidade de linhagens, seu padrão de disseminação e a evolução de fatores de virulência e resistência, especialmente em contextos regionais onde o perfil de infecção e a pressão de seleção podem diferir dos cenários descritos em países de alta renda (ARCARI et al., 2025; ANDRIANAKI et al., 2024; BERNARDI et al., 2024).
A eficácia da vigilância genômica sobre Streptococcus pyogenes depende, em grande parte, da capacidade de tipificar e classificar diferentes linhagens, permitindo que variáveis genéticas sejam traduzidas em decisões clínicas e epidemiológicas concretas (FROST et al., 2020; ARCARI et al., 2025).  A literatura ressalta que a tipificação molecular (ex.: subtipos emm, MLST, perfis de genes de virulência e resistência) é essencial para diferenciar isolados relacionados de forma clonal de aqueles que representam circulação de linhagens geneticamente distintas, o que impacta diretamente a interpretação de surtos, a identificação de surtos comunitários, hospitalares e transnacionais, bem como a avaliação de risco de doenças invasivas ou recorrentes.
Em estudos recentes, a aplicação de tipagem genômica populacional de S. pyogenes em nível nacional revelou a circulação de múltiplos tipos emm e sequências de tipos (STs), com predominância de linhagens como emm1.0 e ST28, ao mesmo tempo em que identificou perfis inéditos, sugerindo diversidade genética regional e dinâmica evolutiva ativa, que só são visíveis a partir de uma abordagem de vigilância genômica sistemática (BERNARDI et al., 2024; RÜMKE et al., 2024; RUSSO et al., 2025).  Esses trabalhos reforçam que, sem a padronização de sistemas de tipificação, os dados genômicos permanecem soltos em relação ao contexto clínico‑epidemiológico, dificultando a comparação entre laboratórios, regiões e países, e reduzindo a utilidade das informações para formulação de políticas de saúde e estratégias de prevenção.
A integração da tipificação genômica à inteligência biológica de Streptococcus pyogenes permite não apenas rastrear a disseminação de linhagens, mas também relacionar certas variações gênicas (ex.: perfil de proteína M, genes de toxinas superantigênicas, fatores de adesão/infiltração) a manifestações clínicas específicas, como faringite, impetigo, erisipela, fasciíte necrosante ou febre reumática pós‑infecciosa, o que aproxima a vigilância genômica da prática clínica cotidiana (BONOMO et al., 2025; SMEESTERS et al., 2024).  Assim, a tipificação passa a ser um ponte crítica entre a biologia molecular do microrganismo, seus padrões de transmissão e a saúde pública, permitindo que, em um mesmo contexto regional, decisões de bloqueio de surtos, ajuste de rotinas de uso de antimicrobianos e até estratégias de prevenção baseadas em risco sejam fundadas em dados genômicos estruturados e reinterpretáveis ao longo do tempo.
Diante disso, o presente trabalho insere‑se nesse quadro ao propor que a vigilância genômica de Streptococcus pyogenes se apoie não apenas na obtenção de genomas completos, mas na tipificação padronizada (por exemplo, combinação de emm, MLST, perfis de virulência e genes de resistência), de modo a maximizar a inteligência epidemiológica, clínica e biológica gerada pelo patógeno em um contexto regional, contribuindo para a compreensão da dinâmica genômica, da diversidade e da disseminação de linhagens, conforme alinhado às bases conceituais apresentadas anteriormente.

2.1 Inteligência artificial aplicada à vigilância genômica
O volume de dados gerados pelo sequenciamento de genomas completos tornou inviável a interpretação exclusivamente manual, o que tem impulsionado o uso de modelos de linguagem e de aprendizado de máquina como apoio à análise. Os modelos de linguagem genômicos (genomic language models) são treinados em sequências de DNA e podem apoiar tarefas como anotação, classificação de variantes e predição de elementos funcionais, embora ainda demandem validação experimental e cuidado com vieses dos dados de treinamento (BENEGAS et al., 2025; BRANDES, 2026). Revisões recentes mostram que os grandes modelos de linguagem (LLMs) já são aplicados em bioinformática para recuperação de informação, escrita de código, interpretação de resultados e apoio à redação científica, com avanços importantes, mas também com limitações de acurácia e reprodutibilidade (LIN et al., 2025).
Na microbiologia clínica e nas doenças infecciosas, os LLMs têm sido avaliados em tarefas como interpretação de laudos, apoio à decisão antimicrobiana e análise de sequências biológicas (LUO et al., 2025; KHALAF et al., 2025; DIEN BARD et al., 2025). Estudos comparativos, no entanto, evidenciam que o desempenho varia entre modelos e contextos, o que reforça a necessidade de supervisão humana e de mecanismos de validação (DE VITO et al., 2025). Nesse sentido, benchmarks como o GeneTuring demonstram que o conhecimento genômico dos LLMs ainda é limitado e heterogêneo, especialmente em questões que exigem raciocínio sobre dados experimentais (SHANG et al., 2025).
Para reduzir o risco de respostas sem suporte, a arquitetura de recuperação aumentada por geração (retrieval-augmented generation, RAG) tem sido proposta para ancorar a resposta do modelo em documentos e bases de dados verificáveis (LIU et al., 2025). No contexto da vigilância, a IA pode contribuir para detecção precoce de surtos, integração de dados heterogêneos e priorização de amostras (MENDES et al., 2025; VILLANUEVA-MIRANDA et al., 2025; LATIF et al., 2026), mas sua adoção exige governança, transparência e equidade no acesso às tecnologias (PANTELI et al., 2025; VITIELLO; ZOVI, 2026). No âmbito do CIGenS, essa discussão orienta a definição de limites para o uso de LLMs no apoio à redação de laudos, mantendo a classificação de risco e a interpretação dos genes de virulência sob controle determinístico de regras implementadas em Python.

3 OBJETIVOS

3.1 Objetivo geral
Identificar fatores de Virulência realizando análises de isolados clínicos de S. pyogenes (EGA).

3.2 Objetivos específicos
* Montagem e Análise dos Isolados de Streptococcus pyogenes
* Anotação dos Genomas
* Genotipagem dos isolados relativo às bases genômicas obtidas 
* Identificar os fatores de virulência presentes nos isolados de S. pyogenes

4 MATERIAL E MÉTODOS
Este é um estudo experimental, desenvolvido a partir de dados genômicos de isolados clínicos de Streptococcus pyogenes do grupo A (EGA) provenientes do projeto “Centro de Inteligência de Dados e Vigilância Genômica em Saúde (CIGenS) de Santa Catarina (Fase I): Vigilância de infecções invasivas por Streptococcus pyogenes como modelo para fortalecimento da resposta em saúde pública no Estado de Santa Catarina”, financiado pela FAPESC (GESTÃO COMPARTILHADA EM SAÚDE (PPSUS)), com a coordenação do Laboratório de Bioinformática UFSC, LACEN/SC, DIVE/SC. O presente trabalho constitui uma etapa específica deste projeto maior, tendo como foco a caracterização dos genes de virulência e genotipagem nos isolados analisados. Este projeto foi aprovado pelo  CEP/UFSC (CAAE: 88365125.0.0000.0121/ Parecer 8.136.905). 
Obtenção e sequenciamento dos isolados
Os isolados de EGA incluídos no estudo serão obtidos a partir de casos suspeitos de infecções invasivas identificados pelos Núcleos Hospitalares de Epidemiologia (NHE) do Estado de Santa Catarina, conforme os critérios estabelecidos pela Nota Técnica Conjunta nº 08/2024. Após coleta, isolamento e caracterização pelos laboratórios locais, até 200 amostras clínicas de sítios estéreis do corpo, serão encaminhadas ao Laboratório Central de Saúde Pública de Santa Catarina (LACEN/SC) para confirmação diagnóstica e, posteriormente, enviadas de forma anonimizada ao Centro de Inovação em Genômica e Saúde (CIGenS) para extração de DNA e tipagem molecular por meio de sequenciamento genético.
A extração do DNA genômico será realizada utilizando kits comerciais baseados em colunas de sílica e/ou beads magnéticos. A quantificação do DNA será realizada utilizando o kit Qubit dsDNA High Sensitivity (Thermo Fisher Scientific). O preparo das bibliotecas será realizado utilizando o kit Rapid Barcoding (SQK-RBK114.24), seguido de sequenciamento na plataforma Oxford Nanopore Technologies MinION, empregando Flow Cells R10.4.1, conforme protocolo do fabricante. Os resultados gerados serão enviados para o laboratório de bioinformática da UFSC, para realização das análises em softwares de bioinformática. Serão enviados também os dados clínicos e epidemiológicos para correlação com os isolados.
Montagem e caracterização dos genomas 
Os dados brutos gerados pelo sequenciamento serão processados conforme metodologia descrita por Cipriani et al. (2025). Inicialmente, as leituras obtidas pela plataforma Oxford Nanopore serão submetidas ao processo de basecalling e controle de qualidade utilizando o software Dorado, responsável pela conversão dos sinais elétricos gerados durante o sequenciamento em sequências de nucleotídeos. Após o pré-processamento, será realizada a montagem de novo dos genomas utilizando o software Flye, seguida de etapas de refinamento (polishing) com a ferramenta Medaka. A qualidade das montagens será avaliada por meio dos softwares QUAST e NanoPlot, que permitirão verificar métricas relacionadas à completude e qualidade dos genomas obtidos. 
Na sequência os genomas montados serão submetidos a anotação pelo pipeline Prokka (SEEMANN, 2014), gerando o conjunto de genes, CDS e proteínas preditas, bem como a caracterização de elementos não codificantes presentes no genoma. Além disso, os genomas montados serão utilizados para a identificação de fatores de virulência com o programa VFDB (Virulence Factor Database), que reúne genes curados associados a mecanismos de patogenicidade bacteriana (ZHOU et al., 2025; DONG et al., 2024).
Utilizando uma ferramenta de tipagem (typing tool), será realizada a tipagem in silico do gene emm dos isolados de Streptococcus pyogenes, a partir dos genomas montados e anotados. A análise será executada com base na documentação da ferramenta emmtyper, desenvolvida para identificação automática do tipo emm em assemblies genômicos de S. pyogenes (EMMTYPER, 2021; FROST et al., 2020), por meio da comparação das sequências obtidas com bases de referência específicas para a região emm. Essa abordagem permitirá a determinação do tipo emm presente em cada isolado, incluindo a identificação de subtipos, quando aplicável, contribuindo para a padronização da tipagem molecular e para a caracterização genotípica das amostras analisadas.
A tipagem emm constitui um dos principais marcadores moleculares utilizados na caracterização de S. pyogenes, em razão da elevada variabilidade do gene que codifica a proteína M, associada à diversidade genética, à circulação de linhagens e à relação com diferentes manifestações clínicas. Assim, a aplicação da ferramenta permitirá comparar os resultados obtidos com dados de vigilância molecular descritos na literatura, possibilitando a interpretação epidemiológica dos isolados e o reconhecimento de perfis genéticos de interesse.
Adicionalmente, os genomas serão submetidos à pesquisa de fatores de virulência com auxílio da Virulence Factor Database (VFDB), na seção correspondente ao gênero Streptococcus (ZHOU et al., 2025; DONG et al., 2024). Essa base de dados reúne genes previamente descritos e curados associados a mecanismos de patogenicidade bacteriana, como adesão, invasão tecidual, evasão imune e produção de toxinas. A utilização dessa base permitirá a identificação e a classificação dos fatores de virulência presentes nos isolados analisados, fornecendo subsídios para a caracterização funcional dos genomas e para a avaliação do potencial patogênico das amostras estudadas.

4.1 Etapas da pipeline

**Quadro 1 – Pipeline alinhada à metodologia**

| ETAPA | PERGUNTA RESPONDIDA | FERRAMENTA | BASE REFERENCIAL | PRODUTO |
|---|---|---|---|---|
| Tipagem emm | Qual é o tipo/subtipo emm do isolado? | emmtyper 0.2.0 | Banco interno emm.fna | Tipo emm, resultado de BLAST e/ou PCR in silico |
| Pesquisa de virulência | Quais genes de virulência conhecidos estão presentes? | blastn diretamente ou ferramenta dedicada | VFDB, filtrado para *S. pyogenes* | Hits por gene, identidade, cobertura e classificação funcional |
| Consolidação | Qual é o perfil genotípico de cada isolado? | Script em bash/Python | Resultados das duas etapas | Tabela final por amostra |

Fonte: elaborado pelo autor (2026).

5 CRONOGRAMA

**Quadro 2 – Cronograma de execução**

| ATIVIDADE | Jul | Ago | Set | Out | Nov | Dez |
|---|---|---|---|---|---|---|
| Revisão bibliográfica | X | X | X | X | X | |
| Montagem dos genomas | | | X | X | X | X |
| Genotipagem | | | | | X | X |
| Predição de fatores de virulência | | | | | X | X |
| Redação do TCC | | | | X | X | X |
| Apresentação do TCC | | | | | | X |

Fonte: elaborado pelo autor (2026).

6 RESULTADOS ESPERADOS

Deve apresentar de forma concreta o que se espera alcançar. Verificar quais os impactos prováveis do projeto: científico, ambiental, econômico e/ou social. 

7 RISCOS E DIFICULDADES

Deve conter os principais riscos e dificuldades referentes ao trabalho ou pesquisa. Por exemplo: Dificuldades no processo de fermentação da bebida devido ao baixo pH do soro de leite. Deve também conter as medidas previstas para contornar ou superar os riscos e as dificuldades.

8 VIABILIDADE ECONÔMICA DO PROJETO

Deve conter o(s) local(is) da realização das análises.
Deve conter se há estrutura física e/ou equipamento necessários para o desenvolvimento do projeto. De onde serão os recursos para a realização de ensaios, se for o caso.

9 REFERÊNCIAS

ARCARI, Gabriele et al. Global spread of Streptococcus pyogenes: a genomics-supported narrative review. FEMS Microbiology Reviews, v. 49, fuaf058, 2025. DOI: 10.1093/femsre/fuaf058.

ARANTES, Ighor et al. Spatiotemporal dynamics and epidemiological impact of SARS-CoV-2 XBB lineage dissemination in Brazil in 2023. Microbiology Spectrum, v. 12, n. 3, e03831-23, 2024. DOI: 10.1128/spectrum.03831-23.

BAKER, Kate S. et al. Genomics for public health and international surveillance of antimicrobial resistance. The Lancet Microbe, v. 4, n. 12, p. e1047–e1055, 2023. DOI: 10.1016/S2666-5247(23)00283-5.

BENEGAS, Gonzalo et al. Genomic language models: opportunities and challenges. Trends in Genetics, v. 41, n. 4, p. 286–302, 2025. DOI: 10.1016/j.tig.2024.11.013.

BERNARDI, Gisele Aparecida et al. Epidemiologia molecular de Streptococcus pyogenes isolados de doenças invasivas nos anos de 2023 e 2024 das Regiões Sul e Sudeste do Brasil. Revista do Instituto Adolfo Lutz, v. 83, e40726, 2024. Disponível em: https://periodicos.saude.sp.gov.br/RIAL/article/view/41290. Acesso em: 10 nov. 2026.

BERNARDI, Gisele Aparecida et al. Genomic analysis of Streptococcus pyogenes emm1-type isolates reveals M1UK circulation and a genetically distinct Brazilian sublineage. European Journal of Clinical Microbiology & Infectious Diseases, 2026. Publicado online em 28 jul. 2026. DOI: 10.1007/s10096-026-05608-z.

BONOMO, Carmelo et al. Molecular and clinical characterization of invasive Streptococcus pyogenes isolates: insights from two Northern-Italy centers. Pathogens, v. 14, n. 2, 152, 2025. DOI: 10.3390/pathogens14020152.

BRANDES, Nadav. Artificial intelligence in human genetics. Annual Review of Genomics and Human Genetics, v. 27, n. 1, p. 183–204, 2026. DOI: 10.1146/annurev-genom-111124-032550.

CIPRIANI, Gabriel et al. Evaluation of whole-genome sequencing protocols for detection of antimicrobial resistance, virulence factors and mobile genetic elements in antimicrobial-resistant bacteria. Journal of Medical Microbiology, v. 74, n. 3, 001990, 2025. DOI: 10.1099/jmm.0.001990.

DAVIES, Matthew A. et al. Streptococcus pyogenes emm type 3.93 emergence, the Netherlands and England. Emerging Infectious Diseases, v. 31, n. 2, 2025. DOI: 10.3201/eid3102.240880.

DE VITO, Andrea et al. Comparing large language models for antibiotic prescribing in different clinical scenarios: which performs better? Clinical Microbiology and Infection, v. 31, n. 8, p. 1336–1342, 2025. DOI: 10.1016/j.cmi.2025.03.002.

DIEN BARD, Jennifer et al. Proceedings of the Clinical Microbiology Open 2024: artificial intelligence applications in clinical microbiology. Journal of Clinical Microbiology, v. 63, n. 4, e01804-24, 2025. DOI: 10.1128/jcm.01804-24.

DONG, Wanting et al. An expanded database and analytical toolkit for identifying bacterial virulence factors and their associations with chronic diseases. Nature Communications, v. 15, 8084, 2024. DOI: 10.1038/s41467-024-51864-y.

EMMTYPER. emmtyper: emm Automatic Isolate Labeller. [S.l.]: MDU-PHL, 2021. Disponível em: https://github.com/MDU-PHL/emmtyper. Acesso em: 10 nov. 2026.

ENGELTHALER, David M. Genomic surveillance and pathogen intelligence. Frontiers in Science, v. 2, 1397048, 2024. DOI: 10.3389/fsci.2024.1397048.

FARIA, Nuno R. et al. Genomics and epidemiology of the P.1 SARS-CoV-2 lineage in Manaus, Brazil. Science, v. 372, n. 6544, p. 815–821, 2021. DOI: 10.1126/science.abh2644.

FROST, H. R. et al. Updated emm-typing protocol for Streptococcus pyogenes. Clinical Microbiology and Infection, v. 26, n. 7, p. 946.e5–946.e8, 2020. DOI: 10.1016/j.cmi.2020.02.026.

KHALAF, Wafaa S.; MORGAN, Radwa N.; ELKHATIB, Walid F. Clinical microbiology and artificial intelligence: different applications, challenges, and future prospects. Journal of Microbiological Methods, v. 232–234, 107125, 2025. DOI: 10.1016/j.mimet.2025.107125.

LATIF, Jahanzaib et al. Enhancing surveillance and early warning of infections and antimicrobial resistance using machine learning and deep learning: a systematic review. Neurocomputing, v. 684, 133502, 2026. DOI: 10.1016/j.neucom.2026.133502.

LIN, Anqi et al. Bridging artificial intelligence and biological sciences: a comprehensive review of large language models in bioinformatics. Briefings in Bioinformatics, v. 26, n. 4, bbaf357, 2025. DOI: 10.1093/bib/bbaf357.

LIU, Siru; MCCOY, Allison B.; WRIGHT, Adam. Improving large language model applications in biomedicine with retrieval-augmented generation: a systematic review, meta-analysis, and clinical development guidelines. Journal of the American Medical Informatics Association, v. 32, n. 4, p. 605–615, 2025. DOI: 10.1093/jamia/ocaf008.

LUO, Junyu; CAI, Xiyang; LI, Yixue. Large language models for biological sequence analysis in infectious disease research. Biosafety and Health, v. 7, n. 5, p. 323–332, 2025. DOI: 10.1016/j.bsheal.2025.09.007.

LYTRAS, Spyros et al. Pathogen genomic surveillance and the AI revolution. Journal of Virology, v. 99, n. 2, e01601-24, 2025. DOI: 10.1128/jvi.01601-24.

MARTINI, Caroline Lopes et al. Streptococcus pyogenes lineage ST62/emm87: the international spread of this potentially invasive lineage. Antibiotics, v. 12, n. 10, 1530, 2023. DOI: 10.3390/antibiotics12101530.

MCCRONE, John T. et al. Context-specific emergence and growth of the SARS-CoV-2 Delta variant. Nature, v. 610, n. 7930, p. 154–160, 2022. DOI: 10.1038/s41586-022-05200-3.

MENDES, Vanessa I. S. et al. Harnessing artificial intelligence for enhanced public health surveillance: a narrative review. Frontiers in Public Health, v. 13, 1601151, 2025. DOI: 10.3389/fpubh.2025.1601151.

PAN AMERICAN HEALTH ORGANIZATION (PAHO). Epidemiological update: invasive disease caused by group A Streptococcus. Washington, D.C.: PAHO/WHO, 21 June 2024. Disponível em: https://www.paho.org/sites/default/files/2024-06/2024-jun-21-phe-actualizacion-epidemiologica-enfermedad-invasiva-estreptococos-grupo-es.pdf. Acesso em: 10 nov. 2026.

PANTELI, Dimitra et al. Artificial intelligence in public health: promises, challenges, and an agenda for policy makers and public health institutions. The Lancet Public Health, v. 10, n. 5, p. e428–e432, 2025. DOI: 10.1016/S2468-2667(25)00036-2.

RÜMKE, Lidewij W. et al. Nationwide upsurge in invasive disease in the context of longitudinal surveillance of carriage and invasive Streptococcus pyogenes 2009–2023, the Netherlands: a molecular epidemiological study. Journal of Clinical Microbiology, v. 62, n. 10, e00766-24, 2024. DOI: 10.1128/jcm.00766-24.

RUSSO, D. O. et al. Invasive infections by group A Streptococcus in Brazil: a pediatric case series. Revista Paulista de Pediatria, v. 43, e2024100, 2025. DOI: 10.1590/1984-0462/2025/43/2024100.

SAMBRANO, Gustavo Enck. Determinantes de virulência em isolados clínicos de Streptococcus pyogenes da cidade de Porto Alegre. 2014. 78 f. Dissertação (Mestrado em Ciências da Saúde) — Universidade Federal de Ciências da Saúde de Porto Alegre, Porto Alegre, 2014. Disponível em: https://repositorio.ufcspa.edu.br/items/2d21ad88-2504-4317-9204-15e3d44f0970. Acesso em: 10 nov. 2026.

SEEMANN, Torsten. Prokka: rapid prokaryotic genome annotation. Bioinformatics, v. 30, n. 14, p. 2068–2069, 2014. DOI: 10.1093/bioinformatics/btu153.

SHANG, Xinyi et al. Benchmarking large language models for genomic knowledge with GeneTuring. Briefings in Bioinformatics, v. 26, n. 5, bbaf492, 2025. DOI: 10.1093/bib/bbaf492.

SMEESTERS, Pierre R. et al. Global Streptococcus pyogenes strain diversity, disease associations, and implications for vaccine development: a systematic review. The Lancet Microbe, v. 5, n. 2, p. e181–e193, 2024. DOI: 10.1016/S2666-5247(23)00318-X.

VIEIRA, Ana et al. Rapid expansion and international spread of M1UK in the post-pandemic UK upsurge of Streptococcus pyogenes. Nature Communications, v. 15, 3916, 2024. DOI: 10.1038/s41467-024-47929-7.

VILLANUEVA-MIRANDA, Ismael; XIAO, Guanghua; XIE, Yang. Artificial intelligence in early warning systems for infectious disease surveillance: a systematic review. Frontiers in Public Health, v. 13, 1609615, 2025. DOI: 10.3389/fpubh.2025.1609615.

VITIELLO, Antonio; ZOVI, Andrea. AI-enabled genomic surveillance for antimicrobial resistance: balancing effectiveness, trustworthiness and equity. Drug Resistance Updates, v. 90, 101486, 2026. DOI: 10.1016/j.drup.2026.101486.

WORLD HEALTH ORGANIZATION (WHO). Global genomic surveillance strategy for pathogens with pandemic and epidemic potential, 2022–2032. Geneva: WHO, 2022. ISBN 978-92-4-004697-9. Disponível em: https://iris.who.int/handle/10665/353022. Acesso em: 10 nov. 2026.

ZHOU, Siyu et al. VFDB 2025: an integrated resource for exploring anti-virulence compounds. Nucleic Acids Research, v. 53, n. D1, p. D871–D877, 2025. DOI: 10.1093/nar/gkae968.

10 APÊNDICE e/ou ANEXO

O Apêndice é um texto ou documento elaborado pelo autor do TCC, ou seja, se foi necessário você criar uma entrevista, um relatório, ou qualquer documento e, portanto deve-se utilizar o termo Apêndice e não Anexo.

Exemplos:
ANEXO – Documento ou texto não elaborado pelo autor
APÊNDICE – Documento ou texto elaborado pelo autor
