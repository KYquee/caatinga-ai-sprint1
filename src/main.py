"""
main.py - Parte 2. Roda BFS, DFS e UCS para uma matrícula e gera os
artefatos exigidos: resultados/resultados.csv, resultados/grafico.png,
resultados/pomar.txt

Uso: python src/main.py <matricula>
"""
import csv
import os
import sys

from gerador_pomar import gerar_pomar
from buscas import bfs, dfs, ucs


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

    # --- Buscas ---
    linhas = [
        ("BFS", bfs(grade)),
        ("DFS", dfs(grade)),
        ("UCS", ucs(grade)),
    ]
    custo_ucs = linhas[2][1].custo  # UCS é a referência de custo ótimo

    with open(os.path.join(dir_resultados, "resultados.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["estrategia", "custo", "passos", "nos_expandidos",
                    "fronteira_max", "tempo_ms", "otima_em_custo"])
        for nome, r in linhas:
            w.writerow([nome, r.custo, r.passos, r.nos_expandidos,
                        r.fronteira_max, round(r.tempo_ms, 3),
                        "sim" if r.custo == custo_ucs else "nao"])

    # --- Gráfico: nós expandidos x estratégia ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        nomes = [nome for nome, _ in linhas]
        nos = [r.nos_expandidos for _, r in linhas]

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(nomes, nos, color="#4a7c59")
        ax.set_xlabel("Estratégia de busca")
        ax.set_ylabel("Nós expandidos")
        ax.set_title(f"Caatinga.AI - Nós expandidos por estratégia (matrícula {matricula})")
        for i, v in enumerate(nos):
            ax.text(i, v + max(nos) * 0.01, str(v), ha="center", fontsize=9)
        plt.tight_layout()
        plt.savefig(os.path.join(dir_resultados, "grafico.png"), dpi=150)
        plt.close(fig)
    except ImportError:
        print("AVISO: matplotlib não encontrado - grafico.png não foi gerado. "
              "Rode: pip install matplotlib", file=sys.stderr)

    # --- Resumo no console ---
    print(f"=== Caatinga.AI - matrícula {matricula} (Parte 2) ===\n")
    for nome, r in linhas:
        otima = "sim" if r.custo == custo_ucs else "nao"
        print(f"{nome:5} custo={r.custo:>4}  passos={r.passos:>3}  "
              f"nos_expandidos={r.nos_expandidos:>4}  fronteira_max={r.fronteira_max:>3}  "
              f"otima_em_custo={otima}")

    print(f"\nArquivos gerados em: {dir_resultados}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/main.py <matricula>")
        sys.exit(1)
    main(int(sys.argv[1]))