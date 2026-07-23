"""Interface Streamlit para apresentar a base de conhecimento da Copa 2026.

EXTRA OPCIONAL. A entrega do mini-projeto continua sendo `python main.py`;
este arquivo existe so para a apresentacao em video e nao altera nada da base
nem das consultas - ele reaproveita os mesmos modulos.

Uso:
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
# Carga (em cache, para a navegacao ficar instantanea no video)
# --------------------------------------------------------------------------- #

@st.cache_resource
def grafo_puro():
    """Grafo exatamente como esta no arquivo .ttl, sem inferencia."""
    return base.carregar()


@st.cache_resource
def grafo_inferido():
    """Grafo depois do reasoner OWL-RL."""
    g = base.carregar()
    base.aplicar_reasoner(g)
    return g


def copia(g):
    """Copia rasa do grafo, para consultas que alteram o conteudo."""
    novo = Graph()
    novo.bind("copa", COPA)
    for tripla in g:
        novo.add(tripla)
    return novo


def saida_de(funcao, g):
    """Captura o que a funcao de consulta imprimiria no terminal."""
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
        "Modelada em **RDF/RDFS/OWL**, entregue em Turtle e consultada com "
        "**rdflib** e **SPARQL**. Todos os dados são reais, extraídos da Wikipédia."
    )

    g = grafo_puro()
    gi = grafo_inferido()

    classes = {c for c in g.subjects(RDF.type, OWL.Class) if str(c).startswith(str(COPA))}
    obj = set(g.subjects(RDF.type, OWL.ObjectProperty))
    dat = set(g.subjects(RDF.type, OWL.DatatypeProperty))
    inst = {s for s, o in g.subject_objects(RDF.type) if o in classes}

    st.subheader("A base em números")
    # o minimo vai no rotulo: como delta, o Streamlit desenha uma seta de
    # variacao que daria a entender que o numero subiu
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Triplas no arquivo · mín. 50", f"{len(g):,}".replace(",", "."))
    c2.metric("Classes · mín. 8", len(classes))
    c3.metric("Propriedades · mín. 10", len(obj) + len(dat))
    c4.metric("Instâncias · mín. 25", len(inst))

    st.info(
        f"Depois do reasoner o grafo vai de **{len(g)}** para **{len(gi)}** triplas — "
        f"**{len(gi) - len(g)} fatos derivados** que ninguém escreveu.",
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
            "**Recorte deliberado**\n\n"
            "- **38 partidas** de 104: todo o mata-mata (16-avos até a final) "
            "mais o Grupo A completo\n"
            "- **208 jogadores**: os elencos oficiais de 26 convocados de "
            "8 seleções — as 4 semifinalistas mais Brasil, Noruega, Marrocos e México"
        )
    st.caption(
        "O recorte segue o próprio enunciado, que pede as quantidades mínimas "
        "\"com informação real, sem inflar a base\". As 8 seleções com elenco são "
        "exatamente as que aparecem nas partidas modeladas, então toda consulta que "
        "cruza jogador → seleção → partida devolve resultado."
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
            "Onde a fonte não confirmava um valor, a tripla foi **omitida** em vez de "
            "estimada — é o caso de `copa:vencedora` no empate de Chéquia 1×1 África "
            "do Sul, que não teve pênaltis."
        )


# --------------------------------------------------------------------------- #
# 2. Taxonomia
# --------------------------------------------------------------------------- #

elif secao == "Taxonomia":
    st.title("Taxonomia")
    st.markdown("O domínio se organiza em **quatro raízes independentes**.")

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
            "A posição em campo é **subclasse**, não atributo. Assim \"liste os "
            "goleiros\" é uma consulta por tipo, e o reasoner sabe que todo Goleiro "
            "também é Jogador e Pessoa."
        )

        st.subheader("Local")
        st.code(
            "Local\n"
            "├── Pais            (3)\n"
            "├── Cidade\n"
            "│   └── CidadeSede  (16)\n"
            "└── Estadio         (16)",
            language=None,
        )
        st.caption(
            "Só os elos curtos são escritos: estádio → cidade, cidade → país. "
            "O vínculo estádio → país vem da transitividade."
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
            "A fase do torneio é a classe da partida. Com 48 seleções, o mata-mata "
            "de 2026 começa nos **16-avos**, não nas oitavas. "
            "`PartidaMataMata` é declarada `owl:equivalentClass` de "
            "`PartidaEliminatoria`."
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
            "`Semifinalista` é uma **classe derivada**: não tem instância no arquivo. "
            "É povoada em execução pela regra INSERT da consulta 8."
        )

    st.divider()
    st.subheader("Propriedades")
    a, b = st.columns(2)
    a.markdown(
        "**De objeto (12)**\n\n"
        "`jogaPor` · `temJogador` · `treina` · `pertenceAoGrupo` · `filiadaA` · "
        "`mandante` · `visitante` · `sediadaEm` · `vencedora` · `apitou` · "
        "`localizadoEm` · `enfrentou`"
    )
    b.markdown(
        "**De dados (14)**\n\n"
        "`numeroCamisa` · `dataNascimento` · `clubeAtual` · `jogosPelaSelecao` · "
        "`golsPelaSelecao` · `paisDeOrigem` · `capacidade` · `dataPartida` · "
        "`golsMandante` · `golsVisitante` · `publico` · `letraGrupo` · "
        "`posicaoNoGrupo` · `codigoFIFA`"
    )
    st.caption(
        "Todas as 26 declaram `rdfs:domain` e `rdfs:range`. Os rótulos legíveis usam "
        "`rdfs:label`, sem domain — dois `rdfs:domain` na mesma propriedade "
        "significariam **interseção** de classes, não união."
    )


# --------------------------------------------------------------------------- #
# 3. Inferencia OWL - a demonstracao principal
# --------------------------------------------------------------------------- #

elif secao == "Inferência OWL":
    st.title("Inferência OWL")
    st.markdown(
        "As 7 construções OWL não são decorativas. Abaixo, a **mesma consulta** "
        "rodando com e sem o reasoner."
    )

    demo = st.radio(
        "Construção a demonstrar",
        ["owl:inverseOf", "owl:TransitiveProperty", "owl:SymmetricProperty"],
        horizontal=True,
    )

    g0, g1 = grafo_puro(), grafo_inferido()

    if demo == "owl:inverseOf":
        st.markdown(
            "**A convocação é um fato só, visto de dois lados.** O arquivo escreve "
            "apenas jogador → seleção (`copa:jogaPor`). Não existe **uma tripla "
            "sequer** de `copa:temJogador` no `.ttl`."
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
            "**Só os elos curtos são escritos**: estádio → cidade e cidade → país. "
            "A pergunta \"em que país fica este estádio?\" nunca foi respondida por "
            "uma tripla explícita."
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
            "**Enfrentar não tem lado.** O CONSTRUCT monta o grafo de confrontos só "
            "no sentido mandante → visitante. Na final a Espanha era a mandante, "
            "então só foi escrita ESP → ARG."
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
        WHERE { ?m copa:mandante ?a ; copa:visitante ?b . }
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
                st.caption("A base, sozinha, não sabe responder.")

    st.divider()
    st.subheader("As 7 construções e o que cada uma resolve")
    st.dataframe(
        [
            {"construção": "owl:inverseOf", "onde": "jogaPor ⁻¹ temJogador",
             "para quê": "escrever a convocação de um lado só e inferir o elenco"},
            {"construção": "owl:TransitiveProperty", "onde": "localizadoEm",
             "para quê": "estádio → cidade → país sem duplicar vínculo"},
            {"construção": "owl:SymmetricProperty", "onde": "enfrentou",
             "para quê": "se A enfrentou B, B enfrentou A"},
            {"construção": "owl:FunctionalProperty", "onde": "sediadaEm, treina, e outras",
             "para quê": "cada uma tem no máximo um valor"},
            {"construção": "owl:InverseFunctionalProperty", "onde": "codigoFIFA",
             "para quê": "\"BRA\" é chave global: identifica a seleção entre bases"},
            {"construção": "owl:disjointWith", "onde": "9 pares de classes",
             "para quê": "ninguém é goleiro e atacante — erro fica detectável"},
            {"construção": "owl:equivalentClass", "onde": "MataMata ≡ Eliminatoria",
             "para quê": "integrar base externa que use o outro termo"},
        ],
        width="stretch", hide_index=True,
    )


# --------------------------------------------------------------------------- #
# 4. Parte 1
# --------------------------------------------------------------------------- #

elif secao == "Parte 1 — g.triples()":
    st.title("Parte 1 — consultas com `g.triples()`")
    st.markdown(
        "Sete consultas percorrendo **todas as combinações** do padrão "
        "(sujeito, predicado, objeto), com `None` como coringa."
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
        "Dez consultas cobrindo **SELECT** (com FILTER, ORDER BY, agregação e "
        "OPTIONAL), **CONSTRUCT**, **ASK** e as **três formas de Update**."
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
            "Esta consulta **altera o grafo**. Ela roda sobre uma cópia em memória; "
            "o arquivo `data/copa2026.ttl` nunca é modificado.",
            icon="✏️",
        )

    with st.expander("Código-fonte da consulta"):
        st.code(inspect.getsource(funcao), language="python")

    g = copia(grafo_inferido())
    if escolha == 6:  # o ASK depende do CONSTRUCT ter rodado antes
        with contextlib.redirect_stdout(io.StringIO()):
            consultas_sparql.consulta_6(g)
    st.code(saida_de(funcao, g), language=None)


# --------------------------------------------------------------------------- #
# 6. Consulta livre
# --------------------------------------------------------------------------- #

elif secao == "Consulta livre":
    st.title("Consulta livre")
    st.markdown("Escreva SPARQL contra a base. Aceita `SELECT`, `ASK` e `CONSTRUCT`.")

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
       copa:paisDeOrigem ?pais ;
       copa:apitou ?m .
}
GROUP BY ?arbitro ?pais
ORDER BY DESC(?partidas) ?arbitro""",
        "Clubes com mais convocados": """PREFIX copa: <http://ufpb.br/sbc/copa2026#>

SELECT ?clube (COUNT(?j) AS ?convocados)
WHERE { ?j a copa:Jogador ; copa:clubeAtual ?clube . }
GROUP BY ?clube
HAVING (COUNT(?j) >= 4)
ORDER BY DESC(?convocados) ?clube""",
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
        help="Desligado, consulta apenas as triplas escritas no arquivo .ttl.",
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
