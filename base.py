"""Carga da base, estatisticas de conformidade e aplicacao do reasoner."""

import os
from collections import defaultdict

from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF, RDFS

import util

COPA = Namespace("http://ufpb.br/sbc/copa2026#")
ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "copa2026.ttl")


def carregar(caminho=ARQUIVO):
    """Le o Turtle e devolve o grafo."""
    g = Graph()
    g.parse(caminho, format="turtle")
    g.bind("copa", COPA)
    return g


def _classes(g):
    return {c for c in g.subjects(RDF.type, OWL.Class) if str(c).startswith(str(COPA))}


def _instancias_de(g, classe):
    """Instancias da classe e de todas as subclasses, diretas ou nao.

    A hierarquia e fechada na mao: estas checagens rodam antes do reasoner.
    """
    subclasses = set(g.transitive_subjects(RDFS.subClassOf, classe))
    return {s for s, o in g.subject_objects(RDF.type) if o in subclasses}


def _profundidade_maxima(g):
    """Maior numero de niveis abaixo de uma raiz em rdfs:subClassOf."""
    classes = _classes(g)
    pais = defaultdict(set)
    for filho, _, pai in g.triples((None, RDFS.subClassOf, None)):
        if filho in classes and pai in classes and filho != pai:
            pais[filho].add(pai)

    def profundidade(c, visitados=frozenset()):
        if c in visitados or not pais[c]:
            return 0
        return 1 + max(profundidade(p, visitados | {c}) for p in pais[c])

    return max((profundidade(c) for c in classes), default=0)


def estatisticas(g):
    """Imprime o cumprimento de cada minimo do enunciado. True se todos passaram."""
    util.banner("CONFERENCIA DOS REQUISITOS MINIMOS DA BASE")

    classes = _classes(g)
    obj_props = {p for p in g.subjects(RDF.type, OWL.ObjectProperty)}
    dat_props = {p for p in g.subjects(RDF.type, OWL.DatatypeProperty)}
    todas_props = obj_props | dat_props

    instancias = {s for s, o in g.subject_objects(RDF.type) if o in classes}

    com_domain = {p for p in todas_props if (p, RDFS.domain, None) in g}
    com_range = {p for p in todas_props if (p, RDFS.range, None) in g}

    construcoes_owl = {
        "owl:inverseOf": len(set(g.triples((None, OWL.inverseOf, None)))),
        "owl:TransitiveProperty": len(set(g.subjects(RDF.type, OWL.TransitiveProperty))),
        "owl:SymmetricProperty": len(set(g.subjects(RDF.type, OWL.SymmetricProperty))),
        "owl:FunctionalProperty": len(set(g.subjects(RDF.type, OWL.FunctionalProperty))),
        "owl:InverseFunctionalProperty": len(
            set(g.subjects(RDF.type, OWL.InverseFunctionalProperty))
        ),
        "owl:disjointWith": len(set(g.triples((None, OWL.disjointWith, None)))),
        "owl:equivalentClass": len(set(g.triples((None, OWL.equivalentClass, None)))),
    }
    usadas = sum(1 for n in construcoes_owl.values() if n > 0)

    print("  Requisitos do enunciado:")
    ok = [
        util.checagem("Classes em hierarquia", len(classes), minimo=8),
        util.checagem("Niveis abaixo da raiz (rdfs:subClassOf)", _profundidade_maxima(g), minimo=2),
        util.checagem("Propriedades de objeto", len(obj_props), minimo=5),
        util.checagem("Propriedades de dados", len(dat_props), minimo=5),
        util.checagem("Propriedades no total", len(todas_props), minimo=10),
        util.checagem("Propriedades com rdfs:domain", len(com_domain), esperado=len(todas_props)),
        util.checagem("Propriedades com rdfs:range", len(com_range), esperado=len(todas_props)),
        util.checagem("Instancias", len(instancias), minimo=25),
        util.checagem("Triplas no arquivo Turtle", len(g), minimo=50),
        util.checagem("Construcoes OWL distintas", usadas, minimo=5),
    ]

    print()
    print("  Construcoes OWL declaradas:")
    for nome, quantidade in construcoes_owl.items():
        print(f"    - {nome:<32} {quantidade:>3} ocorrencia(s)")

    print()
    print("  Instancias por classe (contagem direta, sem inferencia):")
    contagem = defaultdict(int)
    for s, o in g.subject_objects(RDF.type):
        if o in classes:
            contagem[util.curto(o)] += 1
    for nome, quantidade in sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    - {nome:<24} {quantidade:>4}")

    ok.extend(_integridade(g))
    return all(ok)


def _integridade(g):
    """Checagens de integridade dos dados transcritos da fonte."""
    print()
    print("  Integridade dos dados transcritos:")
    resultados = []

    elencos = defaultdict(list)
    for jogador, selecao in g.subject_objects(COPA.jogaPor):
        elencos[selecao].append(jogador)

    resultados.append(util.checagem("Selecoes com elenco modelado", len(elencos), esperado=8))

    tamanhos_ok = all(len(js) == 26 for js in elencos.values())
    print(f"  [{'OK  ' if tamanhos_ok else 'FALHA'}] "
          f"{'Todos os elencos com 26 convocados':<46} "
          f"{min((len(j) for j in elencos.values()), default=0):>6}   (esperado 26)")
    resultados.append(tamanhos_ok)

    camisas_ok = True
    for selecao, jogadores in elencos.items():
        numeros = [int(n) for j in jogadores for n in g.objects(j, COPA.numeroCamisa)]
        if len(set(numeros)) != len(numeros):
            camisas_ok = False
            print(f"       numeros repetidos em {util.rotulo(g, selecao)}")
    print(f"  [{'OK  ' if camisas_ok else 'FALHA'}] "
          f"{'Numero de camisa unico dentro de cada elenco':<46} {'-':>6}")
    resultados.append(camisas_ok)

    partidas = _instancias_de(g, COPA.Partida)
    resultados.append(util.checagem("Partidas modeladas", len(partidas), esperado=38))

    mata_mata = _instancias_de(g, COPA.PartidaMataMata)
    resultados.append(util.checagem("Partidas de mata-mata", len(mata_mata), esperado=32))

    return resultados


def aplicar_reasoner(g):
    """Materializa as inferencias RDFS + OWL-RL no proprio grafo."""
    from owlrl import DeductiveClosure, OWLRL_Semantics

    antes = len(g)
    DeductiveClosure(OWLRL_Semantics).expand(g)
    return antes, len(g)
