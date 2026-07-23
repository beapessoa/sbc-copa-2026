"""Parte 1 - Consultas com g.triples() (API de padroes de tripla do rdflib).

Sao 7 consultas que percorrem todas as combinacoes possiveis do padrao
(sujeito, predicado, objeto), usando None como coringa:

    1. (S, None, None)      sujeito fixo
    2. (None, P, None)      predicado fixo
    3. (None, P, O)         predicado e objeto fixos
    4. (S, P, None)         sujeito e predicado fixos
    5. (None, P, O)         predicado e objeto fixos (outro uso: filtro por valor)
    6. (S, P, O)            os tres fixos - teste de existencia
    7. (None, None, O)      objeto fixo

Cada funcao declara, no proprio docstring, O QUE BUSCA e o RESULTADO ESPERADO.

Todas rodam sobre o grafo JA EXPANDIDO pelo reasoner, entao algumas devolvem
triplas que nao existem no arquivo .ttl (ver consulta 4).
"""

from rdflib import RDF

import util
from base import COPA


def consulta_1(g):
    """BUSCA: todas as triplas cujo sujeito e a selecao da Espanha - padrao (S, None, None).

    ESPERADO: o cartao completo da campea: rotulo, codigo FIFA, grupo, colocacao
    na chave, confederacao e - so por inferencia - os 26 jogadores do elenco.
    """
    util.consulta(
        "Parte 1", 1,
        "Tudo que a base sabe sobre a selecao da Espanha",
        "inspecionar um recurso inteiro, como um 'SELECT *' de uma entidade",
        "Padrao: (copa:selecao_ESP, None, None)",
    )
    linhas = []
    for _, p, o in g.triples((COPA.selecao_ESP, None, None)):
        linhas.append([util.curto(p), util.curto(o)])
    linhas.sort()
    util.tabela(["predicado", "objeto"], linhas, limite=12)


def consulta_2(g):
    """BUSCA: todos os estadios e suas capacidades - padrao (None, P, None).

    ESPERADO: 16 estadios, do Azteca (80.824) ao BMO Field (43.036).
    """
    util.consulta(
        "Parte 1", 2,
        "Capacidade de todos os estadios da Copa",
        "varrer uma propriedade de dados inteira, sem fixar sujeito",
        "Padrao: (None, copa:capacidade, None)",
    )
    linhas = [
        [util.rotulo(g, s), int(o)]
        for s, _, o in g.triples((None, COPA.capacidade, None))
    ]
    linhas.sort(key=lambda linha: -linha[1])
    util.tabela(["estadio", "capacidade"], [[n, f"{c:,}".replace(",", ".")] for n, c in linhas])


def consulta_3(g):
    """BUSCA: todos os recursos do tipo Goleiro - padrao (None, rdf:type, O).

    ESPERADO: os goleiros dos 8 elencos modelados (3 por selecao = 24).
    """
    util.consulta(
        "Parte 1", 3,
        "Quem sao os goleiros da base",
        "listar as instancias de uma classe folha da hierarquia de posicoes",
        "Padrao: (None, rdf:type, copa:Goleiro)",
    )
    linhas = []
    for s, _, _ in g.triples((None, RDF.type, COPA.Goleiro)):
        selecao = next(g.objects(s, COPA.jogaPor), None)
        camisa = next(g.objects(s, COPA.numeroCamisa), None)
        linhas.append([util.rotulo(g, s), util.rotulo(g, selecao) if selecao else "-",
                       util.curto(camisa)])
    linhas.sort(key=lambda linha: (linha[1], linha[2]))
    util.tabela(["goleiro", "selecao", "camisa"], linhas, limite=10)


def consulta_4(g):
    """BUSCA: o elenco da Espanha - padrao (S, P, None).

    ESPERADO: 26 jogadores. O ponto desta consulta e que NENHUMA tripla
    copa:temJogador existe no arquivo .ttl - o arquivo so tem o sentido
    jogador -> selecao (copa:jogaPor). Estes 26 resultados sao produzidos pelo
    reasoner a partir de `copa:jogaPor owl:inverseOf copa:temJogador`.
    """
    util.consulta(
        "Parte 1", 4,
        "Elenco da Espanha pela propriedade inversa",
        "mostrar que a inversa OWL responde uma pergunta que o arquivo nao contem",
        "Padrao: (copa:selecao_ESP, copa:temJogador, None)",
    )
    linhas = []
    for _, _, jogador in g.triples((COPA.selecao_ESP, COPA.temJogador, None)):
        camisa = next(g.objects(jogador, COPA.numeroCamisa), None)
        clube = next(g.objects(jogador, COPA.clubeAtual), None)
        linhas.append([int(camisa) if camisa is not None else 99,
                       util.rotulo(g, jogador), util.curto(clube)])
    linhas.sort()
    util.tabela(["camisa", "jogador", "clube"], linhas, limite=10)
    util.nota(
        "Nenhuma destas triplas esta no .ttl: todas vieram de owl:inverseOf.\n"
        "Sem o reasoner, esta consulta devolveria zero linhas."
    )


def consulta_5(g):
    """BUSCA: quais selecoes caíram no Grupo A - padrao (None, P, O).

    ESPERADO: as 4 selecoes do Grupo A - Mexico, Africa do Sul, Coreia do Sul e Chequia.
    """
    util.consulta(
        "Parte 1", 5,
        "Selecoes do Grupo A",
        "navegar uma relacao no sentido inverso fixando o objeto",
        "Padrao: (None, copa:pertenceAoGrupo, copa:grupo_A)",
    )
    linhas = []
    for s, _, _ in g.triples((None, COPA.pertenceAoGrupo, COPA.grupo_A)):
        posicao = next(g.objects(s, COPA.posicaoNoGrupo), None)
        codigo = next(g.objects(s, COPA.codigoFIFA), None)
        linhas.append([int(posicao) if posicao is not None else 9,
                       util.rotulo(g, s), util.curto(codigo)])
    linhas.sort()
    util.tabela(["colocacao", "selecao", "codigo FIFA"], linhas)


def consulta_6(g):
    """BUSCA: a Espanha foi a mandante da final? - padrao (S, P, O), tudo fixo.

    ESPERADO: True. Um padrao totalmente fechado funciona como teste de
    existencia - o equivalente, na API de triplas, ao ASK do SPARQL.
    """
    util.consulta(
        "Parte 1", 6,
        "Teste de existencia: a Espanha foi a mandante da final?",
        "verificar um fato pontual sem trazer dado nenhum de volta",
        "Padrao: (copa:partida_final_esp_arg, copa:mandante, copa:selecao_ESP)",
    )
    existe = (COPA.partida_final_esp_arg, COPA.mandante, COPA.selecao_ESP) in g
    print(f"  Resposta: {existe}")

    # contraprova com um fato falso, para mostrar que o teste discrimina
    falso = (COPA.partida_final_esp_arg, COPA.mandante, COPA.selecao_BRA) in g
    print(f"  Contraprova (o Brasil foi mandante da final?): {falso}")


def consulta_7(g):
    """BUSCA: tudo que aponta para o MetLife Stadium - padrao (None, None, O).

    ESPERADO: as partidas sediadas la (incluindo a final) via copa:sediadaEm.
    E o unico padrao que varre o grafo pelo objeto, respondendo 'quem se
    relaciona com este recurso?' sem saber por qual propriedade.
    """
    util.consulta(
        "Parte 1", 7,
        "Todo recurso que se relaciona com o MetLife Stadium",
        "descobrir as conexoes de entrada de um recurso, sem fixar a propriedade",
        "Padrao: (None, None, copa:estadio_metlife_stadium)",
    )
    linhas = []
    for s, p, _ in g.triples((None, None, COPA.estadio_metlife_stadium)):
        linhas.append([util.curto(p), util.rotulo(g, s)])
    linhas.sort()
    util.tabela(["propriedade", "recurso de origem"], linhas, limite=10)


TODAS = [consulta_1, consulta_2, consulta_3, consulta_4, consulta_5, consulta_6, consulta_7]


def executar(g):
    util.banner("PARTE 1 - CONSULTAS COM g.triples()")
    for fn in TODAS:
        fn(g)
