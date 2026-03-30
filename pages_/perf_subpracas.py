import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import fmt_horas

def hms(s):
    try:
        p = str(s).split(":")
        return int(p[0]) + int(p[1])/60 + int(p[2])/3600
    except:
        return 0.0

df_perf = st.session_state.get("df_perf")
inicio  = st.session_state.get("inicio")
fim     = st.session_state.get("fim")

st.markdown("""
    <div class='page-header'>
        <h2>🏙️ Performance por Subpraça</h2>
        <p>Comparativo de horas, rotas e entregadores por região</p>
    </div>""", unsafe_allow_html=True)

mask = (df_perf["data_do_periodo"] >= inicio) & (df_perf["data_do_periodo"] <= fim)
df   = df_perf[mask].copy()
df["horas_online"] = df["tempo_disponivel_absoluto"].apply(hms)
df["sub_praca"]    = df["sub_praca"].fillna("Livre (São Paulo)")

st.caption(f"📅 Período: {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}")

# ── Consolidado por subpraça ───────────────────────────────────────────────
sub = df.groupby("sub_praca").agg(
    horas=("horas_online", "sum"),
    ofertadas=("numero_de_corridas_ofertadas", "sum"),
    aceitas=("numero_de_corridas_aceitas", "sum"),
    completas=("numero_de_corridas_completadas", "sum"),
    rejeitadas=("numero_de_corridas_rejeitadas", "sum"),
    entregadores=("id_da_pessoa_entregadora", "nunique"),
).reset_index()
sub["pct_aceitas"]   = (sub["aceitas"]   / sub["ofertadas"].replace(0, float("nan")) * 100).fillna(0)
sub["pct_completas"] = (sub["completas"] / sub["aceitas"].replace(0, float("nan"))   * 100).fillna(0)
sub = sub.sort_values("horas", ascending=False)

# ── Seletor de subpraça ────────────────────────────────────────────────────
subpracas_lista = ["Todas"] + sub["sub_praca"].tolist()
sel = st.selectbox("🔎 Filtrar por subpraça", subpracas_lista, key="sel_sub")

if sel != "Todas":
    sub_view = sub[sub["sub_praca"] == sel]
else:
    sub_view = sub

# ── KPIs gerais ───────────────────────────────────────────────────────────
st.markdown("### 📊 Visão Consolidada")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Horas Online",  fmt_horas(sub_view["horas"].sum()))
k2.metric("Rotas Ofertadas",     f"{int(sub_view['ofertadas'].sum()):,}")
k3.metric("Rotas Completas",     f"{int(sub_view['completas'].sum()):,}")
k4.metric("Entregadores Únicos", f"{int(sub_view['entregadores'].sum()):,}")

st.markdown("---")

# ── Gráficos comparativos ─────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Horas Online por Subpraça")
    fig1 = px.bar(
        sub_view.sort_values("horas"), x="horas", y="sub_praca",
        orientation="h", text_auto=".0f",
        color="horas", color_continuous_scale=["#bfdbfe", "#1d4ed8"],
        labels={"horas": "Horas Online", "sub_praca": "Subpraça"},
    )
    fig1.update_layout(
        height=max(300, len(sub_view) * 44),
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("#### % Rotas Completas por Subpraça")
    fig2 = px.bar(
        sub_view.sort_values("pct_completas"), x="pct_completas", y="sub_praca",
        orientation="h", text_auto=".1f",
        color="pct_completas",
        color_continuous_scale=["#fecaca", "#16a34a"],
        range_color=[0, 100],
        labels={"pct_completas": "% Completas", "sub_praca": "Subpraça"},
    )
    fig2.update_layout(
        height=max(300, len(sub_view) * 44),
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Evolução semanal da subpraça selecionada ──────────────────────────────
if sel != "Todas":
    st.markdown(f"---\n### 📈 Evolução Semanal — {sel}")
    df_sub = df[df["sub_praca"] == sel].copy()
    df_sub["semana"] = df_sub["data_do_periodo"].dt.to_period("W").dt.start_time
    semanal_sub = df_sub.groupby("semana").agg(
        horas=("horas_online", "sum"),
        completas=("numero_de_corridas_completadas", "sum"),
        aceitas=("numero_de_corridas_aceitas", "sum"),
        rejeitadas=("numero_de_corridas_rejeitadas", "sum"),
        entregadores=("id_da_pessoa_entregadora", "nunique"),
    ).reset_index()

    c1, c2 = st.columns(2)
    with c1:
        fig3 = px.area(semanal_sub, x="semana", y="horas",
                       labels={"semana":"Semana","horas":"Horas Online"},
                       color_discrete_sequence=["#3b82f6"])
        fig3.update_layout(height=240, margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(gridcolor="#f0f0f0"))
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        fig4 = px.line(semanal_sub, x="semana",
                       y=["completas","aceitas","rejeitadas"],
                       markers=True,
                       labels={"semana":"Semana","value":"Rotas","variable":"Tipo"},
                       color_discrete_map={
                           "completas": "#10b981",
                           "aceitas":   "#3b82f6",
                           "rejeitadas":"#ef4444",
                       })
        fig4.update_layout(height=240, margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           legend=dict(orientation="h",y=1.1),
                           yaxis=dict(gridcolor="#f0f0f0"))
        st.plotly_chart(fig4, use_container_width=True)

    # Top entregadores da subpraça
    st.markdown(f"#### 🏆 Top Entregadores em {sel}")
    top_sub = (df_sub.groupby("pessoa_entregadora").agg(
        horas=("horas_online","sum"),
        completas=("numero_de_corridas_completadas","sum"),
    ).sort_values("completas", ascending=False).head(15).reset_index())
    top_sub.columns = ["Entregador","Horas Online","Rotas Completas"]
    top_sub["Horas Online"] = top_sub["Horas Online"].apply(lambda x: f"{x:.1f}h")
    st.dataframe(top_sub, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Tabela consolidada ────────────────────────────────────────────────────
st.markdown("### 📋 Tabela Completa")
tab = sub_view.copy()
tab["horas"]         = tab["horas"].apply(lambda x: f"{x:,.0f}h")
tab["pct_aceitas"]   = tab["pct_aceitas"].apply(lambda x: f"{x:.1f}%")
tab["pct_completas"] = tab["pct_completas"].apply(lambda x: f"{x:.1f}%")
tab.columns = ["Subpraça","Horas Online","Ofertadas","Aceitas","Completas",
               "Rejeitadas","Entregadores","% Aceitas","% Completas"]
st.dataframe(tab, use_container_width=True, hide_index=True)
