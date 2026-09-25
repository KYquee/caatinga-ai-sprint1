"""
teste_escala.py - Parte 2.4: aumenta n (12 -> 40 -> 100 -> ...) até que
BFS, DFS ou UCS falhem por estouro de memória, estouro de pilha ou tempo > 60s.

Uso: python src/teste_escala.py <matricula>
"""
import sys
import time
import tracemalloc

from gerador_pomar import gerar_pomar
from buscas import bfs, dfs, ucs, dfs_recursiva

LIMITE_TEMPO_S = 60


def com_limite_de_tempo(func, *args, limite=LIMITE_TEMPO_S):
    t0 = time.perf_counter()
    try:
        resultado = func(*args)
    except MemoryError:
        return "MemoryError", time.perf_counter() - t0
    except RecursionError:
        return "RecursionError", time.perf_counter() - t0
    dt = time.perf_counter() - t0
    if dt > limite:
        return "TIMEOUT", dt
    return "OK", dt


def pico_memoria_mb():
    # tracemalloc funciona em Windows/Linux/Mac (ao contrário de `resource`,
    # que é exclusivo de sistemas Unix e não existe no Windows).
    _atual, pico = tracemalloc.get_traced_memory()
    return pico / (1024 * 1024)


def main(matricula):
    tracemalloc.start()
    tamanhos = [12, 40, 100, 200, 400, 700, 1000, 1500]
    print(f"{'n':>6} {'estados':>10} {'BFS':>18} {'DFS(iter)':>18} "
          f"{'DFS(recurs)':>18} {'UCS':>18}")

    falhou = {}
    for n in tamanhos:
        if set(falhou) == {"BFS", "DFS(iter)", "DFS(recurs)", "UCS"}:
            break
        grade = gerar_pomar(matricula, n)
        estados = n * n
        linha = [f"{n:>6}", f"{estados:>10}"]

        for nome, func in [("BFS", bfs), ("DFS(iter)", dfs)]:
            if nome in falhou:
                linha.append(f"{'(já falhou)':>18}")
                continue
            status, dt = com_limite_de_tempo(func, grade)
            if status != "OK":
                falhou[nome] = (n, status, dt)
            linha.append(f"{status} {dt*1000:.0f}ms".rjust(18))

        # DFS recursiva - a que realmente demonstra estouro de pilha
        if "DFS(recurs)" not in falhou:
            t0 = time.perf_counter()
            status_r, resultado_r, _nos = dfs_recursiva(grade)
            dt_r = time.perf_counter() - t0
            if status_r != "OK" or dt_r > LIMITE_TEMPO_S:
                falhou["DFS(recurs)"] = (n, status_r, dt_r)
            linha.append(f"{status_r} {dt_r*1000:.0f}ms".rjust(18))
        else:
            linha.append(f"{'(já falhou)':>18}")

        if "UCS" in falhou:
            linha.append(f"{'(já falhou)':>18}")
        else:
            status, dt = com_limite_de_tempo(ucs, grade)
            if status != "OK":
                falhou["UCS"] = (n, status, dt)
            linha.append(f"{status} {dt*1000:.0f}ms".rjust(18))

        print(" ".join(linha))
        print(f"       pico de memoria do processo ate agora: {pico_memoria_mb():.1f} MB")

    print("\n=== Resumo das falhas ===")
    for nome, (n, status, dt) in falhou.items():
        print(f"{nome}: falhou em n={n} (estados={n*n}) com {status} após {dt*1000:.0f} ms")
    if not falhou:
        print("Nenhuma estratégia falhou nos tamanhos testados - aumente `tamanhos` "
              "na lista acima até observar uma falha.")


if __name__ == "__main__":
    m = int(sys.argv[1]) if len(sys.argv) > 1 else 20231045
    main(m)