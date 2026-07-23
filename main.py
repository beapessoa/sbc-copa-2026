"""Mini-Projeto 3 - Base de conhecimento da Copa do Mundo FIFA de 2026.

Carrega data/copa2026.ttl, confere os requisitos minimos, aplica o reasoner
OWL-RL e executa as duas partes de consultas.

    python main.py
"""

import sys

from rdflib import RDF

import base
import consultas_sparql
import consultas_triples
import util


def sonda_inferencia(g, momento):
    """Elenco da Espanha por copa:temJogador, que nao tem tripla no arquivo."""
    q = """
    PREFIX copa: <http://ufpb.br/sbc/copa2026#>
    SELECT (COUNT(?j) AS ?n) WHERE { copa:selecao_ESP copa:temJogador ?j }
    """
    n = int(list(g.query(q))[0][0])
    print(f"  {momento:<24} copa:selecao_ESP copa:temJogador ?j  ->  {n} resultado(s)")
    return n


def consistencia(inconsistencias):
    """Mostra que as construcoes de disjuncao sao verificadas de fato.

    Primeiro reporta o resultado sobre a base real. Depois repete o reasoner
    sobre uma copia com um erro plantado de proposito, para provar que a
    verificacao acusa quando ha o que acusar.
    """
    util.banner("VERIFICACAO DE CONSISTENCIA")
    print(f"  Base real: {len(inconsistencias)} inconsistencia(s) encontrada(s).")
    for msg in inconsistencias:
        print(f"    - {msg}")
    print()

    from rdflib import Graph
    from base import COPA

    suja = Graph()
    for tripla in base.carregar():
        suja.add(tripla)
    # a Espanha ja e a equipe A da final; declara-la tambem como equipe B viola
    # copa:equipeA owl:propertyDisjointWith copa:equipeB
    suja.add((COPA.partida_final_esp_arg, COPA.equipeB, COPA.selecao_ESP))
    # e o goleiro Unai Simon como atacante viola copa:Goleiro owl:disjointWith
    # copa:Atacante
    suja.add((COPA.jogador_unai_simon, RDF.type, COPA.Atacante))

    _, _, erros = base.aplicar_reasoner(suja)
    print("  Copia com dois erros plantados de proposito:")
    print(f"  {len(erros)} inconsistencia(s) encontrada(s).")
    # ordenado: o owlrl coleta os erros na ordem em que percorre o grafo, que
    # nao e estavel entre execucoes
    for msg in sorted(str(m) for m in erros):
        print(f"    - {msg}")

    print()
    if not inconsistencias and erros:
        util.nota(
            "A base passa e a copia adulterada e reprovada: owl:disjointWith e\n"
            "owl:propertyDisjointWith estao sendo checados, nao apenas declarados."
        )
        return True
    util.nota("ATENCAO: a verificacao de consistencia nao se comportou como esperado.")
    return False


def main():
    util.banner("MINI-PROJETO 3 - COPA DO MUNDO FIFA 2026")
    print("  Base de conhecimento em RDF/RDFS/OWL consultada com rdflib e SPARQL.")
    print(f"  Arquivo: {base.ARQUIVO}")

    # ---------------------------------------------------------------- #
    # 1. Carga
    # ---------------------------------------------------------------- #
    try:
        g = base.carregar()
    except Exception as erro:
        print(f"\nERRO ao carregar a base: {erro}")
        return 1
    print(f"  Carregado sem erros: {len(g)} triplas.")

    # ---------------------------------------------------------------- #
    # 2. Conferencia dos requisitos
    # ---------------------------------------------------------------- #
    tudo_ok = base.estatisticas(g)

    # ---------------------------------------------------------------- #
    # 3. Reasoner
    # ---------------------------------------------------------------- #
    util.banner("REASONER OWL-RL")
    print("  Sonda: uma consulta que o arquivo .ttl, sozinho, nao responde.")
    print()
    antes_sonda = sonda_inferencia(g, "ANTES do reasoner:")

    antes, depois, inconsistencias = base.aplicar_reasoner(g)
    print()
    print(f"  Triplas: {antes} -> {depois}  (+{depois - antes} inferidas)")
    print()

    depois_sonda = sonda_inferencia(g, "DEPOIS do reasoner:")
    print()
    if antes_sonda == 0 and depois_sonda > 0:
        util.nota(
            f"De 0 para {depois_sonda}: owl:inverseOf derivou o elenco inteiro sem\n"
            "nenhuma tripla copa:temJogador escrita no arquivo."
        )
    else:
        util.nota("ATENCAO: a sonda de inferencia nao se comportou como esperado.")
        tudo_ok = False

    tudo_ok = consistencia(inconsistencias) and tudo_ok

    # ---------------------------------------------------------------- #
    # 4. Consultas
    # ---------------------------------------------------------------- #
    consultas_triples.executar(g)
    consultas_sparql.executar(g)

    # ---------------------------------------------------------------- #
    # 5. Fecho
    # ---------------------------------------------------------------- #
    util.banner("FIM")
    print(f"  Parte 1: {len(consultas_triples.TODAS)} consultas com g.triples()")
    print(f"  Parte 2: {len(consultas_sparql.TODAS)} consultas SPARQL "
          "(SELECT, CONSTRUCT, ASK, INSERT, DELETE, DELETE/INSERT)")
    print(f"  Requisitos minimos: {'TODOS ATENDIDOS' if tudo_ok else 'HA FALHAS ACIMA'}")
    print()
    print("  data/copa2026.ttl nao foi modificado: os tres UPDATE atuaram apenas")
    print("  sobre o grafo em memoria.")
    print()
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
