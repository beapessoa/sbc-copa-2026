"""Parte 1 - Consultas com g.triples(), a API de padroes de tripla do rdflib.

Sete consultas cobrindo as combinacoes do padrao (sujeito, predicado, objeto),
com None como coringa. Rodam sobre o grafo ja expandido pelo reasoner.
"""

from rdflib import RDF

import util
from base import COPA


def consulta_1(g):
    """Padrao (S, None, None).

    Busca: todas as triplas cujo sujeito e a selecao da Espanha.
    Esperado: rotulo, codigo FIFA, grupo, colocacao, confederacao e os 26
    jogadores do elenco (estes ultimos vindos da inferencia).
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
    """Padrao (None, P, None).

    Busca: todos os estadios e suas capacidades.
    Esperado: 16 estadios, do Azteca (80.824) ao BMO Field (43.036).
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
    """Padrao (None, rdf:type, O).

    Busca: os recursos do tipo Goleiro.
    Esperado: 24 goleiros, 3 em cada um dos 8 elencos modelados.
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
    """Padrao (S, P, None).

    Busca: o elenco da Espanha por copa:temJogador.
    Esperado: 26 jogadores, todos inferidos - o arquivo so tem o sentido
    copa:jogaPor, e a inversa e derivada pelo reasoner.
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
    util.nota("Sem o reasoner, esta consulta devolveria zero linhas.")


def consulta_5(g):
    """Padrao (None, P, O).

    Busca: as selecoes sorteadas no Grupo A.
    Esperado: Mexico, Africa do Sul, Coreia do Sul e Chequia, nessa ordem.
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
    """Padrao (S, P, O), sem coringa.

    Busca: se a Espanha e a equipe A da final.
    Esperado: True. Com os tres termos fixos o padrao vira teste de existencia.
    """
    util.consulta(
        "Parte 1", 6,
        "Teste de existencia: a Espanha e a equipe A da final?",
        "verificar um fato pontual sem trazer dado nenhum de volta",
        "Padrao: (copa:partida_final_esp_arg, copa:equipeA, copa:selecao_ESP)",
    )
    existe = (COPA.partida_final_esp_arg, COPA.equipeA, COPA.selecao_ESP) in g
    print(f"  Resposta: {existe}")

    falso = (COPA.partida_final_esp_arg, COPA.equipeA, COPA.selecao_BRA) in g
    print(f"  Contraprova (o Brasil e a equipe A da final?): {falso}")


def consulta_7(g):
    """Padrao (None, None, O).

    Busca: tudo que aponta para o MetLife Stadium, qualquer que seja a propriedade.
    Esperado: as partidas sediadas la, entre elas a final.
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
