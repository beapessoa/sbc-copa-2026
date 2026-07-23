# Copa do Mundo FIFA 2026 — Base de Conhecimento em RDF/RDFS/OWL

Mini-Projeto 3 — **Sistemas Baseados em Conhecimento**

Modelagem de uma base de conhecimento sobre a Copa do Mundo de 2026 em Turtle (`.ttl`),
com inferência via OWL-RL e consultas em `rdflib` e SPARQL.

## Integrantes

- Beatriz Almeida
- Emyle Lucena
- Marcus Vinicius
- Maria Clara Dantas

---

## 1. Como executar

Requer Python 3.9 ou superior.

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python main.py
```

O programa carrega a base, confere na tela os requisitos mínimos do enunciado, aplica
o reasoner e executa as 17 consultas (7 com `g.triples()` e 10 em SPARQL), identificando
cada uma pelo número e pelo propósito.

A saída completa de uma execução está gravada em [`saida_exemplo.txt`](saida_exemplo.txt).

> No Windows, troque a ativação por `.venv\Scripts\activate`.

### Interface visual (extra, opcional)

Há também uma interface em Streamlit, usada para apresentar o projeto. Ela reaproveita
os mesmos módulos de consulta e não toca no `.ttl`.

```bash
pip install -r requirements-app.txt
```

```bash
streamlit run app.py
```

Seis seções: métricas da base, taxonomia, a inferência OWL demonstrada com a mesma
consulta rodando com e sem o reasoner lado a lado, as consultas da Parte 1, as da
Parte 2 e um campo para SPARQL livre.

### Arquivos

| Arquivo | Conteúdo |
|---|---|
| [`data/copa2026.ttl`](data/copa2026.ttl) | A base: T-Box (classes, propriedades, OWL) + A-Box (instâncias) |
| [`main.py`](main.py) | Orquestrador: carga, conferência dos requisitos, reasoner, consultas |
| [`base.py`](base.py) | Carga do grafo, estatísticas de conformidade e aplicação do reasoner |
| [`consultas_triples.py`](consultas_triples.py) | Parte 1 — 7 consultas com `g.triples()` |
| [`consultas_sparql.py`](consultas_sparql.py) | Parte 2 — 10 consultas SPARQL |
| [`util.py`](util.py) | Formatação da saída no terminal |
| [`app.py`](app.py) | Interface Streamlit para a apresentação |

---

## 2. Resumo da base

A base descreve a Copa do Mundo FIFA de 2026, disputada nos Estados Unidos, Canadá e
México entre 11 de junho e 19 de julho de 2026, vencida pela **Espanha**, que bateu a
**Argentina por 1 a 0 na prorrogação** no MetLife Stadium.

| Métrica | Valor | Mínimo exigido |
|---|---|---|
| Triplas no arquivo Turtle | **2.904** | 50 |
| Classes | **27** | 8 |
| Níveis abaixo da raiz | **2** | 2 |
| Propriedades de objeto | **12** | 5 |
| Propriedades de dados | **14** | 5 |
| Propriedades no total | **26** | 10 |
| Instâncias | **381** | 25 |
| Construções OWL distintas | **7** | 5 |

Após o reasoner, o grafo passa de **2.904 para 6.531 triplas**: 3.627 fatos derivados.

### Instâncias por classe

| Classe | Qtd. | Classe | Qtd. |
|---|---:|---|---:|
| Defensor | 67 | Grupo | 12 |
| MeioCampista | 63 | PartidaOitavas | 8 |
| Atacante | 54 | Tecnico | 8 |
| Selecao | 48 | Confederacao | 6 |
| Arbitro | 26 | PartidaFaseGrupos | 6 |
| Goleiro | 24 | PartidaQuartas | 4 |
| CidadeSede | 16 | Pais | 3 |
| Estadio | 16 | PartidaSemifinal | 2 |
| Partida16Avos | 16 | PartidaFinal | 1 |
| | | PartidaTerceiroLugar | 1 |

### Origem e recorte dos dados

Todos os dados são **reais**, transcritos da Wikipédia em julho de 2026:

- `2026 FIFA World Cup` — sedes, estádios e capacidades
- `2026 FIFA World Cup squads` — elencos com número, posição, nascimento e clube
- `2026 FIFA World Cup round of 32` / `knockout stage` / `final` — partidas
- `2026 FIFA World Cup Group A` — partidas da fase de grupos
- `Template:2026 FIFA World Cup group tables` — composição e classificação dos 12 grupos

Cinco dimensões entram **completas**: as 48 seleções, os 12 grupos, os 16 estádios,
as 16 cidades-sede e as 4 posições em campo. Duas são recorte:

- **Partidas (38 de 104):** todo o mata-mata — 16 jogos de 16-avos, 8 oitavas, 4 quartas,
  2 semifinais, a disputa do 3º lugar e a final — mais o Grupo A completo como amostra da
  fase de grupos. Isso popula todas as sete subclasses de `Partida`.
- **Jogadores (208 de 1.248):** os elencos oficiais completos, de 26 convocados cada, de
  8 seleções — Espanha, Argentina, Inglaterra e França (as semifinalistas) mais Brasil,
  Noruega, Marrocos e México. São as seleções que aparecem nas partidas modeladas, então
  consultas que cruzam jogador → seleção → partida devolvem resultado.

Onde a fonte não confirmava um valor, a tripla foi **omitida** em vez de estimada — é o
caso de `copa:vencedora` no empate de Chéquia 1 × 1 África do Sul, que não teve pênaltis.
É essa ausência que torna necessário o `OPTIONAL` da consulta 5.

---

## 3. Principais entidades e classes

O domínio se organiza em quatro raízes independentes.

### Pessoa

Quem participa do torneio. A posição em campo declarada pela FIFA (GK/DF/MF/FW) vira
subclasse de `Jogador`, e não atributo: "liste os goleiros" é uma consulta por tipo, e
todo `Goleiro` também é `Jogador` e `Pessoa`.

```
Pessoa
├── Jogador
│   ├── Goleiro
│   ├── Defensor
│   ├── MeioCampista
│   └── Atacante
├── Tecnico
└── Arbitro
```

### Local

Cada estádio aponta para sua cidade-sede, cada cidade para seu país. O vínculo
estádio → país **não é escrito**: vem da transitividade.

```
Local
├── Pais            (3: Estados Unidos, Canadá, México)
├── Cidade
│   └── CidadeSede  (16)
└── Estadio         (16)
```

### Partida

A fase do torneio é a classe da partida. Com 48 seleções, o mata-mata de 2026 começa nos
**16-avos**, não nas oitavas — a hierarquia espelha o formato real.

```
Partida
├── PartidaFaseGrupos
└── PartidaMataMata          (≡ PartidaEliminatoria)
    ├── Partida16Avos
    ├── PartidaOitavas
    ├── PartidaQuartas
    ├── PartidaSemifinal
    ├── PartidaTerceiroLugar
    └── PartidaFinal
```

### Entidades organizacionais

```
Selecao                Grupo (A–L)        Confederacao
└── Semifinalista                         (UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC)
```

`Semifinalista` é uma **classe derivada**, sem instância no arquivo: é povoada em execução
pela regra `INSERT ... WHERE` da consulta 8.

### Propriedades

**De objeto (12).** `jogaPor`, `temJogador`, `treina`, `pertenceAoGrupo`, `filiadaA`,
`mandante`, `visitante`, `sediadaEm`, `vencedora`, `apitou`, `localizadoEm`, `enfrentou`.

**De dados (14).** `numeroCamisa`, `dataNascimento`, `clubeAtual`, `jogosPelaSelecao`,
`golsPelaSelecao`, `paisDeOrigem`, `capacidade`, `dataPartida`, `golsMandante`,
`golsVisitante`, `publico`, `letraGrupo`, `posicaoNoGrupo`, `codigoFIFA`.

Todas as 26 declaram `rdfs:domain` e `rdfs:range`. Os rótulos usam `rdfs:label`, sem
domain: dois `rdfs:domain` na mesma propriedade significariam **interseção** de classes,
não união.

---

## 4. As 7 construções OWL e por que cada uma existe

O `main.py` demonstra o efeito de cada uma na saída.

| Construção | Onde | Justificativa no domínio |
|---|---|---|
| `owl:inverseOf` | `jogaPor` ⁻¹ `temJogador` | O arquivo escreve só o sentido jogador → seleção; o elenco de cada seleção é **inferido**. Não existe uma única tripla `temJogador` no `.ttl`. |
| `owl:TransitiveProperty` | `localizadoEm` | Estádio → cidade → país, sem repetir o vínculo com o país em cada um dos 16 estádios. |
| `owl:SymmetricProperty` | `enfrentou` | Se A enfrentou B, B enfrentou A. O CONSTRUCT da consulta 6 emite só o sentido mandante → visitante; a inversa é derivada. |
| `owl:FunctionalProperty` | `sediadaEm`, `treina`, `dataPartida`, `numeroCamisa`, `pertenceAoGrupo`, `filiadaA`, `vencedora`, entre outras | Cada uma tem no máximo um valor: uma partida ocorre em um estádio, numa data; um técnico comanda uma seleção; um jogador usa um número. |
| `owl:InverseFunctionalProperty` | `codigoFIFA` | "BRA" identifica unicamente uma seleção. É uma chave global: duas bases que usem o mesmo código falam da mesma seleção, e o reasoner deriva `owl:sameAs`. |
| `owl:disjointWith` | 9 pares entre as posições, `Jogador`, `Tecnico` e `Arbitro` | Ninguém é goleiro e atacante, nem jogador e árbitro da mesma competição. Torna esse erro **detectável**, o que RDFS sozinho não expressa. |
| `owl:equivalentClass` | `PartidaMataMata` ≡ `PartidaEliminatoria` | Os dois termos circulam na imprensa e nos documentos da FIFA. A equivalência integra uma base que use o outro nome sem reescrever dado. |

### A prova de que a inferência funciona

O programa executa a mesma consulta antes e depois do reasoner:

```
ANTES do reasoner:       copa:selecao_ESP copa:temJogador ?j  ->  0 resultado(s)
DEPOIS do reasoner:      copa:selecao_ESP copa:temJogador ?j  ->  26 resultado(s)
```

De 0 para 26 sem nenhuma mudança no arquivo.

---

## 5. As consultas

### Parte 1 — `g.triples()` (7 consultas)

Cobrem as combinações do padrão (sujeito, predicado, objeto) com `None` como coringa.
Cada função declara no docstring **o que busca** e o **resultado esperado**.

| # | Padrão | Pergunta |
|---|---|---|
| 1 | `(S, None, None)` | Tudo que a base sabe sobre a Espanha |
| 2 | `(None, P, None)` | Capacidade de todos os estádios |
| 3 | `(None, rdf:type, O)` | Quem são os goleiros da base |
| 4 | `(S, P, None)` | Elenco da Espanha — **só existe por inferência** |
| 5 | `(None, P, O)` | Seleções do Grupo A |
| 6 | `(S, P, O)` | Teste de existência: a Espanha foi mandante da final? |
| 7 | `(None, None, O)` | Tudo que se relaciona com o MetLife Stadium |

### Parte 2 — SPARQL (10 consultas)

| # | Forma | Pergunta |
|---|---|---|
| 1 | SELECT | Elenco da Argentina com posição vinda da hierarquia de classes |
| 2 | SELECT + **FILTER**, FILTER NOT EXISTS | Estádios grandes fora dos Estados Unidos |
| 3 | SELECT + **ORDER BY** + caminho de propriedade | Caminho da Espanha até o título, em ordem cronológica |
| 4 | SELECT + **GROUP BY / SUM / COUNT / HAVING** | Artilharia por seleção |
| 5 | SELECT + **OPTIONAL** | Partidas do Grupo A e quem venceu — inclusive o empate |
| 6 | **CONSTRUCT** | Grafo derivado de confrontos entre seleções |
| 7 | **ASK** | A Argentina enfrentou a Espanha? (a simetria responde) |
| 8 | **INSERT ... WHERE** | Classificar automaticamente as semifinalistas |
| 9 | **DELETE ... WHERE** | Cortar um jogador do elenco |
| 10 | **DELETE/INSERT ... WHERE** | Trocar o técnico de uma seleção |

As três consultas de UPDATE imprimem o estado **antes e depois**. Atuam somente sobre o
grafo em memória: `data/copa2026.ttl` não é modificado, e reexecutar o programa produz a
mesma saída.

As operações das consultas 9 e 10 são **hipotéticas**, criadas para demonstrar as formas de
`UPDATE`; não descrevem eventos do torneio.

---

## 6. Duas observações de modelagem

**Inferência materializada não se retrai sozinha.** A consulta 9 apaga as duas direções da
convocação: `temJogador` foi gravada pelo reasoner, e remover só o `jogaPor` que a originou
deixaria a inferência órfã.

**Depois do reasoner, `rdfs:subClassOf` é reflexiva.** Na consulta 1 da Parte 2,
`?posicaoClasse rdfs:subClassOf copa:Jogador` casa com `copa:Jogador` consigo mesma e
duplicaria cada jogador — daí o `FILTER (?posicaoClasse != copa:Jogador)`.
