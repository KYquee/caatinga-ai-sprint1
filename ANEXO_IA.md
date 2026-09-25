# ANEXO_IA.md - Registro de Uso de Inteligência Artificial

> **Atividade Prática Avaliativa - Sprint 1 do Projeto Caatinga.AI**  
> **Disciplina:** Inteligência Artificial - Prof. Ronierison Maciel - UniRios - 2026.2  
> **Dupla:** Matheus Caique e Arthur (Matrícula semente: `24114034`)

---

## A.1 Ferramentas Utilizadas e Partes do Trabalho

| Ferramenta | Provedor / Modelo | Onde foi utilizada |
|---|---|---|
| **Antigravity IDE / Gemini** | Google DeepMind (Gemini 3.8 Flash) | • **Parte 2:** Auxílio na estruturação das classes de busca cega e no desenho do script de medição de memória com `tracemalloc`.<br>• **Parte 3:** Implementação inicial do algoritmo $A^*$, geração de boilerplate das heurísticas $h_1, h_2, h_3$, estruturação da função de vizinhança da Busca Local (1-swap) e rascunho do contraexemplo em grade reduzida para a DFS.<br>• **Documentação:** Formatação das tabelas comparativas em Markdown e auxílio nas demonstrações formais de admissibilidade. |

---

## A.2 Prompts na Íntegra e Respostas Recebidas

### Prompt 1: Implementação e Análise da Busca Informada (Parte 3)

**Prompt enviado:**
```text
Parte 3 - Busca informada (1,5 ponto)
3.1 Implemente o A* e rode-o com três heurísticas:
- h1(n) = 0
- h2(n) = distância de Manhattan até o objetivo
- h3(n) = 4 × distância de Manhattan até o objetivo
Heurística Custo da rota Nós expandidos Admissível? (prove)
h1
h2
h3
3.2 Para h2, demonstre a admissibilidade usando o custo mínimo de entrada em um talhão.
Para h3, exiba um par de talhões concretos do seu pomar em que ela superestima o custo real restante. Não basta dizer "superestima": aponte as coordenadas e os dois números.
3.3 - A pergunta que separa quem rodou de quem entendeu. Compare o custo devolvido por h3 com o do UCS.
- Se ficou igual: isso prova que h3 é admissível? Responda sim ou não e justifique formalmente.
- Se ficou maior: calcule a perda percentual e diga quantos nós de expansão você "comprou" com ela.
Em ambos os casos, responda: em que situação de negócio da cooperativa valeria a pena trocar garantia de otimalidade por velocidade? Dê uma condição verificável (ex.: um limite de tempo, um custo por consulta), não uma opinião.
```

**Trecho principal da resposta recebida do assistente:**
```text
Para implementar o A*, definimos a função de avaliação f(n) = g(n) + h(n).
Com a matrícula 24114034:
- h1 (zero): Custo 28, 113 nós expandidos. Admissível trivilamente pois h(n) = 0 <= h*(n).
- h2 (Manhattan): Custo 28, 54 nós expandidos. Admissível pois cada passo custa no mínimo 1 (c_min = 1), e Manhattan é o número mínimo de passos ortogonais, logo h2(n) <= h*(n).
- h3 (4xManhattan): Custo 31, 25 nós expandidos. Não admissível pois superestima.
No talhão (0,0), h3 dá 4 * 22 = 88, mas o custo real restante h* é 28 (superestima em +60).
No talhão (10,11), h3 dá 4 * 1 = 4, mas o custo real para entrar em (11,11) é 1 (superestima em +3).
O custo de h3 (31) ficou maior que o da UCS (28). A perda percentual foi (31-28)/28 = 10,71%.
Com essa perda, compramos uma redução de 113 para 25 nós (88 nós a menos).
Mesmo se tivesse ficado igual, NÃO provaria admissibilidade, pois a definição exige h(n) <= h*(n) para TODOS os estados, e não apenas para o caminho percorrido nesta semente específica.
Condição de negócio: pomar em grande escala (n >= 1000) e prazo de tempo real rigoroso no hardware embarcado (ex: deadline <= 200 ms por planejamento de rota).
```

---

### Prompt 2: Contraexemplo construído à mão para o Bônus da Liga de IA

**Prompt enviado:**
```text
Bônus - Liga de IA (+0,3): construa à mão um pomar de no máximo 8 × 8 em que a sua DFS (com a ordem de vizinhos que você declarou: Norte, Sul, Oeste, Leste) devolva uma rota com custo maior que o dobro do ótimo. Entregue a grade, a rota devolvida, a rota ótima e os dois custos. O ponto é pela construção do contraexemplo, não pela sorte.
```

**Trecho principal da resposta recebida do assistente:**
```text
Podemos explorar o fato de que a ordem de vizinhos declarada é Norte, Sul, Oeste, Leste.
Como o Norte em (0,0) está fora da grade, a DFS sempre explorará o Sul (1,0) antes do Leste (0,1).
Construímos uma grade 4x4 onde:
- O caminho pelo Leste é formado por carreadores firmes ('.' com custo 1) direto para o objetivo (3,3): custo 6.
- O caminho pelo Sul é um corredor de solo encharcado ('~' com custo 4) cercado por paredes ('#'), forçando a DFS a mergulhar pelo terreno caro: custo 21.

Grade:
. . . .
~ # # .
~ ~ ~ .
# # ~ .

DFS devolve rota: (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2) -> (3,2) -> (3,3) | Custo = 21 (passos = 6)
UCS devolve rota: (0,0) -> (0,1) -> (0,2) -> (0,3) -> (1,3) -> (2,3) -> (3,3) | Custo = 6 (passos = 6)
Razão = 21 / 6 = 3,5x (maior que o dobro).
```

---

## A.3 Erro / Imprecisão que o Assistente Cometeu e Evidência Experimental

### O que o assistente afirmou:
Ao propor a implementação inicial do algoritmo $A^*$, o assistente sugeriu a seguinte lógica de poda para os nós fechados:

```python
# Sugestão inicial incorreta do assistente:
if viz in fechados:
    continue
```
O assistente argumentou textualmente:  
*"Como a grade possui pesos positivos e a heurística de Manhattan é consistente, qualquer estado inserido em `fechados` já foi alcançado pelo seu caminho mais curto possível, de modo que nós já fechados nunca precisam ser revisitados ou reabertos."*

### Por que essa afirmação é incorreta e imprecisa:
Essa propriedade de fechar definitivamente os nós **só se sustenta se a heurística for comprovadamente consistente** (o que ocorre com $h_2$).  
Contudo, o próprio enunciado da atividade exige rodar o mesmo algoritmo $A^*$ com a heurística **$h_3(n) = 4 \times \text{Manhattan}(n)$**, que **não é admissível e muito menos consistente**.  
Sob heurísticas inconsistentes ou infladas, um estado pode ser expandido prematuramente por um caminho aparentemente promissor (guiado pelo valor inflado de $h$), entrando no conjunto `fechados`. Se o algoritmo descartar sumariamente nós fechados sem permitir reabertura quando um $g(n)$ menor é descoberto mais tarde, ele pode perder permanentemente rotas factíveis ou devolver caminhos com custo arbitrariamente distante da referência.

### A evidência do experimento que o desmentiu:
Para demonstrar o impacto prático dessa afirmação, executamos um teste comparativo direto na grade da semente de aferição (`20231045`) e na semente oficial (`24114034`), contrastando a versão com reabertura de nós (`reabrir=True`) versus a versão estrita sem reabertura (`reabrir=False`):

1. **Na calibração da semente `20231045`:**
   Ao rodar uma variação onde o teste de objetivo é feito na geração (outro vício comum sugerido por assistentes) ou onde nós em rotas concorrentes com heurística agressiva são fechados sem atualização de $g$, o custo da rota com $h_3$ divergiu de forma espúria e a contagem de nós expandidos caiu abaixo do comportamento formal esperado pela teoria de grafos de Russell & Norvig.
2. **Correção implementada no código final (`src/buscas.py`):**
   Garantimos que o algoritmo reabra nós caso um caminho de custo estritamente menor seja encontrado:
   ```python
   if viz not in g_score or novo_g < g_score[viz]:
       g_score[viz] = novo_g
       veio_de[viz] = atual
       if reabrir and viz in fechados:
           fechados.remove(viz)  # Reabre o nó para garantir correção sob h inconsistente
       novo_f = novo_g + h_func(viz, objetivo)
       heapq.heappush(fronteira, (novo_f, next(contador), viz))
   ```
Essa necessidade foi explicitamente confirmada na Seção 12 (Armadilha 4) do edital: *"A\* que não reabre nós pode devolver rota mais cara mesmo com heurística admissível, se ela não for consistente. Diga no README qual das duas versões você implementou."*

---

## A.4 O que Aprendemos após Rodar o Código

> *"Depois de rodar o código, ficou evidente que a velocidade surpreendente de uma heurística inflada como $h_3$ não resulta de nenhuma 'compreensão superior' do mapa, mas sim de uma agressividade cega que descarta alternativas em busca da meta, 'comprando' 77,8% menos nós às custas de degradar a rota ótima em 10,7% — uma troca de engenharia que a teoria descreve em fórmulas, mas que só a execução concreta no pomar torna tangível."*
