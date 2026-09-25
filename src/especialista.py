"""
especialista.py - Parte 4.1/4.2: mini sistema especialista para
manejo de talhões, com encadeamento para trás e rastro de explicação.

Uso: python src/especialista.py
"""


class Regra:
    def __init__(self, nome, premissas, conclusao):
        self.nome = nome
        self.premissas = premissas   # lista de fatos/subconclusões
        self.conclusao = conclusao

    def __repr__(self):
        return f"SE {' E '.join(self.premissas)} ENTAO {self.conclusao}"


# 4.1 - Base de regras (7, dentro da faixa de 5 a 8 pedida)
REGRAS = [
    Regra("R1",
          ["armadilha_positiva", "umidade_alta", "dias_desde_pulverizacao>14"],
          "inspecionar_prioridade_alta"),
    Regra("R2",
          ["armadilha_positiva", "umidade_baixa"],
          "inspecionar_prioridade_media"),
    Regra("R3",
          ["folhas_amareladas", "solo_encharcado"],
          "risco_fungo"),
    Regra("R4",
          ["risco_fungo", "temperatura_alta"],
          "inspecionar_prioridade_alta"),
    Regra("R5",
          ["sem_sinais_visuais", "armadilha_negativa"],
          "manejo_rotina"),
    Regra("R6",
          ["inspecionar_prioridade_alta", "talhao_proximo_reservatorio"],
          "acionar_agronomo_presencial"),
    Regra("R7",
          ["dias_desde_pulverizacao>14", "chuva_recente"],
          "reprogramar_pulverizacao"),
]


def encadeamento_para_tras(objetivo, base_fatos, regras=REGRAS, rastro=None, visitando=None):
    """Tenta provar `objetivo` a partir de `base_fatos`. Retorna (provado, rastro)."""
    if rastro is None:
        rastro = []
    if visitando is None:
        visitando = set()

    if objetivo in base_fatos:
        return True, rastro
    if objetivo in visitando:
        return False, rastro

    visitando.add(objetivo)
    for regra in regras:
        if regra.conclusao != objetivo:
            continue
        rastro.append(f"Tentando {regra.nome}: {regra}")
        todas_provadas = True
        for premissa in regra.premissas:
            ok, rastro = encadeamento_para_tras(premissa, base_fatos, regras, rastro, visitando)
            rastro.append(f"  premissa '{premissa}' -> {'OK' if ok else 'FALHOU'}")
            if not ok:
                todas_provadas = False
                break
        if todas_provadas:
            rastro.append(f"=> {regra.nome} disparada: '{objetivo}' PROVADO")
            visitando.discard(objetivo)
            return True, rastro
    rastro.append(f"Nenhuma regra provou '{objetivo}' com os fatos disponíveis")
    visitando.discard(objetivo)
    return False, rastro


def explicar(objetivo, base_fatos, regras=REGRAS):
    provado, rastro = encadeamento_para_tras(objetivo, base_fatos, regras)
    print(f"\n=== Por que '{objetivo}'? (fatos: {sorted(base_fatos)}) ===")
    for linha in rastro:
        print(linha)
    print(f"Conclusão: {'PROVADO' if provado else 'NÃO PROVADO'}")
    return provado


if __name__ == "__main__":
    # --- 4.1: exemplo que dispara diretamente (R1) ---
    base1 = {"armadilha_positiva", "umidade_alta", "dias_desde_pulverizacao>14"}
    explicar("inspecionar_prioridade_alta", base1)

    # --- 4.1: exemplo que encadeia duas regras (R3 -> R4) ---
    base2 = {"folhas_amareladas", "solo_encharcado", "temperatura_alta"}
    explicar("inspecionar_prioridade_alta", base2)

    # -----------------------------------------------------------------
    # 4.2 - Quebrando a própria base
    # -----------------------------------------------------------------
    # Caso legítimo: armadilha positiva + umidade alta, mas ainda dentro da
    # janela segura de pulverização (<=14 dias). Nem R1 (exige >14 dias) nem
    # R2 (exige umidade_baixa) disparam - um talhão com PRAGA CONFIRMADA fica
    # sem manejo algum recomendado. Erro de omissão perigoso.
    base_falha = {"armadilha_positiva", "umidade_alta"}
    print("\n\n### 4.2 - Caso que quebra a base (ANTES da correção) ###")
    explicar("inspecionar_prioridade_alta", base_falha)
    explicar("inspecionar_prioridade_media", base_falha)

    # Regra corretiva: armadilha positiva sozinha já garante ao menos
    # prioridade média, sem contradizer R1/R2 (que continuam valendo para
    # seus casos mais específicos).
    REGRAS_CORRIGIDAS = REGRAS + [
        Regra("R8", ["armadilha_positiva"], "inspecionar_prioridade_media")
    ]
    print("\n### 4.2 - Mesmo caso, DEPOIS da correção (R8 adicionada) ###")
    explicar("inspecionar_prioridade_media", base_falha, REGRAS_CORRIGIDAS)