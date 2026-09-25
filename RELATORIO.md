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
 
Rodando `src/buscas.py` com a semente `24114034` (ordem N,S,O,L; objetivo testado na expansão):
 
| Heurística | Custo | Nós expandidos | Admissível? |
|---|---|---|---|
| h1 = 0 | 28 | 113 | Sim (trivial: 0 ≤ h*(n) sempre) |
| h2 = Manhattan | 28 | 54 | Sim (prova abaixo) |
| h3 = 4×Manhattan | 31 | 25 | Não (contraexemplo abaixo) |
 
*(Calibração: com a semente 20231045, h2 deu custo 34 e 91 nós - aderente à referência do enunciado, ~93.)*
 
### 3.2 Provas de admissibilidade
 
**h2 é admissível:** o custo mínimo de qualquer passo na grade é 1 (talhão `.`). A distância de Manhattan `d(n,obj)` é o número mínimo de passos ortogonais até o objetivo, ignorando bloqueios. Como bloqueios só forçam desvios (mais passos, nunca menos), o número real de passos `P ≥ d(n,obj)`, e o custo real `h*(n) = soma dos custos dos P passos ≥ P × 1 ≥ d(n,obj) = h2(n)`. Logo `h2(n) ≤ h*(n)` para todo estado - admissível.
 
**h3 não é admissível** - dois talhões concretos da semente `24114034` onde superestima:
- `(0,0)`: h3 = 4×22 = **88**, custo real ótimo h* = **28** (superestima em +60)
- `(10,11)` (talhão `.`, vizinho do objetivo): h3 = 4×1 = **4**, custo real h* = **1** (superestima em +3)
### 3.3 Custo de h3 vs. UCS
 
Custo h3 = 31, UCS = 28 → **maior**. Perda percentual = (31-28)/28 = **10,71%**. Em troca, nós expandidos caíram de 113 (UCS) para 25 (h3) - **88 nós a menos** (77,9% de redução).
 
**Se tivesse ficado igual, provaria admissibilidade?** Não. Admissibilidade exige `h(n) ≤ h*(n)` para **todo** estado do espaço, não só para os estados visitados numa execução. Bater o custo ótimo num pomar específico seria coincidência da topologia daquele mapa, sem garantia nenhuma para outras sementes.
 
**Condição de negócio verificável:** trocar otimalidade por velocidade vale a pena quando o pomar escala (n ≥ 1.000, ≥1 milhão de estados) **e** existe limite de tempo real rígido (ex.: resposta em ≤200ms num hardware embarcado). Na Parte 2.4, a UCS levou 15,2s para n=1.000 - inviável em tempo real. Aceitar ~10% a mais de custo por uma resposta em milissegundos é a troca que viabiliza o sistema nesse cenário.
 
### 3.4 Busca local: K=15 talhões, 6h de bateria
 
**Modelagem:** estado = subconjunto de 15 talhões livres (|L|=121 para a semente `24114034`, logo C(121,15) ≈ 6,65×10¹⁷ combinações possíveis). Vizinhança = troca de 1 talhão por outro fora do conjunto (1.590 vizinhos por estado). Objetivo (maximizar): risco fitossanitário dos talhões escolhidos (`~`=10, `.`=3) + bônus de contiguidade (+2 por par adjacente, simulando manchas de infestação) − penalidade de dispersão (0,5× soma das distâncias Manhattan ao centroide, simulando gasto de deslocamento sob a bateria limitada).
 
**Resultado (30 execuções, `src/busca_local.py`):**
 
| Algoritmo | Média | Desvio | Melhor | Pior |
|---|---|---|---|---|
| Subida de encosta | 154,94 | 2,97 | 158,87 | 150,20 |
| Têmpera simulada | 152,61 | 2,26 | 158,73 | 148,93 |
 
Têmpera simulada aceitou em média **603,9 pioras de propósito por execução** (mín. 565, máx. 657).
 
**Por que aceitar piora ajuda:** a subida de encosta só aceita vizinhos estritamente melhores - fica presa no primeiro pico local que encontra. A têmpera simulada aceita pioras com probabilidade `exp(Δ/T)`: no início (T alto) aceita quase qualquer coisa, funcionando como passeio aleatório que atravessa vales entre picos; conforme T cai, a aceitação de pioras cai junto, convergindo pra uma busca fina perto das melhores regiões encontradas. As ~604 pioras aceitas por execução são exatamente esse mecanismo em ação.
 
### Bônus - Liga de IA: contraexemplo pra DFS
 
Como Norte está fora da grade em `(0,0)`, a DFS sempre tenta Sul primeiro. Construí uma grade 4×4 com um corredor de solo encharcado (`~`) ao Sul e um caminho direto de carreadores (`.`) ao Leste:
 
```
. . . .
~ # # .
~ ~ ~ .
# # ~ .
```
 
- **DFS** (segue Sul cegamente): `(0,0)→(1,0)→(2,0)→(2,1)→(2,2)→(3,2)→(3,3)`, todos `~` exceto o último - custo = 4×5+1 = **21**
- **UCS (ótima)**: `(0,0)→(0,1)→(0,2)→(0,3)→(1,3)→(2,3)→(3,3)`, todos `.` - custo = **6**
Razão = 21/6 = **3,5×** o ótimo (exigido: >2×).

## Parte 4 - Regras e incerteza

Parâmetros do sensor (`parametros_sensor(24114034)`): prevalência=0,0272; sensibilidade=0,99; taxa de falso positivo=0,03; talhões/semana=800.

### 4.1 Mini sistema especialista

7 regras SE...ENTÃO (`src/especialista.py`), com encadeamento para trás e rastro de explicação:

```
R1: armadilha_positiva E umidade_alta E dias_desde_pulverizacao>14 -> inspecionar_prioridade_alta
R2: armadilha_positiva E umidade_baixa -> inspecionar_prioridade_media
R3: folhas_amareladas E solo_encharcado -> risco_fungo
R4: risco_fungo E temperatura_alta -> inspecionar_prioridade_alta
R5: sem_sinais_visuais E armadilha_negativa -> manejo_rotina
R6: inspecionar_prioridade_alta E talhao_proximo_reservatorio -> acionar_agronomo_presencial
R7: dias_desde_pulverizacao>14 E chuva_recente -> reprogramar_pulverizacao
```

Exemplo de rastro (`python src/especialista.py`), fatos `{folhas_amareladas, solo_encharcado, temperatura_alta}`, pergunta "por que inspecionar_prioridade_alta?":
```
Tentando R1 -> premissa 'armadilha_positiva' FALHOU
Tentando R4: risco_fungo E temperatura_alta -> inspecionar_prioridade_alta
  Tentando R3: folhas_amareladas E solo_encharcado -> risco_fungo
    premissa 'folhas_amareladas' -> OK
    premissa 'solo_encharcado' -> OK
  => R3 disparada: 'risco_fungo' PROVADO
  premissa 'risco_fungo' -> OK
  premissa 'temperatura_alta' -> OK
=> R4 disparada: 'inspecionar_prioridade_alta' PROVADO
```
R1 falhou (sem armadilha_positiva), o motor então testou R4, que encadeou com R3 - exatamente o "por que você concluiu isso?" pedido.

### 4.2 Quebrando a própria base

**Caso legítimo mal classificado:** fatos `{armadilha_positiva, umidade_alta}` - praga confirmada, mas ainda dentro da janela segura de pulverização (≤14 dias). Nem R1 (exige >14 dias) nem R2 (exige umidade_baixa) disparam → a base conclui **"não provado"** para qualquer prioridade. Um talhão com praga confirmada fica sem nenhum manejo recomendado - erro de omissão perigoso.

**Regra corretiva**, sem contradizer R1/R2:
```
R8: armadilha_positiva -> inspecionar_prioridade_media
```
Traço antes: `inspecionar_prioridade_media` → NÃO PROVADO (R2 falha em `umidade_baixa`).
Traço depois: R2 ainda falha, mas R8 dispara com só `armadilha_positiva` → PROVADO.

### 4.3 Bayes com os números da dupla

(a) `P(infestado|positivo)` via Bayes:
```
P(inf|pos) = (0,99 × 0,0272) / (0,99 × 0,0272 + 0,03 × 0,9728) = 0,4799
```

(b) A cada 100 alertas do sistema, cerca de **52** são falsos.

(c) Com 800 talhões/semana: **44,9 alertas totais/semana**, dos quais **23,3 são falsos**. A 12 min por inspeção, isso é **4,67 horas/semana** perseguindo alertas falsos.

(d) Aumentando a sensibilidade para 99,9% (mantendo FPR=0,03): novo VPP = **0,4822** - praticamente igual ao original (0,4799). **Não resolve o problema.** Sensibilidade já era alta (0,99); o gargalo é a **taxa de falso positivo** (0,03) multiplicando uma população majoritariamente saudável (97,28%). O parâmetro que realmente vale a pena mexer é a **taxa de falso positivo**, não a sensibilidade.

### 4.4 A regra que fica em regra explícita

**Decisão:** "nunca aplicar manejo automático (ex.: liberar pulverização) num talhão a menos de 14 dias da última aplicação" deve ficar como **regra explícita** (SE...ENTÃO), não em modelo aprendido.

**Justificativa (auditabilidade, não acurácia):** intervalo mínimo de reaplicação é uma exigência regulatória/de segurança do produto, não um padrão estatístico a ser "aprendido" dos dados. Um modelo treinado poderia, em tese, aprender a relaxar essa restrição se isso correlacionasse com melhores métricas de produtividade no histórico - e isso seria uma falha auditável e potencialmente ilegal. Uma regra explícita garante que essa restrição nunca é violada, independentemente do que o modelo estatístico "aprendeu", e pode ser apontada linha por linha numa fiscalização.

## Parte 5 - Auditoria do laudo do fornecedor
 
### 1. "A* com h3=4×Manhattan é comprovadamente ótimo, então a rota é sempre a mais barata."
**Incorreta.** Otimalidade do A* exige heurística admissível; h3 não é (Parte 3.2). Na nossa semente, h3 devolveu custo 31 contra o ótimo real de 28 (Parte 3.1) - 10,71% mais caro, não "sempre a mais barata".
 
### 2. "Substituir BFS por A* caiu 38% o custo. Isso prova que a heurística melhora a solução."
**Enganosa.** A queda vem de considerar custo, não da heurística: BFS→UCS (sem heurística nenhuma) já cai 49,1% (55→28, Parte 2.2). A* com h2 dá o mesmo custo da UCS (28) - a heurística só reduz nós expandidos (113→54), não melhora a rota.
 
### 3. "99% de sensibilidade, então 99% dos apontados estão infestados."
**Incorreta.** Confunde sensibilidade com VPP. Com nossos parâmetros, VPP real = 47,99% (Parte 4.3a) - menos da metade do alegado.
 
### 4. "Dois positivos seguidos levam a confiança pra além de 99%."
**Incorreta mesmo no melhor caso.** Atualização bayesiana sequencial com nossos números dá 96,82% assumindo testes independentes - e mesmo sensor, mesmo talhão, near-simultâneo tende a ter erros correlacionados, então o real fica ainda mais abaixo.
 
### 5. "DFS gasta muito menos memória, e como o ambiente é estático e observável, ela basta."
**Incorreta nas duas partes.** Na Parte 2.2, a fronteira máxima da DFS (47) foi *maior* que a da UCS (22) - o oposto do alegado. E estático/observável são propriedades do ambiente, não justificam a escolha do algoritmo - o bônus da Parte 3.4 mostra a mesma DFS devolvendo rota 3,5× pior que o ótimo.