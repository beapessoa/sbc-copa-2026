"""Interface Streamlit sobre a base da Copa 2026.

    pip install -r requirements-app.txt
    streamlit run app.py
"""

import contextlib
import inspect
import io
import textwrap

import streamlit as st
from rdflib import Graph
from rdflib.namespace import OWL, RDF

import base
import consultas_sparql
import consultas_triples
from base import COPA

st.set_page_config(page_title="Copa 2026 - Base de Conhecimento", page_icon="⚽",
                   layout="wide")


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #

@st.cache_resource
def grafo_puro():
    """Grafo como esta no arquivo, sem inferencia."""
    return base.carregar()


@st.cache_resource
def grafo_inferido():
    """Grafo depois do reasoner OWL-RL."""
    g = base.carregar()
    base.aplicar_reasoner(g)
    return g


def copia(g):
    """Copia do grafo, para as consultas que alteram conteudo."""
    novo = Graph()
    novo.bind("copa", COPA)
    for tripla in g:
        novo.add(tripla)
    return novo


def saida_de(funcao, g):
    """Captura o que a consulta imprimiria no terminal."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        funcao(g)
    return buffer.getvalue()


def tabela_sparql(g, consulta):
    resultado = g.query(consulta)
    colunas = [str(v) for v in resultado.vars]
    return colunas, [
        {c: (str(linha[c]).split("#")[-1] if linha[c] is not None else "")
         for c in colunas}
        for linha in resultado
    ]


# --------------------------------------------------------------------------- #
# Navegacao
# --------------------------------------------------------------------------- #

SECOES = [
    "Visão geral",
    "Taxonomia",
    "Inferência OWL",
    "Parte 1 — g.triples()",
    "Parte 2 — SPARQL",
    "Consulta livre",
]

st.sidebar.title("⚽ Copa do Mundo 2026")
st.sidebar.caption("Base de conhecimento em RDF/RDFS/OWL")
secao = st.sidebar.radio("Seção", SECOES, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(
    "Mini-Projeto 3 — Sistemas Baseados em Conhecimento\n\n"
    "Beatriz Almeida · Emyle Lucena · Marcus Vinicius · Maria Clara Dantas"
)


# --------------------------------------------------------------------------- #
# 1. Visao geral
# --------------------------------------------------------------------------- #

if secao == "Visão geral":
    st.title("Base de conhecimento da Copa do Mundo FIFA 2026")
    st.markdown(
        "Modelada em RDF/RDFS/OWL, entregue em Turtle e consultada com rdflib "
        "e SPARQL. Dados reais, extraídos da Wikipédia."
    )

    g = grafo_puro()
    gi = grafo_inferido()

    classes = {c for c in g.subjects(RDF.type, OWL.Class) if str(c).startswith(str(COPA))}
    obj = set(g.subjects(RDF.type, OWL.ObjectProperty))
    dat = set(g.subjects(RDF.type, OWL.DatatypeProperty))
    inst = {s for s, o in g.subject_objects(RDF.type) if o in classes}

    st.subheader("A base em números")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Triplas no arquivo · mín. 50", f"{len(g):,}".replace(",", "."))
    c2.metric("Classes · mín. 8", len(classes))
    c3.metric("Propriedades · mín. 10", len(obj) + len(dat))
    c4.metric("Instâncias · mín. 25", len(inst))

    st.info(
        f"Após o reasoner: **{len(g)} → {len(gi)}** triplas "
        f"({len(gi) - len(g)} inferidas).",
        icon="🧠",
    )

    st.subheader("O que está modelado")
    esq, dir_ = st.columns(2)
    with esq:
        st.markdown(
            "**Entram completos**\n\n"
            "- as 48 seleções\n"
            "- os 12 grupos, com classificação final\n"
            "- os 16 estádios, com capacidade\n"
            "- as 16 cidades-sede\n"
            "- as 4 posições em campo"
        )
    with dir_:
        st.markdown(
            "**Recorte**\n\n"
            "- **38 partidas** de 104: o mata-mata inteiro mais o Grupo A\n"
            "- **208 jogadores**: os elencos de 26 convocados de 8 seleções — "
            "as 4 semifinalistas mais Brasil, Noruega, Marrocos e México"
        )
    st.caption(
        "As 8 seleções com elenco são as que jogam as partidas modeladas."
    )

    st.subheader("Instâncias por classe")
    contagem = {}
    for s, o in g.subject_objects(RDF.type):
        if o in classes:
            nome = str(o).split("#")[-1]
            contagem[nome] = contagem.get(nome, 0) + 1
    st.dataframe(
        [{"classe": k, "instâncias": v}
         for k, v in sorted(contagem.items(), key=lambda kv: -kv[1])],
        width="stretch", hide_index=True, height=320,
    )

    with st.expander("De onde vieram os dados"):
        st.markdown(
            "Transcritos da Wikipédia em julho de 2026:\n\n"
            "- `2026 FIFA World Cup` — sedes, estádios e capacidades\n"
            "- `2026 FIFA World Cup squads` — elencos com número, posição, "
            "nascimento e clube\n"
            "- `2026 FIFA World Cup round of 32` / `knockout stage` / `final` — partidas\n"
            "- `2026 FIFA World Cup Group A` — partidas da fase de grupos\n"
            "- `Template:2026 FIFA World Cup group tables` — os 12 grupos\n\n"
            "Onde a fonte não confirmava um valor, a tripla foi omitida — é o caso "
            "de `copa:vencedora` no empate Chéquia 1×1 África do Sul, sem pênaltis."
        )


# --------------------------------------------------------------------------- #
# 2. Taxonomia
# --------------------------------------------------------------------------- #

elif secao == "Taxonomia":
    st.title("Taxonomia")
    st.markdown("Quatro raízes independentes.")

    esq, dir_ = st.columns(2)

    with esq:
        st.subheader("Pessoa")
        st.code(
            "Pessoa\n"
            "├── Jogador\n"
            "│   ├── Goleiro\n"
            "│   ├── Defensor\n"
            "│   ├── MeioCampista\n"
            "│   └── Atacante\n"
            "├── Tecnico\n"
            "└── Arbitro",
            language=None,
        )
        st.caption(
            "A posição é subclasse, não atributo: \"liste os goleiros\" vira consulta "
            "por tipo, e todo Goleiro também é Jogador e Pessoa."
        )

        st.subheader("Local")
        st.code(
            "Local\n"
            "├── Pais            (53)\n"
            "├── Cidade\n"
            "│   └── CidadeSede  (16)\n"
            "└── Estadio         (16)",
            language=None,
        )
        st.caption(
            "Só os elos curtos são escritos. O vínculo estádio → país vem da "
            "transitividade. O mesmo recurso de país serve de sede, de país "
            "representado pela seleção e de federação do árbitro."
        )

    with dir_:
        st.subheader("Partida")
        st.code(
            "Partida\n"
            "├── PartidaFaseGrupos\n"
            "└── PartidaMataMata\n"
            "    ├── Partida16Avos\n"
            "    ├── PartidaOitavas\n"
            "    ├── PartidaQuartas\n"
            "    ├── PartidaSemifinal\n"
            "    ├── PartidaTerceiroLugar\n"
            "    └── PartidaFinal",
            language=None,
        )
        st.caption(
            "A fase é a classe da partida. Com 48 seleções o mata-mata começa nos "
            "16-avos, não nas oitavas."
        )

        st.subheader("Entidades organizacionais")
        st.code(
            "Selecao                Grupo (A–L)\n"
            "└── Semifinalista\n"
            "\n"
            "Confederacao\n"
            "(UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC)",
            language=None,
        )
        st.caption(
            "`Semifinalista` não tem instância no arquivo: é povoada pela regra "
            "INSERT da consulta 8."
        )

    st.divider()
    st.subheader("Propriedades")
    a, b = st.columns(2)
    a.markdown(
        "**De objeto (14)**\n\n"
        "`jogaPor` · `temJogador` · `treina` · `pertenceAoGrupo` · `filiadaA` · "
        "`equipeA` · `equipeB` · `sediadaEm` · `vencedora` · `apitou` · "
        "`representa` · `nacionalidade` · `localizadoEm` · `enfrentou`"
    )
    b.markdown(
        "**De dados (13)**\n\n"
        "`numeroCamisa` · `dataNascimento` · `clubeAtual` · `jogosPelaSelecao` · "
        "`golsPelaSelecao` · `capacidade` · `dataPartida` · `golsEquipeA` · "
        "`golsEquipeB` · `publico` · `letraGrupo` · `posicaoNoGrupo` · `codigoFIFA`"
    )
    st.caption(
        "Todas as 27 declaram `rdfs:domain` e `rdfs:range`. Dois `rdfs:domain` na "
        "mesma propriedade significariam interseção de classes, não união — por "
        "isso os rótulos usam `rdfs:label`."
    )


# --------------------------------------------------------------------------- #
# 3. Inferencia OWL - a demonstracao principal
# --------------------------------------------------------------------------- #

elif secao == "Inferência OWL":
    st.title("Inferência OWL")
    st.markdown("A **mesma consulta**, rodando com e sem o reasoner.")

    demo = st.radio(
        "Construção a demonstrar",
        ["owl:inverseOf", "owl:TransitiveProperty", "owl:SymmetricProperty"],
        horizontal=True,
    )

    g0, g1 = grafo_puro(), grafo_inferido()

    if demo == "owl:inverseOf":
        st.markdown(
            "O arquivo escreve só o sentido jogador → seleção (`copa:jogaPor`). "
            "Nenhuma tripla `copa:temJogador` existe no `.ttl`."
        )
        consulta = """
        PREFIX copa: <http://ufpb.br/sbc/copa2026#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?jogador ?camisa
        WHERE {
            copa:selecao_ESP copa:temJogador ?j .
            ?j rdfs:label ?jogador ; copa:numeroCamisa ?camisa .
        }
        ORDER BY ?camisa
        """
        declaracao = "copa:jogaPor owl:inverseOf copa:temJogador ."

    elif demo == "owl:TransitiveProperty":
        st.markdown(
            "O arquivo liga estádio → cidade e cidade → país. Nenhuma tripla liga "
            "estádio a país."
        )
        consulta = """
        PREFIX copa: <http://ufpb.br/sbc/copa2026#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?estadio ?pais
        WHERE {
            ?e a copa:Estadio ; rdfs:label ?estadio ; copa:localizadoEm ?p .
            ?p a copa:Pais ; rdfs:label ?pais .
        }
        ORDER BY ?estadio
        """
        declaracao = "copa:localizadoEm a owl:ObjectProperty , owl:TransitiveProperty ."

    else:
        st.markdown(
            "O CONSTRUCT monta os confrontos só no sentido equipe A → equipe B. "
            "Na final a Espanha é a equipe A, então só existe ESP → ARG."
        )
        consulta = """
        PREFIX copa: <http://ufpb.br/sbc/copa2026#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?selecao
        WHERE {
            copa:selecao_ARG copa:enfrentou ?s .
            ?s rdfs:label ?selecao .
        }
        ORDER BY ?selecao
        """
        declaracao = "copa:enfrentou a owl:ObjectProperty , owl:SymmetricProperty ."

        # o grafo de confrontos precisa existir nos dois lados da comparacao
        construct = """
        PREFIX copa: <http://ufpb.br/sbc/copa2026#>
        CONSTRUCT { ?a copa:enfrentou ?b }
        WHERE { ?m copa:equipeA ?a ; copa:equipeB ?b . }
        """
        g0, g1 = copia(g0), copia(g1)
        for grafo in (g0, g1):
            for tripla in grafo.query(construct).graph:
                grafo.add(tripla)
        from owlrl import DeductiveClosure, OWLRL_Semantics
        DeductiveClosure(OWLRL_Semantics).expand(g1)

    st.code(declaracao, language="turtle")
    st.code(textwrap.dedent(consulta).strip(), language="sparql")

    esq, dir_ = st.columns(2)
    for coluna, grafo, titulo in [(esq, g0, "Sem reasoner"), (dir_, g1, "Com reasoner")]:
        with coluna:
            colunas, linhas = tabela_sparql(grafo, consulta)
            if linhas:
                st.success(f"**{titulo}** — {len(linhas)} resultado(s)")
                st.dataframe(linhas, width="stretch", hide_index=True,
                             height=min(400, 40 + 35 * len(linhas)))
            else:
                st.error(f"**{titulo}** — 0 resultados")
                st.caption("A base, sozinha, não responde.")

    st.divider()
    st.subheader("As 7 construções OWL")
    st.dataframe(
        [
            {"construção": "owl:inverseOf", "onde": "jogaPor ⁻¹ temJogador",
             "para quê": "escrever a convocação de um lado só e inferir o elenco"},
            {"construção": "owl:TransitiveProperty", "onde": "localizadoEm",
             "para quê": "estádio → cidade → país sem duplicar vínculo"},
            {"construção": "owl:SymmetricProperty", "onde": "enfrentou",
             "para quê": "se A enfrentou B, B enfrentou A"},
            {"construção": "owl:FunctionalProperty", "onde": "sediadaEm, treina e outras",
             "para quê": "no máximo um valor por sujeito"},
            {"construção": "owl:InverseFunctionalProperty", "onde": "codigoFIFA",
             "para quê": "chave global: \"BRA\" identifica a seleção entre bases"},
            {"construção": "owl:disjointWith", "onde": "9 pares de classes",
             "para quê": "ninguém é goleiro e atacante"},
            {"construção": "owl:propertyDisjointWith", "onde": "equipeA ⊥ equipeB",
             "para quê": "ninguém joga contra si mesmo"},
        ],
        width="stretch", hide_index=True,
    )


# --------------------------------------------------------------------------- #
# 4. Parte 1
# --------------------------------------------------------------------------- #

elif secao == "Parte 1 — g.triples()":
    st.title("Parte 1 — consultas com `g.triples()`")
    st.markdown(
        "Combinações do padrão (sujeito, predicado, objeto), com `None` como coringa."
    )

    rotulos = [
        "1 · (S, None, None) — tudo sobre a Espanha",
        "2 · (None, P, None) — capacidade dos estádios",
        "3 · (None, rdf:type, O) — os goleiros da base",
        "4 · (S, P, None) — elenco da Espanha, só por inferência",
        "5 · (None, P, O) — seleções do Grupo A",
        "6 · (S, P, O) — teste de existência",
        "7 · (None, None, O) — conexões do MetLife Stadium",
    ]
    escolha = st.selectbox("Consulta", range(7), format_func=lambda i: rotulos[i])
    funcao = consultas_triples.TODAS[escolha]

    with st.expander("Código-fonte da consulta"):
        st.code(inspect.getsource(funcao), language="python")

    st.code(saida_de(funcao, grafo_inferido()), language=None)


# --------------------------------------------------------------------------- #
# 5. Parte 2
# --------------------------------------------------------------------------- #

elif secao == "Parte 2 — SPARQL":
    st.title("Parte 2 — consultas SPARQL")
    st.markdown(
        "SELECT (com FILTER, ORDER BY, agregação e OPTIONAL), CONSTRUCT, ASK e as "
        "três formas de Update."
    )

    rotulos = [
        "1 · SELECT — elenco da Argentina com posição",
        "2 · SELECT + FILTER — estádios grandes fora dos EUA",
        "3 · SELECT + ORDER BY + caminho — campanha da Espanha",
        "4 · SELECT + GROUP BY/SUM/HAVING — artilharia por seleção",
        "5 · SELECT + OPTIONAL — partidas do Grupo A e vencedoras",
        "6 · CONSTRUCT — grafo de confrontos",
        "7 · ASK — a simetria funcionou?",
        "8 · INSERT — classificar as semifinalistas",
        "9 · DELETE — cortar um jogador do elenco",
        "10 · DELETE/INSERT — trocar o técnico",
    ]
    escolha = st.selectbox("Consulta", range(10), format_func=lambda i: rotulos[i])
    funcao = consultas_sparql.TODAS[escolha]

    if escolha >= 5:
        st.warning(
            "Altera o grafo. Roda sobre uma cópia; `data/copa2026.ttl` não muda.",
            icon="✏️",
        )

    with st.expander("Código-fonte da consulta"):
        st.code(inspect.getsource(funcao), language="python")

    g = copia(grafo_inferido())
    if escolha == 6:  # o ASK depende do CONSTRUCT
        with contextlib.redirect_stdout(io.StringIO()):
            consultas_sparql.consulta_6(g)
    st.code(saida_de(funcao, g), language=None)


# --------------------------------------------------------------------------- #
# 6. Consulta livre
# --------------------------------------------------------------------------- #

elif secao == "Consulta livre":
    st.title("Consulta livre")
    st.markdown("Aceita `SELECT`, `ASK` e `CONSTRUCT`.")

    exemplos = {
        "Jogadores mais velhos da base": """PREFIX copa: <http://ufpb.br/sbc/copa2026#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?jogador ?nascimento ?selecao
WHERE {
    ?j a copa:Jogador ;
       rdfs:label ?jogador ;
       copa:dataNascimento ?nascimento ;
       copa:jogaPor ?s .
    ?s rdfs:label ?selecao .
}
ORDER BY ?nascimento
LIMIT 10""",
        "Árbitros que mais apitaram": """PREFIX copa: <http://ufpb.br/sbc/copa2026#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?arbitro ?pais (COUNT(?m) AS ?partidas)
WHERE {
    ?a a copa:Arbitro ;
       rdfs:label ?arbitro ;
       copa:nacionalidade ?p ;
       copa:apitou ?m .
    ?p rdfs:label ?pais .
}
GROUP BY ?arbitro ?pais
ORDER BY DESC(?partidas) ?arbitro""",
        "Clubes com mais convocados": """PREFIX copa: <http://ufpb.br/sbc/copa2026#>

SELECT ?clube (COUNT(?j) AS ?convocados)
WHERE { ?j a copa:Jogador ; copa:clubeAtual ?clube . }
GROUP BY ?clube
HAVING (COUNT(?j) >= 4)
ORDER BY DESC(?convocados) ?clube""",
        "Países que têm seleção e árbitro": """PREFIX copa: <http://ufpb.br/sbc/copa2026#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Só funciona porque a seleção e o árbitro apontam para o MESMO recurso de país
SELECT ?pais (COUNT(DISTINCT ?a) AS ?arbitros)
WHERE {
    ?a a copa:Arbitro ; copa:nacionalidade ?p .
    ?s copa:representa ?p .
    ?p rdfs:label ?pais .
}
GROUP BY ?pais
ORDER BY DESC(?arbitros) ?pais""",
        "Seleções por confederação": """PREFIX copa: <http://ufpb.br/sbc/copa2026#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?confederacao (COUNT(?s) AS ?selecoes)
WHERE {
    ?s a copa:Selecao ; copa:filiadaA ?c .
    ?c rdfs:label ?confederacao .
}
GROUP BY ?confederacao
ORDER BY DESC(?selecoes)""",
    }

    exemplo = st.selectbox("Começar de um exemplo", list(exemplos))
    texto = st.text_area("SPARQL", exemplos[exemplo], height=280)

    usar_reasoner = st.toggle(
        "Consultar o grafo com inferência", value=True,
        help="Desligado, consulta só as triplas escritas no arquivo.",
    )

    if st.button("Executar", type="primary"):
        g = grafo_inferido() if usar_reasoner else grafo_puro()
        try:
            resultado = g.query(texto)
            if resultado.type == "ASK":
                st.metric("Resposta", str(bool(resultado)))
            elif resultado.type == "CONSTRUCT":
                st.success(f"{len(resultado.graph)} triplas construídas")
                st.code(resultado.graph.serialize(format="turtle"), language="turtle")
            else:
                colunas, linhas = tabela_sparql(g, texto)
                st.success(f"{len(linhas)} resultado(s)")
                st.dataframe(linhas, width="stretch", hide_index=True)
        except Exception as erro:
            st.error(f"Erro na consulta: {erro}")
