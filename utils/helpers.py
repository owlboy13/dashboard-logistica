import streamlit as st


def fmt_brl(valor: float) -> str:
    """Formata número como moeda brasileira: R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(valor: float) -> str:
    """Formata como percentual: 36,0%"""
    return "{valor * 100:.1f}%"


def fmt_horas(horas: float) -> str:
    """Converte horas decimais para formato legível: 1h 30min"""
    h = int(horas)
    m = int((horas - h) * 60)
    return f"{h}h {m:02d}min"


def kpi_card(label: str, valor: str, delta: str = None, help: str = None):
    """Renderiza um card de KPI usando st.metric."""
    st.metric(label=label, value=valor, delta=delta, help=help)


def alerta_sla(criterios_atingidos: int, percentual: float):
    """Exibe badge colorido com status do SLA."""
    if criterios_atingidos == 3:
        st.success(f"✅ SLA: {criterios_atingidos}/3 critérios atingidos — Percentual Variável: {fmt_pct(percentual)}")
    elif criterios_atingidos == 2:
        st.warning(f"⚠️ SLA: {criterios_atingidos}/3 critérios atingidos — Percentual Variável: {fmt_pct(percentual)}")
    else:
        st.error(f"🚨 SLA: {criterios_atingidos}/3 critérios atingidos — Percentual Variável: {fmt_pct(percentual)}")


def sidebar_filtro_data(df_financeiro, df_performance):
    """
    Filtro de calendário global na sidebar.
    Retorna (data_inicio, data_fim) como Timestamps.
    """
    import pandas as pd

    # Determina o range disponível nos dados
    min_fin = df_financeiro["data_do_lancamento_financeiro"].min()
    max_fin = df_financeiro["data_do_lancamento_financeiro"].max()
    min_pf = df_performance["data_do_periodo"].min()
    max_pf = df_performance["data_do_periodo"].max()

    data_min = min(min_fin, min_pf).date()
    data_max = max(max_fin, max_pf).date()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Filtro de Período")
    inicio = st.sidebar.date_input("De", value=data_min, min_value=data_min, max_value=data_max, key="filtro_inicio")
    fim = st.sidebar.date_input("Até", value=data_max, min_value=data_min, max_value=data_max, key="filtro_fim")

    if inicio > fim:
        st.sidebar.error("Data inicial não pode ser maior que a final.")
        fim = data_max

    return pd.Timestamp(inicio), pd.Timestamp(fim)
