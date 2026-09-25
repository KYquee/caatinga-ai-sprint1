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

O tipo escolhido foi o **Agente baseado em objetivos**. O Caatinga.AI tem um critério de sucesso único e bem definido - alcançar o ponto de coleta em (11,11) - e a tarefa central do projeto é justamente decidir, via busca (BFS/DFS/UCS/A*), qual sequência de movimentos atinge esse objetivo com o menor custo acumulado. O ambiente é determinístico e (assumindo mapa completo disponível) totalmente observável - exatamente as condições em que um agente baseado em objetivos com busca já resolve bem o problema, sem precisar de uma função de utilidade explícita ponderando objetivos conflitantes.

### 1.4 Métrica Perversa

**Métrica proposta (perigosa):** "número de talhões inspecionados por semana" - parece razoável para o cliente, porque parece medir produtividade.

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
 
*(Implementação validada previamente contra a caixa de aferição do enunciado com a matrícula fictícia 20231045: UCS=34, BFS=55/22 passos, nós UCS≈112 - todos bateram exatamente ou dentro da margem de ±20% aceita para nós expandidos.)*
 
### 2.3 Por que a BFS devolveu uma rota mais cara, mesmo com o menor nº de passos possível
 
Isso **não é um bug**. A hipótese violada é a premissa de otimalidade da BFS: ela só garante encontrar a rota de **menor custo** quando **todos os passos têm o mesmo custo** (grafo com custo uniforme por aresta). A BFS expande por número de passos, não por custo acumulado - ela para assim que encontra *qualquer* caminho com o menor número de movimentos possível, sem comparar o custo desse caminho com o de outros caminhos mais longos em passos, porém mais baratos.
 
No pomar do Caatinga.AI, os talhões `~` custam 4× mais que os `.`. Uma rota pode ter o menor número de passos e ainda assim atravessar vários talhões `~`, resultando em custo total maior do que uma rota com mais passos, mas que evita solo encharcado. Isso é exatamente o que aconteceu: a rota da BFS tem os mesmos 22 passos da UCS, mas custa 55 contra 28 - ela escolheu, entre as rotas de 22 passos, uma que passa por talhões mais caros, porque BFS não tem como comparar custo, só contagem de movimentos. (A DFS ilustra o oposto: encontrou uma rota bem mais longa, 52 passos e custo 130, porque não é guiada nem por custo nem por proximidade do objetivo - segue a ordem fixa de vizinhos até "esbarrar" numa saída, mergulhando fundo em ramos que se afastam do ponto de coleta antes de retroceder.)
 
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
 
**Quem falhou, em qual n, e por quê:** a **DFS recursiva** (implementada em `dfs_recursiva`, em `src/buscas.py`, feita especificamente para observar esse limite) estourou a pilha de chamadas em **n = 100** (10.000 estados), com `RecursionError`. O limite teórico é o **limite de profundidade de recursão do Python** (por padrão ~1000 frames de pilha) - cada chamada recursiva empilha um novo frame por estado visitado, e a profundidade máxima da recursão é proporcional ao comprimento do caminho mais longo que a DFS percorre antes de "desempilhar" (retroceder). Num pomar 100×100 cheio de obstáculos, a DFS explora ramos que facilmente ultrapassam 1000 células de profundidade antes de encontrar o objetivo ou esgotar um ramo - violando o limite do interpretador. Isso ilustra exatamente a armadilha nº1 do enunciado (custo de pilha da DFS via recursão) e é a razão pela qual a implementação **principal** do projeto (usada nas Partes 2.2 e 2.3) é a **DFS iterativa** (com pilha explícita em Python `list`, sem recursão): ela não tem esse limite porque a "pilha" vira uma estrutura de dados no heap da memória, não frames de chamada de função.
 
BFS, DFS iterativa e UCS **não falharam** dentro dos tamanhos testados (até n=1500, 2,25 milhões de estados) - mas o crescimento do tempo é claramente **O(n²)**, coerente com o número de estados sendo proporcional a n² (fórmula de complexidade da Aula 03 para busca em grafo). A UCS foi a mais lenta em todos os tamanhos (heap de prioridade tem overhead maior que fila/pilha simples) - saiu de 15,2s em n=1000 para 35,7s em n=1500, já perto do limite de 60s. Extrapolando essa curva, a UCS ultrapassaria 60s em torno de **n ≈ 1.800** (3,2 milhões de estados). O consumo de memória também cresce de forma aproximadamente linear com o nº de estados (chegou a ~484 MB em n=1500, para armazenar `custo_ate`, `veio_de` e a fronteira) - em máquinas com menos RAM disponível, `MemoryError` seria a causa mais provável de falha em tamanhos ainda maiores, antes mesmo de bater o timeout de 60s.
 
BFS, DFS iterativa e UCS **não falharam** dentro dos tamanhos testados (até n=3000, 9 milhões de estados) - mas a tendência de tempo é claramente **O(n²) = O(b·|E|)**, coerente com a fórmula de complexidade da Aula 03 para busca em grafo com número de estados proporcional a n². Extrapolando a curva medida (UCS foi de 11,8s em n=2000 para 28,8s em n=3000 - um crescimento mais que proporcional ao dobro de estados, coerente com o custo extra de manter um heap maior a cada expansão), a UCS ultrapassaria o limite de 60s em torno de **n ≈ 4.000-4.500** (16 a 20 milhões de estados). O consumo de memória também cresce linearmente com o nº de estados (chegou a ~2 GB em n=3000, para armazenar `custo_ate`, `veio_de` e a fronteira de ~9 milhões de entradas) - em algum ponto acima disso, `MemoryError` seria a causa provável de falha antes mesmo do timeout de 60s, dependendo da memória disponível na máquina.