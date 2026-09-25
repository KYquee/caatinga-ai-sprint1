"""
buscas.py -  BFS, DFS (iterativa e recursiva) e UCS sobre a grade do pomar.

Convenções fixas para todo o projeto (declaradas também no README):
- Estado = coordenada (i, j) da grade (linha, coluna).
- Ordem de expansão dos vizinhos: NORTE, SUL, OESTE, LESTE.
    Norte = (i-1, j) | Sul = (i+1, j) | Oeste = (i, j-1) | Leste = (i, j+1)
- Custo de entrar num talhão: 1 para '.', 4 para '~'. '#' é intransponível.
- O talhão inicial NÃO é contado no custo do caminho.
- Teste de objetivo é feito na EXPANSÃO (quando o nó sai da fronteira),
  nunca na geração/inserção. Isso é o que a UCS precisa para garantir
  otimalidade quando o primeiro nó gerado para um estado não é o mais barato.
- UCS REABRE nós: se um caminho mais barato para um estado já visitado
  aparece, ele substitui o custo antigo e o nó volta para a fronteira.
"""

import heapq
import itertools
from collections import deque

CUSTO = {".": 1, "~": 4}
BLOQUEADO = "#"

# Ordem fixa: Norte, Sul, Oeste, Leste
VIZINHOS_ORDEM = [(-1, 0, "N"), (1, 0, "S"), (0, -1, "O"), (0, 1, "L")]


class ResultadoBusca:
    def __init__(self, encontrado, caminho, custo, passos, nos_expandidos,
                 fronteira_max, tempo_ms):
        self.encontrado = encontrado
        self.caminho = caminho              # lista de (i,j) do início ao fim
        self.custo = custo                  # soma dos custos de entrada
        self.passos = passos                # nº de movimentos (len(caminho)-1)
        self.nos_expandidos = nos_expandidos
        self.fronteira_max = fronteira_max
        self.tempo_ms = tempo_ms

    def as_row(self, nome):
        return {
            "estrategia": nome,
            "custo": self.custo,
            "passos": self.passos,
            "nos_expandidos": self.nos_expandidos,
            "fronteira_max": self.fronteira_max,
            "tempo_ms": round(self.tempo_ms, 3),
        }


def _vizinhos(grade, n, i, j):
    """Gera vizinhos válidos (não bloqueados, dentro da grade) na ordem N,S,O,L."""
    for di, dj, _rot in VIZINHOS_ORDEM:
        ni, nj = i + di, j + dj
        if 0 <= ni < n and 0 <= nj < n and grade[ni][nj] != BLOQUEADO:
            yield (ni, nj)


def _reconstruir_caminho(veio_de, alvo):
    caminho = [alvo]
    while caminho[-1] in veio_de:
        caminho.append(veio_de[caminho[-1]])
    caminho.reverse()
    return caminho


def bfs(grade, inicio=(0, 0), objetivo=None):
    """BFS: expande por nº de passos (não usa custo). Não garante custo ótimo
    quando os passos têm custos diferentes (só garante nº mínimo de passos)."""
    import time
    t0 = time.perf_counter()
    n = len(grade)
    if objetivo is None:
        objetivo = (n - 1, n - 1)

    fronteira = deque([inicio])
    visitados = {inicio}
    veio_de = {}
    nos_expandidos = 0
    fronteira_max = 1

    while fronteira:
        fronteira_max = max(fronteira_max, len(fronteira))
        atual = fronteira.popleft()
        nos_expandidos += 1
        if atual == objetivo:  # teste de objetivo na expansão
            caminho = _reconstruir_caminho(veio_de, atual)
            custo = sum(CUSTO[grade[i][j]] for (i, j) in caminho[1:])
            t1 = time.perf_counter()
            return ResultadoBusca(True, caminho, custo, len(caminho) - 1,
                                   nos_expandidos, fronteira_max, (t1 - t0) * 1000)
        for viz in _vizinhos(grade, n, *atual):
            if viz not in visitados:
                visitados.add(viz)
                veio_de[viz] = atual
                fronteira.append(viz)

    t1 = time.perf_counter()
    return ResultadoBusca(False, [], None, None, nos_expandidos, fronteira_max,
                           (t1 - t0) * 1000)


def dfs(grade, inicio=(0, 0), objetivo=None):
    """DFS iterativa com pilha, grafo (visitados) para não entrar em loop
    infinito nos ciclos da grade. Não é completa/ótima em custo nem em passos
    de forma garantida - é usada aqui como busca em grafo com visitados,
    então termina, mas a rota pode ser bem mais cara que a ótima."""
    import time
    t0 = time.perf_counter()
    n = len(grade)
    if objetivo is None:
        objetivo = (n - 1, n - 1)

    # Empilhamos em ordem inversa (L,O,S,N) para que N seja desempilhado primeiro,
    # respeitando a ordem declarada N,S,O,L.
    pilha = [inicio]
    visitados = {inicio}
    veio_de = {}
    nos_expandidos = 0
    fronteira_max = 1

    while pilha:
        fronteira_max = max(fronteira_max, len(pilha))
        atual = pilha.pop()
        nos_expandidos += 1
        if atual == objetivo:
            caminho = _reconstruir_caminho(veio_de, atual)
            custo = sum(CUSTO[grade[i][j]] for (i, j) in caminho[1:])
            t1 = time.perf_counter()
            return ResultadoBusca(True, caminho, custo, len(caminho) - 1,
                                   nos_expandidos, fronteira_max, (t1 - t0) * 1000)
        vizinhos = list(_vizinhos(grade, n, *atual))
        for viz in reversed(vizinhos):  # inverso p/ desempilhar na ordem N,S,O,L
            if viz not in visitados:
                visitados.add(viz)
                veio_de[viz] = atual
                pilha.append(viz)

    t1 = time.perf_counter()
    return ResultadoBusca(False, [], None, None, nos_expandidos, fronteira_max,
                           (t1 - t0) * 1000)


def ucs(grade, inicio=(0, 0), objetivo=None):
    """Busca de custo uniforme com fila de prioridade, reabertura de nós
    (decrease-key via reinserção) e teste de objetivo na expansão."""
    import time
    t0 = time.perf_counter()
    n = len(grade)
    if objetivo is None:
        objetivo = (n - 1, n - 1)

    contador = itertools.count()  # desempate estável (ordem de inserção)
    fronteira = [(0, next(contador), inicio)]
    custo_ate = {inicio: 0}
    veio_de = {}
    fechados = set()
    nos_expandidos = 0
    fronteira_max = 1

    while fronteira:
        fronteira_max = max(fronteira_max, len(fronteira))
        custo_atual, _, atual = heapq.heappop(fronteira)
        if atual in fechados:
            continue  # entrada obsoleta (nó já expandido com custo melhor)
        fechados.add(atual)
        nos_expandidos += 1
        if atual == objetivo:
            caminho = _reconstruir_caminho(veio_de, atual)
            t1 = time.perf_counter()
            return ResultadoBusca(True, caminho, custo_atual, len(caminho) - 1,
                                   nos_expandidos, fronteira_max, (t1 - t0) * 1000)
        for viz in _vizinhos(grade, n, *atual):
            novo_custo = custo_atual + CUSTO[grade[viz[0]][viz[1]]]
            if viz not in custo_ate or novo_custo < custo_ate[viz]:
                custo_ate[viz] = novo_custo
                veio_de[viz] = atual
                heapq.heappush(fronteira, (novo_custo, next(contador), viz))

    t1 = time.perf_counter()
    return ResultadoBusca(False, [], None, None, nos_expandidos, fronteira_max,
                           (t1 - t0) * 1000)


def dfs_recursiva(grade, inicio=(0, 0), objetivo=None):
    """Versão RECURSIVA da DFS (chamada de função por estado visitado), usada
    especificamente na Parte 2.4 para observar estouro de pilha (RecursionError)
    em grades grandes. A versão principal do projeto (usada nas Partes 2.2/2.3)
    é a `dfs` iterativa acima, que não sofre desse limite - a recursiva existe
    só para demonstrar o fenômeno pedido no enunciado."""
    import sys
    import time
    t0 = time.perf_counter()
    n = len(grade)
    if objetivo is None:
        objetivo = (n - 1, n - 1)

    visitados = {inicio}
    veio_de = {}
    contadores = {"nos_expandidos": 0, "fronteira_max": 1}

    def visitar(atual, profundidade_pilha):
        contadores["fronteira_max"] = max(contadores["fronteira_max"], profundidade_pilha)
        contadores["nos_expandidos"] += 1
        if atual == objetivo:
            return True
        for viz in _vizinhos(grade, n, *atual):
            if viz not in visitados:
                visitados.add(viz)
                veio_de[viz] = atual
                if visitar(viz, profundidade_pilha + 1):  # <- chamada recursiva
                    return True
        return False

    try:
        encontrado = visitar(inicio, 1)
    except RecursionError:
        t1 = time.perf_counter()
        return "RecursionError", (t1 - t0) * 1000, contadores["nos_expandidos"]

    t1 = time.perf_counter()
    if encontrado:
        caminho = _reconstruir_caminho(veio_de, objetivo)
        custo = sum(CUSTO[grade[i][j]] for (i, j) in caminho[1:])
        r = ResultadoBusca(True, caminho, custo, len(caminho) - 1,
                            contadores["nos_expandidos"], contadores["fronteira_max"],
                            (t1 - t0) * 1000)
        return "OK", r, contadores["nos_expandidos"]
    return "NAO_ENCONTRADO", None, contadores["nos_expandidos"]


if __name__ == "__main__":
    import sys
    from gerador_pomar import gerar_pomar

    m = int(sys.argv[1]) if len(sys.argv) > 1 else 20231045
    grade = gerar_pomar(m)

    r_bfs = bfs(grade)
    r_dfs = dfs(grade)
    r_ucs = ucs(grade)

    print(f"Matricula: {m}")
    print(f"{'Estrategia':12} {'Custo':>6} {'Passos':>7} {'NosExp':>7} {'FrontMax':>9}")
    for nome, r in [("BFS", r_bfs), ("DFS", r_dfs), ("UCS", r_ucs)]:
        print(f"{nome:12} {r.custo:>6} {r.passos:>7} {r.nos_expandidos:>7} {r.fronteira_max:>9}")