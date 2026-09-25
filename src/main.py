"""
main.py - Roda BFS, DFS, UCS e A* (h1, h2, h3) para uma matrícula e gera os
artefatos exigidos pelo enunciado: resultados/resultados.csv, resultados/grafico.png,
resultados/pomar.txt

Uso: python src/main.py <matricula>
"""
import csv
import os
import sys

from gerador_pomar import gerar_pomar
from buscas import bfs, dfs, ucs, astar


def main(matricula):
    grade = gerar_pomar(matricula)

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dir_resultados = os.path.join(raiz, "resultados")
    os.makedirs(dir_resultados, exist_ok=True)

    # --- pomar.txt (semente na 1a linha) ---
    with open(os.path.join(dir_resultados, "pomar.txt"), "w") as f:
        f.write(f"{matricula}\n")
        for linha in grade:
            f.write(" ".join(linha) + "\n")

    # --- Buscas Cegas e Informadas ---
    linhas = [
        ("BFS", "-", bfs(grade)),
        ("DFS", "-", dfs(grade)),
        ("UCS", "-", ucs(grade)),
        ("A*", "h1 (zero)", astar(grade, heuristica="h1")),
        ("A*", "h2 (Manhattan)", astar(grade, heuristica="h2")),
        ("A*", "h3 (4xManhattan)", astar(grade, heuristica="h3")),
    ]
    custo_ucs = linhas[2][2].custo  # UCS é a referência de custo ótimo

    # --- resultados.csv (Seção 9.1: estrategia,heuristica,custo,passos,nos_expandidos,fronteira_max,tempo_ms) ---
    with open(os.path.join(dir_resultados, "resultados.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["estrategia", "heuristica", "custo", "passos", "nos_expandidos",
                    "fronteira_max", "tempo_ms"])
        for estr, heur, r in linhas:
            w.writerow([estr, heur, r.custo, r.passos, r.nos_expandidos,
                        r.fronteira_max, round(r.tempo_ms, 3)])

    # --- Gráfico: nós expandidos x estratégia com eixos rotulados ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = [f"{estr}\n{heur}" if heur != "-" else estr for estr, heur, _ in linhas]
        nos = [r.nos_expandidos for _, _, r in linhas]

        fig, ax = plt.subplots(figsize=(9, 5.5))
        cores = ["#5c7f67", "#8c6d62", "#4a7c59", "#3b6978", "#204051", "#d9534f"]
        barras = ax.bar(labels, nos, color=cores)
        ax.set_xlabel("Estratégia de busca / Heurística", fontsize=11, fontweight="bold")
        ax.set_ylabel("Nós expandidos (unidades)", fontsize=11, fontweight="bold")
        ax.set_title(f"Caatinga.AI - Nós expandidos por estratégia (matrícula {matricula})", fontsize=12, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        for bar, v in zip(barras, nos):
            ax.text(bar.get_x() + bar.get_width() / 2, v + max(nos) * 0.015, str(v),
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

        plt.tight_layout()
        plt.savefig(os.path.join(dir_resultados, "grafico.png"), dpi=150)
        plt.close(fig)
    except ImportError:
        print("AVISO: matplotlib não encontrado - grafico.png não foi gerado. "
              "Rode: pip install matplotlib", file=sys.stderr)

    # --- Resumo no console ---
    print(f"=== Caatinga.AI - matrícula {matricula} (Buscas Concluídas) ===\n")
    print(f"{'Estratégia':10} {'Heurística':18} {'Custo':>6} {'Passos':>7} {'NósExp':>7} {'FrontMáx':>9} {'Ótimo?':>7}")
    print("-" * 72)
    for estr, heur, r in linhas:
        otima = "sim" if r.custo == custo_ucs else "nao"
        print(f"{estr:10} {heur:18} {r.custo:>6} {r.passos:>7} {r.nos_expandidos:>7} {r.fronteira_max:>9} {otima:>7}")

    print(f"\nArquivos gerados com sucesso em: {dir_resultados}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/main.py <matricula>")
        sys.exit(1)
    main(int(sys.argv[1]))