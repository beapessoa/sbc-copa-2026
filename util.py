"""Formatacao da saida no terminal."""

from rdflib import Literal, URIRef
from rdflib.namespace import RDFS

LARGURA = 92


def banner(texto):
    """Cabecalho das grandes etapas do programa."""
    print()
    print("=" * LARGURA)
    print(texto.center(LARGURA))
    print("=" * LARGURA)


def secao(texto):
    print()
    print("-" * LARGURA)
    print(texto)
    print("-" * LARGURA)


def consulta(parte, numero, titulo, proposito, detalhe=None):
    """Cabecalho de uma consulta: numero, titulo e proposito."""
    print()
    print(f"[{parte} | Consulta {numero}] {titulo}")
    print(f"  Proposito: {proposito}")
    if detalhe:
        print(f"  {detalhe}")
    print()


def nota(texto):
    for linha in texto.strip().split("\n"):
        print(f"  >> {linha.strip()}")


def curto(termo):
    """Encolhe URIs e literais para caber no terminal."""
    if isinstance(termo, URIRef):
        s = str(termo)
        for sep in ("#", "/"):
            if sep in s:
                s = s.rsplit(sep, 1)[-1]
        return s
    if isinstance(termo, Literal):
        return str(termo)
    if termo is None:
        return "-"
    return str(termo)


def rotulo(g, recurso):
    """rdfs:label do recurso, ou o nome curto da URI se nao houver."""
    for r in g.objects(recurso, RDFS.label):
        return str(r)
    return curto(recurso)


def tabela(cabecalhos, linhas, limite=None):
    """Tabela alinhada. `limite` corta a exibicao e avisa quanto sobrou."""
    linhas = [[("-" if c is None else str(c)) for c in linha] for linha in linhas]
    total = len(linhas)
    cortadas = 0
    if limite is not None and total > limite:
        cortadas = total - limite
        linhas = linhas[:limite]

    if not linhas:
        print("  (nenhum resultado)")
        return

    larguras = [len(h) for h in cabecalhos]
    for linha in linhas:
        for i, celula in enumerate(linha):
            larguras[i] = max(larguras[i], len(celula))

    def formata(celulas):
        return "  " + " | ".join(c.ljust(larguras[i]) for i, c in enumerate(celulas)).rstrip()

    print(formata(cabecalhos))
    print("  " + "-+-".join("-" * w for w in larguras))
    for linha in linhas:
        print(formata(linha))

    if cortadas:
        print(f"  ... (+{cortadas} linhas; total de {total})")
    else:
        print(f"  ({total} linha{'s' if total != 1 else ''})")


def checagem(descricao, valor, minimo=None, esperado=None):
    """Verificacao de requisito com OK/FALHA. Devolve o booleano."""
    if minimo is not None:
        ok = valor >= minimo
        alvo = f"minimo {minimo}"
    else:
        ok = valor == esperado
        alvo = f"esperado {esperado}"
    marca = "OK  " if ok else "FALHA"
    print(f"  [{marca}] {descricao:<46} {valor:>6}   ({alvo})")
    return ok
