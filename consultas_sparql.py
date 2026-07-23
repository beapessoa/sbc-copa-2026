"""Parte 2 - Consultas SPARQL sobre a mesma base.

Cobertura exigida pelo enunciado:

    SELECT ............ consultas 1 a 5 (1 com FILTER, 1 com ORDER BY,
                        1 com agregacao GROUP BY/SUM/COUNT/HAVING, 1 com OPTIONAL)
    CONSTRUCT ......... consulta 6
    ASK ............... consulta 7
    INSERT ............ consulta 8
    DELETE ............ consulta 9
    DELETE/INSERT ..... consulta 10

As consultas 8, 9 e 10 alteram o grafo EM MEMORIA e imprimem o estado antes e
depois. O arquivo data/copa2026.ttl nunca e modificado.
"""

import util

PREFIXOS = """
PREFIX copa: <http://ufpb.br/sbc/copa2026#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""


def _linhas(resultado, colunas):
    return [[util.curto(linha[c]) for c in colunas] for linha in resultado]


# --------------------------------------------------------------------------- #
# SELECT
# --------------------------------------------------------------------------- #

def consulta_1(g):
    """Elenco de uma selecao com a posicao vinda da hierarquia de classes."""
    util.consulta(
        "Parte 2", 1,
        "Elenco da Argentina com posicao, camisa e clube",
        "juntar tres padroes pela variavel compartilhada ?j e ler a posicao do "
        "jogador a partir da subclasse que ele instancia",
    )
    q = PREFIXOS + """
    SELECT ?camisa ?nome ?posicao ?clube
    WHERE {
        ?j copa:jogaPor copa:selecao_ARG ;
           a ?posicaoClasse ;
           rdfs:label ?nome ;
           copa:numeroCamisa ?camisa ;
           copa:clubeAtual ?clube .
        ?posicaoClasse rdfs:subClassOf copa:Jogador ;
                       rdfs:label ?posicao .
        # apos o reasoner rdfs:subClassOf tambem e reflexiva, entao copa:Jogador
        # casaria consigo mesma e duplicaria cada jogador
        FILTER (?posicaoClasse != copa:Jogador)
    }
    ORDER BY ?camisa
    """
    util.tabela(
        ["camisa", "jogador", "posicao", "clube"],
        _linhas(g.query(q), ["camisa", "nome", "posicao", "clube"]),
        limite=10,
    )


def consulta_2(g):
    """SELECT com FILTER."""
    util.consulta(
        "Parte 2", 2,
        "Estadios grandes fora dos Estados Unidos",
        "filtrar por capacidade e por pais; o vinculo estadio->pais nao existe no "
        "arquivo, vem da transitividade de copa:localizadoEm",
        "Clausulas: FILTER (>) e FILTER NOT EXISTS",
    )
    q = PREFIXOS + """
    SELECT ?estadio ?cidade ?pais ?capacidade
    WHERE {
        ?e a copa:Estadio ;
           rdfs:label ?estadio ;
           copa:capacidade ?capacidade ;
           copa:localizadoEm ?c ,
                             ?p .
        ?c a copa:CidadeSede ; rdfs:label ?cidade .
        ?p a copa:Pais ; rdfs:label ?pais .
        FILTER (?capacidade > 45000)
        FILTER NOT EXISTS { ?e copa:localizadoEm copa:pais_USA }
    }
    ORDER BY DESC(?capacidade)
    """
    util.tabela(
        ["estadio", "cidade", "pais", "capacidade"],
        _linhas(g.query(q), ["estadio", "cidade", "pais", "capacidade"]),
    )


def consulta_3(g):
    """SELECT com ORDER BY e caminho de propriedade."""
    util.consulta(
        "Parte 2", 3,
        "Caminho da Espanha ate o titulo, em ordem cronologica",
        "reconstruir a campanha da campea usando um caminho de propriedade para "
        "chegar do jogo ate o pais",
        "Clausulas: ORDER BY e o caminho copa:sediadaEm/copa:localizadoEm+",
    )
    q = PREFIXOS + """
    SELECT ?data ?confronto ?estadio ?pais
    WHERE {
        ?m a copa:PartidaMataMata ;
           rdfs:label ?confronto ;
           copa:dataPartida ?data ;
           copa:sediadaEm ?e .
        { ?m copa:mandante copa:selecao_ESP } UNION { ?m copa:visitante copa:selecao_ESP }
        ?e rdfs:label ?estadio .
        ?m copa:sediadaEm/copa:localizadoEm+ ?p .
        ?p a copa:Pais ; rdfs:label ?pais .
    }
    ORDER BY ?data
    """
    util.tabela(
        ["data", "confronto", "estadio", "pais"],
        _linhas(g.query(q), ["data", "confronto", "estadio", "pais"]),
    )


def consulta_4(g):
    """SELECT com agregacao."""
    util.consulta(
        "Parte 2", 4,
        "Artilharia por selecao nas partidas modeladas",
        "somar os gols que cada selecao marcou, esteja ela como mandante ou como "
        "visitante, e manter apenas quem fez 5 ou mais",
        "Clausulas: UNION, GROUP BY, SUM, COUNT, HAVING e ORDER BY",
    )
    q = PREFIXOS + """
    SELECT ?selecao (SUM(?gols) AS ?golsMarcados) (COUNT(?m) AS ?partidas)
    WHERE {
        { ?m copa:mandante  ?s ; copa:golsMandante  ?gols }
        UNION
        { ?m copa:visitante ?s ; copa:golsVisitante ?gols }
        ?s rdfs:label ?selecao .
    }
    GROUP BY ?selecao
    HAVING (SUM(?gols) >= 5)
    ORDER BY DESC(?golsMarcados) ?selecao
    """
    util.tabela(
        ["selecao", "gols marcados", "partidas"],
        _linhas(g.query(q), ["selecao", "golsMarcados", "partidas"]),
    )


def consulta_5(g):
    """SELECT com OPTIONAL."""
    util.consulta(
        "Parte 2", 5,
        "Partidas do Grupo A e quem venceu cada uma",
        "listar as partidas mesmo quando nao ha vencedora registrada - o empate "
        "sem disputa de penaltis simplesmente nao tem essa tripla",
        "Clausula: OPTIONAL (o equivalente ao LEFT JOIN do SQL)",
    )
    q = PREFIXOS + """
    SELECT ?data ?confronto ?vencedora
    WHERE {
        ?m a copa:PartidaFaseGrupos ;
           rdfs:label ?confronto ;
           copa:dataPartida ?data .
        OPTIONAL {
            ?m copa:vencedora ?v .
            ?v rdfs:label ?vencedora .
        }
    }
    ORDER BY ?data ?confronto
    """
    resultado = list(g.query(q))
    util.tabela(
        ["data", "confronto", "vencedora"],
        [[util.curto(l["data"]), util.curto(l["confronto"]),
          util.curto(l["vencedora"]) if l["vencedora"] else "(empate)"]
         for l in resultado],
    )
    util.nota(
        "Sem OPTIONAL o empate desapareceria da resposta inteira, e nao apenas a "
        "coluna vazia."
    )


# --------------------------------------------------------------------------- #
# CONSTRUCT e ASK
# --------------------------------------------------------------------------- #

def consulta_6(g):
    """CONSTRUCT: monta um grafo derivado de confrontos.

    Emite SO a direcao mandante -> visitante. A direcao inversa nunca e escrita:
    ela vai aparecer sozinha na consulta 7, por causa de owl:SymmetricProperty.
    """
    util.consulta(
        "Parte 2", 6,
        "Grafo derivado: quem enfrentou quem",
        "transformar 38 partidas num grafo de confrontos entre selecoes, "
        "descartando placar, data e local",
        "Forma: CONSTRUCT (devolve um grafo RDF novo, nao uma tabela)",
    )
    q = PREFIXOS + """
    CONSTRUCT { ?a copa:enfrentou ?b }
    WHERE {
        ?m copa:mandante ?a ;
           copa:visitante ?b .
    }
    """
    derivado = g.query(q).graph
    print(f"  Grafo construido: {len(derivado)} triplas copa:enfrentou "
          f"(uma por partida, so no sentido mandante -> visitante)")
    print()
    # ordenado porque a iteracao sobre um Graph do rdflib nao tem ordem estavel
    amostra = sorted([util.rotulo(g, s), util.rotulo(g, o)] for s, _, o in derivado)
    util.tabela(["selecao", "enfrentou"], amostra, limite=8)

    # incorpora o grafo derivado a base em memoria, para a consulta 7
    for tripla in derivado:
        g.add(tripla)
    util.nota(
        f"As {len(derivado)} triplas foram incorporadas ao grafo em memoria.\n"
        "Repare que copa:selecao_ARG copa:enfrentou copa:selecao_ESP NAO esta entre "
        "elas:\n"
        "na final a Espanha era a mandante, entao so foi escrita ESP -> ARG."
    )


def consulta_7(g):
    """ASK: a simetria produziu a direcao que ninguem escreveu?"""
    util.consulta(
        "Parte 2", 7,
        "A Argentina enfrentou a Espanha?",
        "verificar se o reasoner derivou a direcao inversa do confronto a partir "
        "de owl:SymmetricProperty",
        "Forma: ASK (devolve apenas verdadeiro ou falso)",
    )
    q = PREFIXOS + """
    ASK { copa:selecao_ARG copa:enfrentou copa:selecao_ESP }
    """
    antes = bool(g.query(q))
    print(f"  Antes de reaplicar o reasoner: {antes}")

    from owlrl import DeductiveClosure, OWLRL_Semantics
    DeductiveClosure(OWLRL_Semantics).expand(g)

    depois = bool(g.query(q))
    print(f"  Depois de reaplicar o reasoner: {depois}")
    util.nota(
        "A tripla ARG -> ESP nunca foi escrita por ninguem: nem no arquivo .ttl, "
        "nem\npelo CONSTRUCT da consulta 6. Ela existe porque copa:enfrentou foi "
        "declarada\ncomo owl:SymmetricProperty."
    )


# --------------------------------------------------------------------------- #
# UPDATE - as tres formas
# --------------------------------------------------------------------------- #

def _conta(g, consulta_contagem):
    return int(list(g.query(PREFIXOS + consulta_contagem))[0][0])


def consulta_8(g):
    """INSERT ... WHERE - regra de producao declarativa."""
    util.consulta(
        "Parte 2", 8,
        "INSERT: classificar automaticamente as semifinalistas",
        "derivar uma classificacao nova a partir dos fatos existentes, em vez de "
        "digitar quem chegou a semifinal",
        "Forma: INSERT ... WHERE (condicao -> acao, como uma regra de producao)",
    )
    contagem = "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a copa:Semifinalista }"
    print(f"  ANTES : {_conta(g, contagem)} selecoes classificadas como copa:Semifinalista")

    g.update(PREFIXOS + """
    INSERT { ?s a copa:Semifinalista }
    WHERE {
        ?m a copa:PartidaSemifinal .
        { ?m copa:mandante ?s } UNION { ?m copa:visitante ?s }
    }
    """)

    print(f"  DEPOIS: {_conta(g, contagem)} selecoes classificadas como copa:Semifinalista")
    print()
    q = PREFIXOS + """
    SELECT ?selecao ?colocacao
    WHERE {
        ?s a copa:Semifinalista ; rdfs:label ?selecao ; copa:posicaoNoGrupo ?colocacao .
    }
    ORDER BY ?selecao
    """
    util.tabela(
        ["selecao", "colocacao no grupo"],
        _linhas(g.query(q), ["selecao", "colocacao"]),
    )


def consulta_9(g):
    """DELETE ... WHERE - remocao de fatos."""
    util.consulta(
        "Parte 2", 9,
        "DELETE: cortar um jogador do elenco da Espanha",
        "simular um corte por lesao, removendo a convocacao de Borja Iglesias",
        "Forma: DELETE ... WHERE",
    )
    contagem = "SELECT (COUNT(?j) AS ?n) WHERE { ?j copa:jogaPor copa:selecao_ESP }"
    print(f"  ANTES : elenco da Espanha com {_conta(g, contagem)} jogadores")

    g.update(PREFIXOS + """
    DELETE {
        ?j copa:jogaPor copa:selecao_ESP .
        copa:selecao_ESP copa:temJogador ?j .
    }
    WHERE {
        ?j copa:jogaPor copa:selecao_ESP ;
           rdfs:label "Borja Iglesias" .
    }
    """)

    print(f"  DEPOIS: elenco da Espanha com {_conta(g, contagem)} jogadores")
    util.nota(
        "O DELETE apaga as duas direcoes de proposito. A tripla copa:temJogador foi\n"
        "materializada pelo reasoner, e inferencia ja gravada no grafo nao se retrai\n"
        "sozinha quando o fato de origem some."
    )


def consulta_10(g):
    """DELETE ... INSERT ... WHERE - transicao de estado."""
    util.consulta(
        "Parte 2", 10,
        "DELETE/INSERT: trocar o tecnico da selecao brasileira",
        "simular a substituicao do comando tecnico: o WHERE fixa os vinculos, o "
        "DELETE desfaz o antigo e o INSERT cria o novo, na mesma operacao",
        "Forma: DELETE ... INSERT ... WHERE",
    )
    q = PREFIXOS + """
    SELECT ?tecnico WHERE { ?t copa:treina copa:selecao_BRA ; rdfs:label ?tecnico . }
    """
    atual = [util.curto(l["tecnico"]) for l in g.query(q)]
    print(f"  ANTES : tecnico do Brasil = {', '.join(atual) or '(nenhum)'}")

    g.update(PREFIXOS + """
    DELETE { ?antigo copa:treina copa:selecao_BRA }
    INSERT {
        copa:tecnico_novo_comando a copa:Tecnico ;
            rdfs:label "Jorge Jesus" ;
            copa:treina copa:selecao_BRA .
    }
    WHERE {
        ?antigo copa:treina copa:selecao_BRA .
    }
    """)

    novo = [util.curto(l["tecnico"]) for l in g.query(q)]
    print(f"  DEPOIS: tecnico do Brasil = {', '.join(novo) or '(nenhum)'}")
    util.nota(
        "Operacao hipotetica, so para demonstrar a forma DELETE/INSERT.\n"
        "Como copa:treina e owl:FunctionalProperty, deixar os dois tecnicos ligados a\n"
        "mesma selecao faria o reasoner concluir que sao a mesma pessoa - por isso a\n"
        "remocao e a insercao precisam acontecer juntas."
    )


TODAS = [
    consulta_1, consulta_2, consulta_3, consulta_4, consulta_5,
    consulta_6, consulta_7, consulta_8, consulta_9, consulta_10,
]


def executar(g):
    util.banner("PARTE 2 - CONSULTAS SPARQL")
    for fn in TODAS:
        fn(g)
