"""
busca_local.py - Parte 3.4: Subida de Encosta (Hill Climbing) e
Têmpera Simulada (Simulated Annealing) para seleção de K=15 talhões
a serem inspecionados pelo Caatinga.AI sob restrição de bateria (6 horas).

Uso: python src/busca_local.py <matricula>
"""
import math
import random
import statistics
import sys
import time

from gerador_pomar import gerar_pomar


class ProblemaInspecaoTalhoes:
    """Modela a seleção de K talhões como problema de busca local.

    - Estado: subconjunto S de K talhões livres da grade (|S| = K).
    - Vizinhança: qualquer subconjunto obtido pela substituição de 1 talhão
      em S por 1 talhão livre fora de S (1-swap).
    - Função Objetivo f(S): maximiza o risco fitossanitário inspecionado
      com bônus de contiguidade epidemiológica e penalidade de dispersão
      (para respeitar o limite de 6h de bateria de deslocamento).
    """

    def __init__(self, grade, k=15):
        self.grade = grade
        self.n = len(grade)
        self.k = k
        self.livres = [
            (i, j)
            for i in range(self.n)
            for j in range(self.n)
            if self.grade[i][j] != "#"
        ]
        if len(self.livres) < k:
            raise ValueError(f"Pomar possui apenas {len(self.livres)} células livres, menor que K={k}")

    def estado_inicial_aleatorio(self, rng):
        return set(rng.sample(self.livres, self.k))

    def funcao_objetivo(self, estado):
        """Avalia a qualidade do subconjunto de talhões escolhido:
        1. Risco fitossanitário base: talhão encharcado '~' tem risco 10.0 (alto risco
           de fungos radiculares como Ceratocystis fimbriata); '.' tem risco 3.0.
        2. Bônus de contiguidade: +1.0 por par ordenado vizinho (+2.0 por aresta ortogonal),
           pois pragas e fungos formam focos e manchas contíguas no pomar.
        3. Penalidade por dispersão espacial: penaliza a distância Manhattan ao centroide,
           simulando o gasto energético de deslocamento sob a restrição de 6h de bateria.
        """
        score = 0.0
        s_set = set(estado)

        # 1. Risco base dos talhões inspecionados
        for (i, j) in estado:
            score += 10.0 if self.grade[i][j] == "~" else 3.0

        # 2. Bônus de agrupamento / foco
        for (i, j) in estado:
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (i + di, j + dj) in s_set:
                    score += 1.0

        # 3. Penalidade de dispersão (distância Manhattan média ao centroide)
        ci = sum(i for i, j in estado) / self.k
        cj = sum(j for i, j in estado) / self.k
        dispersao = sum(abs(i - ci) + abs(j - cj) for i, j in estado)
        score -= 0.5 * dispersao

        return round(score, 2)


def subida_de_encosta(problema, rng, max_passos=100):
    """Subida de Encosta (Steepest Ascent Hill Climbing).
    Avalia a vizinhança de 1-swap e aceita estritamente o melhor vizinho.
    Para quando nenhum vizinho supera a avaliação do estado atual.
    """
    atual = problema.estado_inicial_aleatorio(rng)
    valor_atual = problema.funcao_objetivo(atual)

    for _ in range(max_passos):
        melhor_troca = None
        melhor_valor = valor_atual
        fora = [t for t in problema.livres if t not in atual]

        for dentro in list(atual):
            for novo in fora:
                candidato = (atual - {dentro}) | {novo}
                val = problema.funcao_objetivo(candidato)
                if val > melhor_valor:
                    melhor_valor = val
                    melhor_troca = (dentro, novo)

        if melhor_troca is None:
            break  # Ótimo local ou platô atingido

        atual = (atual - {melhor_troca[0]}) | {melhor_troca[1]}
        valor_atual = melhor_valor

    return valor_atual, atual


def tempera_simulada(problema, rng, t_inicial=100.0, alpha=0.95, t_min=0.01, iter_por_temp=20):
    """Têmpera Simulada (Simulated Annealing).
    Aceita melhorias com probabilidade 1 e aceita pioras com probabilidade
    exp(delta / T), permitindo escapar de ótimos locais.
    """
    atual = problema.estado_inicial_aleatorio(rng)
    valor_atual = problema.funcao_objetivo(atual)
    melhor_solucao = set(atual)
    melhor_valor = valor_atual

    T = t_inicial
    pioras_aceitas = 0
    pioras_tentadas = 0

    while T > t_min:
        for _ in range(iter_por_temp):
            dentro = rng.choice(list(atual))
            fora = [t for t in problema.livres if t not in atual]
            novo = rng.choice(fora)
            candidato = (atual - {dentro}) | {novo}
            val_cand = problema.funcao_objetivo(candidato)
            delta = val_cand - valor_atual

            if delta > 0:
                atual = candidato
                valor_atual = val_cand
                if val_cand > melhor_valor:
                    melhor_valor = val_cand
                    melhor_solucao = set(candidato)
            else:
                pioras_tentadas += 1
                prob = math.exp(delta / T)
                if rng.random() < prob:
                    atual = candidato
                    valor_atual = val_cand
                    pioras_aceitas += 1

        T *= alpha

    return melhor_valor, melhor_solucao, pioras_aceitas, pioras_tentadas


def rodar_experimento_30(matricula: int, rodadas: int = 30):
    grade = gerar_pomar(matricula)
    problema = ProblemaInspecaoTalhoes(grade, k=15)

    hc_resultados = []
    sa_resultados = []
    pioras_aceitas_list = []

    for i in range(rodadas):
        # Sementes determinísticas e independentes para reprodutibilidade
        rng_hc = random.Random(matricula + i * 997 + 11)
        rng_sa = random.Random(matricula + i * 997 + 11)

        val_hc, _ = subida_de_encosta(problema, rng_hc)
        val_sa, _, p_acc, _ = tempera_simulada(problema, rng_sa)

        hc_resultados.append(val_hc)
        sa_resultados.append(val_sa)
        pioras_aceitas_list.append(p_acc)

    estatisticas = {
        "hc": {
            "valores": hc_resultados,
            "media": round(statistics.mean(hc_resultados), 2),
            "desvio": round(statistics.stdev(hc_resultados), 2),
            "melhor": round(max(hc_resultados), 2),
            "pior": round(min(hc_resultados), 2),
        },
        "sa": {
            "valores": sa_resultados,
            "media": round(statistics.mean(sa_resultados), 2),
            "desvio": round(statistics.stdev(sa_resultados), 2),
            "melhor": round(max(sa_resultados), 2),
            "pior": round(min(sa_resultados), 2),
            "media_pioras": round(statistics.mean(pioras_aceitas_list), 1),
            "min_pioras": min(pioras_aceitas_list),
            "max_pioras": max(pioras_aceitas_list),
        },
    }
    return estatisticas


if __name__ == "__main__":
    m = int(sys.argv[1]) if len(sys.argv) > 1 else 24114034
    print(f"=== Caatinga.AI - Parte 3.4: Busca Local (Matrícula {m}) ===")
    t0 = time.perf_counter()
    est = rodar_experimento_30(m, rodadas=30)
    dt = time.perf_counter() - t0

    print(f"\nTempo total para 30 execuções: {dt:.2f}s\n")
    print(f"{'Algoritmo':22} {'Média':>8} {'Desvio':>8} {'Melhor':>8} {'Pior':>8}")
    print("-" * 58)
    print(
        f"{'Subida de Encosta':22} {est['hc']['media']:>8.2f} "
        f"{est['hc']['desvio']:>8.2f} {est['hc']['melhor']:>8.2f} {est['hc']['pior']:>8.2f}"
    )
    print(
        f"{'Têmpera Simulada':22} {est['sa']['media']:>8.2f} "
        f"{est['sa']['desvio']:>8.2f} {est['sa']['melhor']:>8.2f} {est['sa']['pior']:>8.2f}"
    )
    print("-" * 58)
    print(
        f"Têmpera Simulada - Pioras aceitas de propósito: "
        f"Média = {est['sa']['media_pioras']:.1f} (mín: {est['sa']['min_pioras']}, máx: {est['sa']['max_pioras']})"
    )
