# Relatório Caatinga.AI

## Parte 1 - O agente antes do código

### 1.1 Ficha PEAS 

| Agente | P | E | A | S |
|---|---|---|---|---|
| Caatinga.IA  | custo total do trajeto (unid. de talhão); nº de alertas verdadeiros/semana; horas de inspeção perdidas com falso positivo/semana  | grade 12×12 do pomar (carreador, solo encharcado, bloqueado); portão (0,0); ponto de coleta (11,11)  | movimento N/S/L/O; sinalização de talhão suspeito  | sensor óptico de pragas; posição na grade; tipo de terreno  |

### 1.2 Propriedades do Ambiente

|Dimensão|Classificação do Caatinga.IA|Frase do Cenário|
|:---:|:---:|---|
|Totalmente vs Parcialmente observável|***Discutível***|**Ver abaixo**|
|Determinístico vs Estocático|Determinístico| Custo de entrar num talhão é fixo por tipo (1 para ``.``, 4 para ``~``); a mesma ação no mesmo estado sempre produz o mesmo resultado. |
|Episódico vs Sequencial|Sequencial| O custo do caminho é a soma de todas as entradas de talhão ao longo de toda a rota, a ação de agora afeta o que ainda vem pela frente, não é uma decisão isolada. |
|Estático vs Dinâmico|***Discutível***|**Ver abaixo**|
|Discreto vs Contínuo|Discreto| Grade de células discretas, 4 ações possíveis por estado, custos em valores discretos (1 ou 4) |
|Agente único vs Multiagente|Agente único| O enunciado descreve um único agente percorrendo o pomar sozinho |

**Totalmente ou Parcialmente observável - depende de:** o agente ter acesso ao mapa 12×12 inteiro antes de começar o que seria ***totalmente observável*** para fins de planejamento. Ou ***parcialmente observável*** se só descobrir o tipo de cada talhão conforme se aproxima dele, via sensor local.<br> **A informação que falta é:** o agente planeja a rota com o mapa completo em mãos, ou descobre o terreno em tempo real enquanto anda?

**Estático ou Dinâmico - depende de:** as condições do pomar (ex: um talhão virar solo encharcado por causa de chuva) poderem mudar enquanto o agente ainda está no meio do percurso oque seria ***dinâmico***. Já ***estático*** se só mudam entre uma execução e outra (ex: toda semana o pomar é regerado, mas fica parado durante o trajeto).<br> **A informação que falta é:** o ambiente pode mudar durante a travessia do agente, ou só entre uma "rodada" e a próxima?

### 1.3 Tipo de Agente

O tipo escolhido foi o **Agente baseado em objetivos**. O Caatinga.AI tem um critério de sucesso único e bem definido - alcançar o ponto de coleta em (11,11) - e a tarefa central do projeto é justamente decidir, via busca (BFS/DFS/UCS/A*), qual sequência de movimentos atinge esse objetivo com o menor custo acumulado. O ambiente é determinístico e totalmente observável - exatamente as condições em que um agente baseado em objetivos com busca já resolve bem o problema, sem precisar de uma função de utilidade explícita ponderando objetivos conflitantes.

### 1.4 Métrica Perversa

**Métrica proposta:** "número de talhões inspecionados por semana" - parece razoável para o cliente, porque parece medir produtividade.

**Comportamento ruim que o agente aprenderia:** como inspecionar um talhão `~` (solo encharcado) custa 4× mais que um `.` (carreador firme), o agente otimizado só nessa métrica vai priorizar sistematicamente os talhões `.` - mais baratos, mais rápidos, mais fáceis de acumular contagem. Só que solo encharcado é justamente onde o risco de fungo é maior (é a própria regra do sistema especialista: `solo_encharcado` + `folhas_amareladas` -> `risco_fungo`). Resultado concreto: as zonas de maior risco fitossanitário do pomar ficam sistematicamente sub-inspecionadas, exatamente porque são as mais caras de visitar - um ponto cego criado pela própria métrica.

**Correção:** trocar por uma métrica ponderada por risco, por exemplo **"cobertura ponderada por risco"** = (soma do peso de risco dos talhões inspecionados) ÷ (soma do peso de risco de todos os talhões do pomar), onde talhões `~` recebem peso maior que talhões `.`. Isso faz o agente ser recompensado justamente por ir aonde é mais caro e mais necessário, em vez de ser recompensado por evitar esses lugares.

## Parte 2 - Formulação e busca cega
 
### 2.1 Os cinco componentes do problema de busca
 
| Componente | Definição para o Caatinga.AI |
|---|---|
| **Estado inicial** | `(0, 0)` - o portão de entrada do pomar |
| **Ações** | Mover para Norte, Sul, Oeste ou Leste, desde que a célula de destino esteja dentro da grade (0 ≤ i,j ≤ 11) e não seja `#` (bloqueada) |
| **Modelo de transição** | `resultado((i,j), acao) = (i±1, j)` ou `(i, j±1)`, conforme a ação; se a célula destino for inválida, a ação não está disponível naquele estado |
| **Teste de objetivo** | `estado == (11, 11)` |
| **Custo do caminho** | soma dos custos de entrada de cada talhão visitado (exceto o inicial): 1 por `.`, 4 por `~` |
 
**Tamanho do espaço de estados:** cada estado é uma célula da grade `(i,j)`, então o limite superior é `n × n = 12 × 12 = 144` estados. Descontando as células bloqueadas (`#`, que nunca são estados válidos porque o agente não pode entrar nelas), o espaço de estados realmente alcançável, para a matrícula-semente `24114034`, é **121 estados** (144 células − 23 bloqueadas), calculado com:
 
```python
from gerador_pomar import gerar_pomar
g = gerar_pomar(24114034)
livres = sum(row.count(".") + row.count("~") for row in g)
print(livres)  # 121
```
 
### 2.2 BFS, DFS e UCS instrumentadas
 
Ordem de expansão dos vizinhos usada em **todas** as estratégias do projeto: **Norte, Sul, Oeste, Leste** (declarada em `src/buscas.py`, constante `VIZINHOS_ORDEM`).
 
Resultado obtido rodando `python src/main.py 24114034`:
 
| Estratégia | Custo da rota | Nº de passos | Nós expandidos | Fronteira máx. | Rota é ótima em custo? |
|---|---|---|---|---|---|
| BFS | 55 | 22 | 121 | 12 | Não |
| DFS | 130 | 52 | 81 | 47 | Não |
| UCS | 28 | 22 | 113 | 22 | Sim |
 
 
### 2.3 Por que a BFS devolveu rota mais cara com o mesmo nº de passos ótimo
 
Não é bug. A BFS só garante custo mínimo quando todos os passos custam igual - aqui não custam (`.`=1, `~`=4). Ela para no primeiro caminho com menos passos, sem comparar custo entre caminhos de tamanhos diferentes. Por isso achou uma rota de 22 passos (igual à UCS) mas custando 55 em vez de 28 - entre as rotas de 22 passos, pegou uma com mais `~`.
 
A DFS mostra o oposto: sem nenhuma guia de custo ou proximidade do objetivo, mergulhou em ramos distantes antes de retroceder, resultando em 52 passos e custo 130.
 
### 2.4 Escalando n até uma estratégia falhar
 
Rodando `python src/teste_escala.py 24114034`, aumentando `n` de 12 até 1500 (medição de memória via `tracemalloc`, portátil entre Windows/Linux/Mac):
 
| n | Estados (n²) | BFS | DFS (iterativa) | DFS (recursiva) | UCS |
|---|---|---|---|---|---|
| 12 | 144 | OK | OK | OK | OK |
| 40 | 1.600 | OK | OK | OK | OK |
| **100** | 10.000 | OK | OK | **RecursionError** | OK |
| 200 | 40.000 | OK | OK | (já falhou) | OK |
| 1.000 | 1.000.000 | OK (8,1s) | OK (5,4s) | (já falhou) | OK (15,2s) |
| 1.500 | 2.250.000 | OK (19,3s) | OK (13,2s) | (já falhou) | OK (35,7s) |
 
**A DFS recursiva** (`dfs_recursiva`, feita só pra este teste) estourou em **n=100** com `RecursionError` - limite de ~1000 frames de pilha do Python, atingido porque o caminho explorado num pomar 100×100 cheio de obstáculos passa de 1000 células de profundidade. É por isso que a implementação principal (Partes 2.2/2.3) usa a **DFS iterativa** (pilha explícita, sem recursão), que não tem esse limite.
 
BFS, DFS iterativa e UCS não falharam até n=1500. O crescimento é O(n²), coerente com nº de estados ∝ n². UCS foi a mais lenta (heap tem mais overhead) e, extrapolando (15,2s em n=1000 → 35,7s em n=1500), passaria de 60s em torno de **n≈1.800**. Memória também cresce ~linear com o nº de estados (~484 MB em n=1500) - em máquinas com menos RAM, `MemoryError` apareceria antes do timeout.

---

## Parte 3 - Busca informada e busca local

### 3.1 A* com três heurísticas

Executando o $A^*$ implementado em `src/buscas.py` com a semente `24114034` (ordem de vizinhos N, S, O, L e teste de objetivo na expansão):

| Heurística | Custo da rota | Nós expandidos | Admissível? (prove) |
|---|:---:|:---:|---|
| **$h_1(n) = 0$** | 28 | 113 | **Sim** (Trivial: como todos os custos de entrada são $\ge 1 > 0$, $0 \le h^*(n)$ para todo $n$). |
| **$h_2(n) = \text{Manhattan}(n)$** | 28 | 54 | **Sim** (Demonstração formal na Seção 3.2 abaixo). |
| **$h_3(n) = 4 \times \text{Manhattan}(n)$** | 31 | 25 | **Não** (Superestima o custo real restante; contraexemplo na Seção 3.2). |

*Nota de calibração:* Rodando com a semente de aferição `20231045`, o $A^*$ com $h_2$ obteve exatamente custo 34 e expandiu 91 nós (aderente à referência do enunciado de ~93 nós).

---

### 3.2 Demonstrações de Admissibilidade

#### Prova de Admissibilidade para $h_2(n)$
Em uma grade bidimensional com movimentação restrita às quatro direções cardeais ortogonais (Norte, Sul, Oeste, Leste), a distância de Manhattan entre qualquer célula $n = (i, j)$ e o objetivo $obj = (11, 11)$ é dada por:
$$d_M(n, obj) = |i - 11| + |j - 11|$$

Essa distância representa o número mínimo absoluto de passos ortogonais necessários para transitar de $n$ até $obj$ em um grafo ideal (relaxado, sem bloqueios `#`).

No pomar do Caatinga.AI, os custos de entrada em talhões livres são:
* Carreador firme (`.`): $c = 1$
* Solo encharcado (`~`): $c = 4$

Portanto, o custo mínimo de qualquer transição possível na grade é $c_{\min} = 1$. Seja $P$ o número real de passos de qualquer caminho factível de $n$ até o objetivo. Como eventuais obstáculos (`#`) apenas forçam desvios, temos necessariamente $P \ge d_M(n, obj)$. Logo, o custo real restante $h^*(n)$ satisfaz:
$$h^*(n) = \sum_{k=1}^{P} c(step_k) \ge \sum_{k=1}^{P} c_{\min} = P \times 1 = P \ge d_M(n, obj) = h_2(n)$$

Como $h_2(n) \le h^*(n)$ para todo estado $n$ alcançável e $h_2(obj) = 0$, $h_2$ nunca superestima o custo real restante até o objetivo, sendo **estritamente admissível** (e consistente, visto que a variação de $h_2$ entre vizinhos ortogonais é de no máximo $1 \le c$).

#### Refutação de Admissibilidade para $h_3(n)$ com Par de Talhões Concretos
A heurística $h_3(n) = 4 \times d_M(n, obj)$ pressupõe que todos os passos até o objetivo ocorrerão sobre solo encharcado (`~`, custo 4). Contudo, grande parte do pomar é composta por carreadores firmes (`.`, custo 1). Seguem dois exemplos concretos da grade gerada com a semente `24114034`:

1. **Talhão inicial $(0, 0)$:**
   * Distância de Manhattan até $(11, 11)$: $|0 - 11| + |0 - 11| = 22$.
   * Valor heurístico estimado: $h_3((0, 0)) = 4 \times 22 = \mathbf{88}$.
   * Custo real ótimo até o objetivo (calculado via UCS): $h^*((0, 0)) = \mathbf{28}$.
   * **Conclusão:** $h_3((0, 0)) = 88 > 28 = h^*((0, 0))$. A heurística superestima o custo real em **$+60$** ($+214\%$).

2. **Talhão vizinho ao objetivo $(10, 11)$:**
   * Tipo de terreno do talhão $(10, 11)$: carreador firme (`.`).
   * Distância de Manhattan até o objetivo $(11, 11)$: $|10 - 11| + |11 - 11| = 1$.
   * Valor heurístico estimado: $h_3((10, 11)) = 4 \times 1 = \mathbf{4}$.
   * Custo real restante: para entrar na célula objetivo $(11, 11)$ (que é `.`), o custo é exatamente $\mathbf{1}$.
   * **Conclusão:** $h_3((10, 11)) = 4 > 1 = h^*((10, 11))$. A heurística superestima o custo real em **$+3$** ($+300\%$).

A existência desses estados concretos viola a condição $h(n) \le h^*(n)$, provando formalmente que $h_3$ **não é admissível**.

---

### 3.3 A Pergunta que Separa quem Rodou de quem Entendeu

#### Comparação do Custo Devolvido por $h_3$ com o UCS
* Custo ótimo de referência (UCS): **28**
* Custo devolvido pelo $A^*$ com $h_3$: **31**
* O custo ficou **maior** que o ótimo.

**Cálculo da perda percentual:**
$$\text{Perda Percentual} = \frac{\text{Custo}(h_3) - \text{Custo}(\text{UCS})}{\text{Custo}(\text{UCS})} \times 100\% = \frac{31 - 28}{28} \times 100\% = \frac{3}{28} \times 100\% \approx \mathbf{10,71\%}$$

**Nós de expansão "comprados":**
* A UCS expandiu **113 nós**.
* O $A^*$ com $h_2$ (admissível) expandiu **54 nós**.
* O $A^*$ com $h_3$ expandiu apenas **25 nós**.
* A perda de $10,71\%$ na otimalidade do caminho permitiu economizar **88 nós expandidos** em relação à UCS (uma redução de **$77,88\%$** no esforço de busca) e **29 nós expandidos** em relação ao $A^*$ com Manhattan (redução de **$53,70\%$**).

#### E se o Custo Fosse Igual, Provaria Admissibilidade?
**Não.** A admissibilidade de uma heurística é uma propriedade universal quantificada sobre todo o espaço de estados: exige-se que $h(n) \le h^*(n)$ para **todo** $n \in S$. O fato de um algoritmo guiado por uma heurística inadmissível eventualmente devolver uma rota de custo ótimo em um pomar específico é apenas uma coincidência decorrente da topologia daquele mapa particular e dos critérios de desempate da fila, não fornecendo nenhuma garantia matemática teórica para outras execuções ou outros pomares.

#### Cenário de Negócio da Cooperativa
**Condição verificável:**
Trocar garantia de otimalidade por velocidade é justificável quando o pomar escala para dimensões operacionais de grande porte ($n \ge 1.000$ talhões, totalizando $\ge 1.000.000$ de estados) e o veículo autônomo opera sob um **limite estrito de tempo de resposta em tempo real ($t_{\text{limite}} \le 200\text{ ms}$)** em hardware embarcado de baixo consumo.
Conforme demonstrado no teste de escalabilidade da Parte 2.4, a UCS leva **15,2 segundos** para planejar em $n=1.000$, o que tornaria o robô inoperante em tempo real. Aceitar um desvio de rota de até $\sim 10\%$ no custo energético da bateria em troca de uma resposta calculada em milissegundos ($< 100\text{ ms}$) viabiliza a operação do sistema sem interrupções de navegação em campo.

---

### 3.4 Busca Local: Seleção de $K=15$ Talhões para Inspeção (6h de Bateria)

#### Modelagem Formal do Problema
1. **Espaço de Estados ($S$):** Subconjunto de exatamente $K = 15$ talhões livres e distintos da grade ($S \subset L$, com $|S| = 15$ e $L = \{(i,j) \mid \text{grade}[i][j] \neq \text{'\#'}\}$). Na semente `24114034`, $|L| = 121$, resultando em um espaço de busca com $\binom{121}{15} \approx 6,65 \times 10^{17}$ combinações possíveis.
2. **Vizinhança ($N(S)$):** Operador de troca simples (1-swap). Um vizinho $S'$ é gerado substituindo um talhão inspecionado $u \in S$ por um talhão livre não inspecionado $v \in L \setminus S$. Cada estado possui uma vizinhança imediata de $15 \times (121 - 15) = 1.590$ estados vizinhos.
3. **Função Objetivo ($f(S)$ - a ser maximizada):**
   $$f(S) = \sum_{t \in S} R_{\text{base}}(t) + \sum_{u \in S} \sum_{v \in S \cap \text{viz}(u)} 1.0 - 0.5 \times \sum_{t \in S} \left( |i_t - c_i| + |j_t - c_j| \right)$$
   * **Risco Fitossanitário Base:** Talhão encharcado `~` pontua $+10.0$ (maior suscetibilidade a patógenos radiculares e fúngicos da manga); carreador firme `.` pontua $+3.0$.
   * **Bônus de Contiguidade / Foco:** $+2.0$ por par de talhões adjacentes ortogonalmente em $S$, refletindo a detecção de manchas contíguas de infestação.
   * **Penalidade Logística de Dispersão:** $0.5 \times$ soma das distâncias Manhattan de cada talhão ao centroide geométrico $(c_i, c_j)$ do conjunto $S$, modelando o gasto de deslocamento do robô sob o teto rígido de 6 horas de autonomia de bateria.

#### Resultados Comparativos (30 Rodadas Independentes - `src/busca_local.py`)

| Algoritmo | Média | Desvio Padrão | Melhor Valor | Pior Valor |
|---|:---:|:---:|:---:|:---:|
| **Subida de Encosta (Hill Climbing)** | 154,94 | 2,97 | 158,87 | 150,20 |
| **Têmpera Simulada (Simulated Annealing)** | 152,61 | 2,26 | 158,73 | 148,93 |

* **Média de pioras aceitas de propósito na Têmpera Simulada:** **603,9 pioras/execução** (mínimo: 565, máximo: 657).

#### Por que Aceitar Piora de Propósito Ajuda? (Aula 04)
A Subida de Encosta adota uma abordagem puramente gulosa e monotônica: só aceita transições onde $f(S') > f(S)$. Como o espaço de busca possui múltiplos agrupamentos de talhões encharcados separados por barreiras de carreadores e dispersão, a função objetivo apresenta diversos **máximos locais**. A Subida de Encosta inevitavelmente fica presa no primeiro pico local que atinge, incapaz de cruzar regiões de valor temporariamente inferior.

A Têmpera Simulada supera essa armadilha aceitando movimentos que pioram a função objetivo com probabilidade controlada pela temperatura:
$$P(\text{aceitar piora}) = e^{\frac{\Delta E}{T}}, \quad \text{onde } \Delta E = f(S') - f(S) < 0$$

No início da busca, quando a temperatura $T$ está alta, o algoritmo aceita pioras com frequência (em média mais de 600 pioras por rodada nos testes práticos), funcionando como um passeio aleatório capaz de transpor vales e escapar de bacias de atração medíocres. À medida que o sistema resfria ($T \to 0$), a probabilidade de aceitar pioras decai progressivamente, convergindo para uma exploração refinada em torno das melhores bacias globais encontradas.

---

### Bônus - Liga de IA (+0,3): Construção de Contraexemplo para a DFS

#### Racional da Construção Analítica
A ordem fixa de expansão dos vizinhos declarada para o projeto é **Norte, Sul, Oeste, Leste** ($N \to S \to O \to L$).
A partir do portão inicial $(0, 0)$, a direção Norte está fora dos limites da grade. Portanto, a **primeira direção que a DFS sempre tentará explorar é o Sul** ($S = (1, 0)$).

Para forçar a DFS a devolver uma rota substancialmente pior que a ótima, construímos deliberadamente uma grade $4 \times 4$ ($\le 8 \times 8$) com duas ramificações antagônicas a partir de $(0, 0)$:
1. **O ramo ao Leste ($L$):** Uma linha direta de carreadores firmes (`.`, custo 1) até a meta $(3, 3)$.
2. **O ramo ao Sul ($S$):** Um corredor contínuo de talhões de solo encharcado (`~`, custo 4) ladeado por bloqueios (`#`), formando uma serpentina obrigatória que desce até a base da grade antes de alcançar a meta.

Como a DFS prioriza o Sul e mergulha cegamente em profundidade sem levar os custos de aresta em consideração, ela percorre toda a serpentina de solo encharcado sem retroceder, ignorando o caminho direto e econômico pelo Leste.

#### Grade $4 \times 4$ Construída à Mão
```
.  .  .  .
~  #  #  .
~  ~  ~  .
#  #  ~  .
```

#### Comparação das Rotas e Custos
* **Rota devolvida pela DFS:**
  `(0,0) -> (1,0)[~:4] -> (2,0)[~:4] -> (2,1)[~:4] -> (2,2)[~:4] -> (3,2)[~:4] -> (3,3)[.:1]`
  * Número de passos: **6**
  * Custo total da DFS: $4 + 4 + 4 + 4 + 4 + 1 = \mathbf{21}$

* **Rota ótima devolvida pela UCS:**
  `(0,0) -> (0,1)[.:1] -> (0,2)[.:1] -> (0,3)[.:1] -> (1,3)[.:1] -> (2,3)[.:1] -> (3,3)[.:1]`
  * Número de passos: **6**
  * Custo total da UCS (ótimo): $1 + 1 + 1 + 1 + 1 + 1 = \mathbf{6}$

**Razão dos custos:**
$$\frac{\text{Custo}(\text{DFS})}{\text{Custo}(\text{UCS})} = \frac{21}{6} = \mathbf{3,5 \times}$$

O custo devolvido pela DFS foi **3,5 vezes maior que o ótimo**, superando com folga o dobro ($> 2,0\times$) exigido pelo regulamento do bônus.