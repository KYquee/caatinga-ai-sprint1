# Caatinga.AI — Sprint 1

## 1. Identificação

**Disciplina:** Inteligência Artificial
**Período:** 2026.2
**Projeto:** Caatinga.AI - Sprint 1

**Integrantes:**

* Matheus Caique Braz Costa - 241.14.034
* Arthur Ivo Livino e Silva Maia - 241.14.053

**Matrícula utilizada como semente:** `24114034`

---

## 2. Sobre o projeto

O Caatinga.AI é um agente desenvolvido para planejar a movimentação em um pomar representado por uma grade de 12 × 12 talhões. O projeto implementa algoritmos de busca cega e busca informada para encontrar caminhos entre o portão `(0,0)` e o ponto de coleta `(11,11)`.

Foram implementados BFS, DFS, UCS e A*, utilizando três heurísticas diferentes. O projeto também possui uma etapa de busca local, um sistema especialista baseado em regras e cálculos probabilísticos utilizando Bayes.

---

## 3. Como executar

### Requisitos

* Python 3.x
* Dependências listadas em `requirements.txt`

Instalação:

```bash
pip install -r requirements.txt
```

Execução:

```bash
python src/main.py 24114034
```

O comando gera automaticamente:

```text
resultados/resultados.csv
resultados/grafico.png
resultados/pomar.txt
```

---

## 4. Resultados

Resultados obtidos utilizando a matrícula-semente `24114034`.

| Estratégia | Heurística         | Custo | Passos | Nós expandidos | Fronteira máxima |
| :---------- | :------------------ | :----: | :-----: | :-------------: | :---------------: |
| BFS        | -                  |    55 |     22 |            121 |               12 |
| DFS        | -                  |   130 |     52 |             81 |               47 |
| UCS        | -                  |    28 |     22 |            113 |               22 |
| A*         | h1 = 0             |    28 |      - |            113 |                - |
| A*         | h2 = Manhattan     |    28 |      - |             54 |                - |
| A*         | h3 = 4 × Manhattan |    31 |      - |             25 |                - |

A UCS encontrou o menor custo da rota para a semente utilizada. A heurística Manhattan também encontrou esse mesmo custo no A*, reduzindo o número de nós expandidos em relação à UCS.

---

## 5. Convenções das buscas

A ordem de expansão dos vizinhos utilizada em todas as estratégias é:

```text
Norte → Sul → Oeste → Leste
```

O estado é representado pela coordenada `(linha, coluna)`.

O A* implementado possui reabertura de nós quando um caminho de menor custo é encontrado.

---

## 6. Estrutura do repositório

| Arquivo                     | Função                                                                 |
| --------------------------- | ---------------------------------------------------------------------- |
| `src/gerador_pomar.py`      | Gera o pomar a partir da matrícula-semente.                            |
| `src/buscas.py`             | Implementa BFS, DFS, UCS e A*.                                         |
| `src/busca_local.py`        | Implementa subida de encosta e têmpera simulada.                       |
| `src/especialista.py`       | Implementa as regras do sistema especialista e encadeamento para trás. |
| `src/bayes.py`              | Realiza os cálculos probabilísticos da Parte 4.3.                      |
| `src/main.py`               | Executa as buscas e gera os arquivos de resultados.                    |
| `src/teste_escala.py`       | Realiza os testes de escalabilidade das buscas.                        |
| `resultados/resultados.csv` | Armazena os resultados das estratégias.                                |
| `resultados/grafico.png`    | Gráfico dos nós expandidos.                                            |
| `resultados/pomar.txt`      | Grade do pomar utilizada no experimento.                               |
| `RELATORIO.md`              | Relatório completo das Partes 1 a 5.                                   |
| `ANEXO_IA.md`               | Registro do uso de assistentes de IA.                                  |
| `requirements.txt`          | Dependências utilizadas no projeto.                                    |

[Relatório completo](RELATORIO.md)

[Anexo de uso de IA](ANEXO_IA.md)

---

## 7. Limitações conhecidas

Os resultados apresentados no relatório correspondem à matrícula-semente `24114034`. O desempenho das buscas pode variar para outras sementes, pois a geração do pomar é determinada pela matrícula.

Nos testes de escalabilidade, a versão recursiva da DFS atingiu o limite de recursão do Python em grades maiores. A DFS utilizada nas buscas principais é iterativa, utilizando uma pilha explícita.

O A* com `h3 = 4 × Manhattan` não possui garantia de admissibilidade e pode devolver uma rota de custo superior ao ótimo.
