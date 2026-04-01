import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import fmt_brl, fmt_pct, alerta_sla

# ── Constantes de categorização ───────────────────────────────────────────
DESC_FRANQUIA   = {"Franquia XY", "XY", "FREQUENCIA - APR FRANQUIA", "FREQUENCIA"}
DESC_FEE        = {"Percentual atingido de rotas completas", "Percentual atingido de hora online"}
DESC_GORJETA    = {"Gorjeta", "UNPAID_TIPS - pagamento de gorjetas retidas",
                   "Lancamento Gorjetas nao repassadas"}

COR_POSITIVO = "#1a9e6e"
COR_NEGATIVO = "#e05252"
COR_NEUTRO   = "#3b82f6"
COR_AVISO    = "#f59e0b"

def _categorizar(df):
    df = df.copy()
    df["categoria"] = "entregador"
    df.loc[df["descricao"].isin(DESC_FRANQUIA), "categoria"] = "franquia"
    df.loc[df["descricao"].isin(DESC_FEE),      "categoria"] = "fee_franquia"
    df.loc[df["descricao"].isin(DESC_GORJETA),  "categoria"] = "gorjeta"
    return df

def _gauge(valor_pct, meta, titulo, cor):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor_pct,
        number={"suffix": "%", "font": {"size": 22}},
        title={"text": titulo, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": cor},
            "steps": [
                {"range": [0, meta * 0.8], "color": "#fce8e8"},
                {"range": [meta * 0.8, meta], "color": "#fef3cd"},
                {"range": [meta, 100], "color": "#d1fae5"},
            ],
            "threshold": {
                "line": {"color": "#374151", "width": 3},
                "thickness": 0.8,
                "value": meta,
            },
        },
    ))
    fig.update_layout(
        height=200, margin=dict(t=40, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# ── Render ─────────────────────────────────────────────────────────────────
df_fin  = st.session_state.get("df_fin")
df_perf = st.session_state.get("df_perf")
df_base = st.session_state.get("df_base")
inicio  = st.session_state.get("inicio")
fim     = st.session_state.get("fim")

st.markdown("""
    <div class='page-header'>
        <h2>💰 Visão Geral Financeira</h2>
        <p>Receitas, SLA e Percentual Variável da Franquia</p>
    </div>""", unsafe_allow_html=True)

# Filtra período
mask = (df_fin["data_do_periodo_de_referencia"] >= inicio) & \
       (df_fin["data_do_periodo_de_referencia"] <= fim)
df = _categorizar(df_fin[mask])

periodo_str = f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
st.caption(f"📅 Período: {periodo_str} — {len(df):,} lançamentos")

# ── KPIs principais ────────────────────────────────────────────────────────
fat_entregadores = df[df["categoria"] == "entregador"]["valor"].sum()
fat_franquia = df[df["categoria"] == "franquia"]["valor"].sum()
fee_franquia = df[df["categoria"] == "fee_franquia"]["valor"].sum()
gorjetas = df[df["categoria"] == "gorjeta"]["valor"].sum()
fat_bruto = fat_entregadores + fat_franquia + fee_franquia + gorjetas
fat_sem_franquia = fat_entregadores + gorjetas

st.markdown("### 📊 Faturamento")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento Bruto", fmt_brl(fat_bruto))
c2.metric("Faturamento Entregadores", fmt_brl(fat_sem_franquia))
c3.metric("Receita da Franquia", fmt_brl(fee_franquia))
c4.metric("Gorjetas", fmt_brl(gorjetas))

st.markdown("---")

# ── SLA ────────────────────────────────────────────────────────────────────
st.markdown("### 🎯 SLA — Indicadores de Nível de Serviço")

df_sla = df[df["atingido"].notna()].copy()

if df_sla.empty:
    st.warning("Sem dados de SLA no período selecionado.")
else:
    # Último período SLA disponível
    ult = df_sla.sort_values("data_do_periodo_de_referencia").iloc[-1]
    criterios_atingidos = sum([
        1 if ult["percentual_de_tempo_disponivel"] >= ult["criterio_tempo_disponivel"] else 0,
        1 if ult["percentual_de_aceitacao"]        >= ult["criterio_rotas_aceitas"]    else 0,
        1 if ult["percentual_de_conclusao"]        >= ult["criterio_rotas_concluidas"] else 0,
    ])
    pct_variavel = {3: 0.36, 2: 0.33, 1: 0.30, 0: 0.28}[criterios_atingidos]

    alerta_sla(criterios_atingidos, pct_variavel)

    g1, g2, g3 = st.columns(3)
    with g1:
        cor = COR_POSITIVO if ult["percentual_de_tempo_disponivel"] >= 80 else COR_NEGATIVO
        st.plotly_chart(_gauge(
            float(ult["percentual_de_tempo_disponivel"]), 80,
            "Horas Online ≥ 80%", cor), use_container_width=True, key="g1")
        st.caption(f"Meta: 80% | Realizado: {ult['percentual_de_tempo_disponivel']:.1f}%")

    with g2:
        cor = COR_POSITIVO if ult["percentual_de_aceitacao"] >= 90 else COR_NEGATIVO
        st.plotly_chart(_gauge(
            float(ult["percentual_de_aceitacao"]), 90,
            "Taxa de Aceitação ≥ 90%", cor), use_container_width=True, key="g2")
        st.caption(f"Meta: 90% | Realizado: {ult['percentual_de_aceitacao']:.1f}%")

    with g3:
        cor = COR_POSITIVO if ult["percentual_de_conclusao"] >= 95 else COR_NEGATIVO
        st.plotly_chart(_gauge(
            float(ult["percentual_de_conclusao"]), 95,
            "Rotas Completas ≥ 95%", cor), use_container_width=True, key="g3")
        st.caption(f"Meta: 95% | Realizado: {ult['percentual_de_conclusao']:.1f}%")

    # Tabela histórico SLA
    with st.expander("📋 Histórico de SLA por período"):
        hist = df_sla.groupby("data_do_periodo_de_referencia").agg(
            pct_tempo=("percentual_de_tempo_disponivel","mean"),
            pct_aceitacao=("percentual_de_aceitacao","mean"),
            pct_conclusao=("percentual_de_conclusao","mean"),
            atingido=("atingido","mean"),
        ).reset_index()
        hist.columns = ["Data","% Tempo Online","% Aceitação","% Conclusão","% Variável"]
        hist["Data"] = hist["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(hist, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Faturamento por subpraça ───────────────────────────────────────────────
st.markdown("### 🗺️ Faturamento por Região")
fat_subpraca = (
    df.groupby("subpraca")["valor"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
fat_subpraca.columns = ["Subpraça", "Faturamento"]

col_graf, col_tab = st.columns([2, 1])
with col_graf:
    fig = px.bar(
        fat_subpraca, x="Faturamento", y="Subpraça",
        orientation="h", text_auto=".2s",
        color="Faturamento",
        color_continuous_scale=["#c7e9f5", "#0369a1"],
    )
    fig.update_traces(textfont_size=11)
    fig.update_layout(
        height=max(300, len(fat_subpraca) * 42),
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_tab:
    fat_subpraca["Faturamento"] = fat_subpraca["Faturamento"].apply(fmt_brl)
    fat_subpraca["% Total"] = (
        df.groupby("subpraca")["valor"].sum() /
        df["valor"].sum() * 100
    ).sort_values(ascending=False).reset_index()[["valor"]].rename(
        columns={"valor": "% Total"}
    )["% Total"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(fat_subpraca, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Evolução mensal ────────────────────────────────────────────────────────
st.markdown("### 📈 Evolução Mensal do Faturamento")
df["mes"] = df["data_do_periodo_de_referencia"].dt.to_period("M").astype(str)
evolucao = df.groupby(["mes","categoria"])["valor"].sum().reset_index()
fig2 = px.bar(
    evolucao, x="mes", y="valor", color="categoria",
    barmode="stack", text_auto=".2s",
    color_discrete_map={
        "entregador":  "#3b82f6",
        "fee_franquia":"#10b981",
        "franquia":    "#f59e0b",
        "gorjeta":     "#8b5cf6",
    },
    labels={"mes":"Mês","valor":"Valor (R$)","categoria":"Categoria"},
)
fig2.update_layout(
    height=320, margin=dict(t=10, b=10, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig2, use_container_width=True)
