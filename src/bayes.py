"""
bayes.py - Parte 4.3: P(infestado | sensor positivo) e custo operacional
dos falsos positivos, usando parametros_sensor(matricula).

Uso: python src/bayes.py <matricula>
"""


def vpp(prevalencia, sensibilidade, taxa_falso_positivo):
    """Valor preditivo positivo: P(infestado | positivo), via Bayes."""
    p_inf = prevalencia
    p_sao = 1 - prevalencia
    numerador = sensibilidade * p_inf
    denominador = numerador + taxa_falso_positivo * p_sao
    return numerador / denominador


def relatorio_bayes(params, minutos_por_inspecao=12):
    prevalencia = params["prevalencia"]
    sensibilidade = params["sensibilidade"]
    fpr = params["taxa_falso_positivo"]
    talhoes_sem = params["talhoes_por_semana"]

    # (a) VPP
    p_inf_dado_pos = vpp(prevalencia, sensibilidade, fpr)

    # (b) a cada 100 alertas, quantos são falsos
    falsos_a_cada_100 = round((1 - p_inf_dado_pos) * 100, 1)

    # (c) alertas falsos/semana e horas perdidas/semana
    p_sao = 1 - prevalencia
    p_positivo = sensibilidade * prevalencia + fpr * p_sao
    alertas_totais_semana = p_positivo * talhoes_sem
    alertas_falsos_semana = (1 - p_inf_dado_pos) * alertas_totais_semana
    horas_perdidas_semana = alertas_falsos_semana * minutos_por_inspecao / 60

    # (d) sensibilidade -> 99.9%, mesma FPR
    novo_vpp = vpp(prevalencia, 0.999, fpr)

    return {
        "parametros": params,
        "P(infestado|positivo)": round(p_inf_dado_pos, 4),
        "falsos_a_cada_100_alertas": falsos_a_cada_100,
        "alertas_totais_por_semana": round(alertas_totais_semana, 1),
        "alertas_falsos_por_semana": round(alertas_falsos_semana, 1),
        "horas_perdidas_por_semana": round(horas_perdidas_semana, 2),
        "novo_VPP_com_sensibilidade_99_9pct": round(novo_vpp, 4),
    }


if __name__ == "__main__":
    import sys
    from gerador_pomar import parametros_sensor

    m = int(sys.argv[1]) if len(sys.argv) > 1 else 24114034
    params = parametros_sensor(m)
    r = relatorio_bayes(params)
    for k, v in r.items():
        print(f"{k}: {v}")