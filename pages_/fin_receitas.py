import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import fmt_brl

DESC_FRANQUIA = {"Franquia XY", "XY", "FREQUENCIA - APR FRANQUIA", "FREQUENCIA"}
DESC_FEE      = {"Percentual atingido de rotas completas", "Percentual atingido de hora online"}

def _cat(df):
    df = df.copy()
    df["categoria"] = "Entregadores"
    df.loc[df["descricao"].isin(DESC_FRANQUIA), "categoria"] = "Franquia"
    df.loc[df["descricao"].isin(DESC_FEE),      "categoria"] = "Fee Franquia"
    return df

df_fin = st.session_state.get("df_fin")
inicio = st.session_state.get("inicio")
fim = st.session_state.get("fim")

st.markdown("""
    <div class='page-header'>
        <h2>📥 Receitas Detalhadas</h2>
        <p>Breakdown completo de faturamento por tipo e entregador</p>
    </div>""", unsafe_allow_html=True)

mask = (df_fin["data_do_periodo_de_referencia"] >= inicio) & \
       (df_fin["data_do_periodo_de_referencia"] <= fim)
df = _cat(df_fin[mask])

# ── KPIs ──────────────────────────────────────────────────────────────────
total = df["valor"].sum()
por_cat = df.groupby("categoria")["valor"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de Receitas",    fmt_brl(total))
c2.metric("Entregadores",         fmt_brl(por_cat.get("Entregadores", 0)))
c3.metric("Fee da Franquia",      fmt_brl(por_cat.get("Fee Franquia",  0)))
c4.metric("Receita Franquia",     fmt_brl(por_cat.get("Franquia",      0)))

st.markdown("---")

# ── Composição de receitas (pizza) ────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Composição das Receitas")
    pizza = df.groupby("categoria")["valor"].sum().reset_index()
    fig = px.pie(pizza, values="valor", names="categoria", hole=0.45,
                 color_discrete_sequence=["#3b82f6","#10b981","#f59e0b","#8b5cf6"])
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(height=320, margin=dict(t=10,b=10,l=10,r=10),
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Receita por Tipo de Lançamento")
    por_desc = (df.groupby("descricao")["valor"].sum()
                  .sort_values(ascending=False).head(12).reset_index())
    por_desc.columns = ["Descrição","Valor"]
    fig2 = px.bar(por_desc, x="Valor", y="Descrição", orientation="h",
                  text_auto=".2s",
                  color="Valor", color_continuous_scale=["#bfdbfe","#1d4ed8"])
    fig2.update_layout(height=320, margin=dict(t=10,b=10,l=10,r=10),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Top entregadores por faturamento ──────────────────────────────────────
st.markdown("#### 🏆 Top 20 Entregadores por Faturamento")
top = (df[df["categoria"]=="Entregadores"]
       .groupby("recebedor")["valor"].sum()
       .sort_values(ascending=False).head(20).reset_index())
top.columns = ["Entregador","Faturamento"]

fig3 = px.bar(top, x="Faturamento", y="Entregador", orientation="h",
              text_auto=".2s",
              color="Faturamento", color_continuous_scale=["#bfdbfe","#1e40af"])
fig3.update_layout(height=600, margin=dict(t=10,b=10,l=10,r=10),
                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                   coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── Tabela completa filtrável ──────────────────────────────────────────────
st.markdown("#### 🔍 Lançamentos Detalhados")

col_f1, col_f2 = st.columns(2)
with col_f1:
    cats = ["Todas"] + sorted(df["categoria"].unique().tolist())
    cat_sel = st.selectbox("Categoria", cats, key="rec_cat")
with col_f2:
    desc_opts = ["Todas"] + sorted(df["descricao"].dropna().unique().tolist())
    desc_sel = st.selectbox("Tipo de lançamento", desc_opts, key="rec_desc")

df_view = df.copy()
if cat_sel  != "Todas": df_view = df_view[df_view["categoria"] == cat_sel]
if desc_sel != "Todas": df_view = df_view[df_view["descricao"] == desc_sel]

df_show = df_view[["data_do_periodo_de_referencia","recebedor","subpraca",
                    "descricao","valor","categoria"]].copy()
df_show.columns = ["Data","Entregador","Subpraça","Tipo","Valor","Categoria"]
df_show["Data"]  = df_show["Data"].dt.strftime("%d/%m/%Y")
df_show["Valor"] = df_show["Valor"].apply(fmt_brl)

st.caption(f"{len(df_show):,} lançamentos exibidos | Total: {fmt_brl(df_view['valor'].sum())}")
st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)
