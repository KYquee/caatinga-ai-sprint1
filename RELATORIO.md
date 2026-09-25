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