import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import fmt_brl, fmt_horas, fmt_pct

# ── helpers locais ─────────────────────────────────────────────────────────
def hms(s):
    try:
        p = str(s).split(":")
        return int(p[0]) + int(p[1])/60 + int(p[2])/3600
    except:
        return 0.0

MODAL_LABELS = {
    "MOTORCYCLE":       "Moto",
    "BICYCLE":          "Bicicleta",
    "EBIKE":            "E-Bike",
    "BIKE_IFOOD_PEDAL": "Bike iFood",
}
MODAL_CORES = {
    "Moto":       "#3b82f6",
    "Bicicleta":  "#10b981",
    "E-Bike":     "#f59e0b",
    "Bike iFood": "#8b5cf6",
}

# ── dados ──────────────────────────────────────────────────────────────────
df_base = st.session_state.get("df_base")
df_perf = st.session_state.get("df_perf")
inicio  = st.session_state.get("inicio")
fim     = st.session_state.get("fim")

st.markdown("""
    <div class='page-header'>
        <h2>🚴 Visão Geral da Frota</h2>
        <p>Supply hours, rotas e desempenho operacional</p>
    </div>""", unsafe_allow_html=True)

# Filtra período
mask = (df_perf["data_do_periodo"] >= inicio) & (df_perf["data_do_periodo"] <= fim)
df   = df_perf[mask].copy()
df["horas_online"]    = df["tempo_disponivel_absoluto"].apply(hms)
df["horas_escaladas"] = pd.to_numeric(df["tempo_disponivel_escalado"], errors="coerce").fillna(0)
df["sub_praca"]       = df["sub_praca"].fillna("Livre (São Paulo)")

periodo_str = f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
st.caption(f"📅 Período: {periodo_str}")

# ── Aniversariantes do dia ─────────────────────────────────────────────────
hoje = pd.Timestamp.today()
aniv = df_base[
    (df_base["Data de nascimento"].dt.month == hoje.month) &
    (df_base["Data de nascimento"].dt.day   == hoje.day) &
    (df_base["ativo"].str.lower() == "ativo")
]
if not aniv.empty:
    nomes_aniv = " · ".join(aniv["Nome"].tolist())
    st.success(f"🎂 **Aniversariantes hoje ({hoje.strftime('%d/%m')}):** {nomes_aniv}")

st.markdown("---")

# ── KPIs entregadores ─────────────────────────────────────────────────────
st.markdown("### 👥 Entregadores")
total    = len(df_base)
ativos   = (df_base["ativo"].str.lower() == "ativo").sum()
inativos = (df_base["ativo"].str.lower() == "inativo").sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Cadastrados", total)
c2.metric("Ativos",   ativos,   delta=f"+{ativos}",   delta_color="normal")
c3.metric("Inativos", inativos, delta=f"-{inativos}", delta_color="inverse")
c4.metric("% Ativos", f"{ativos/total*100:.1f}%")

# Gráfico modais
col_modal, col_ativo = st.columns(2)
with col_modal:
    st.markdown("#### Distribuição por Modal")
    modais = df_base["Modal"].map(MODAL_LABELS).fillna(df_base["Modal"])
    modais_cnt = modais.value_counts().reset_index()
    modais_cnt.columns = ["Modal", "Quantidade"]
    fig_modal = px.pie(
        modais_cnt, values="Quantidade", names="Modal", hole=0.45,
        color="Modal", color_discrete_map=MODAL_CORES,
    )
    fig_modal.update_traces(textposition="outside", textinfo="percent+label+value")
    fig_modal.update_layout(
        height=280, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    st.plotly_chart(fig_modal, use_container_width=True)

with col_ativo:
    st.markdown("#### Ativos vs Inativos")
    status_cnt = pd.DataFrame({
        "Status": ["Ativos", "Inativos"],
        "Qtd":    [ativos, inativos],
    })
    fig_status = px.bar(
        status_cnt, x="Status", y="Qtd", text="Qtd",
        color="Status",
        color_discrete_map={"Ativos": "#10b981", "Inativos": "#ef4444"},
    )
    fig_status.update_traces(textposition="outside")
    fig_status.update_layout(
        height=280, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_status, use_container_width=True)

st.markdown("---")

# ── Supply Hours ───────────────────────────────────────────────────────────
st.markdown("### ⏱️ Supply Hours")

total_horas    = df["horas_online"].sum()
total_escalado = df["horas_escaladas"].sum()
pct_supply     = (total_horas / total_escalado * 100) if total_escalado > 0 else 0

s1, s2, s3 = st.columns(3)
s1.metric("Total Horas Online",   fmt_horas(total_horas))
s2.metric("Total Horas Escaladas",fmt_horas(total_escalado))
s3.metric("% Supply Hours",       f"{pct_supply:.1f}%",
          help="Relação entre horas efetivamente online e horas escaladas. Meta: 80%")

# Gauge supply hours
fig_supply = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=pct_supply,
    number={"suffix": "%", "font": {"size": 28}},
    delta={"reference": 80, "suffix": "%", "relative": False},
    title={"text": "Supply Hours — Meta: 80%", "font": {"size": 14}},
    gauge={
        "axis": {"range": [0, 100]},
        "bar":  {"color": "#3b82f6" if pct_supply >= 80 else "#ef4444"},
        "steps": [
            {"range": [0,  64], "color": "#fce8e8"},
            {"range": [64, 80], "color": "#fef3cd"},
            {"range": [80,100], "color": "#d1fae5"},
        ],
        "threshold": {
            "line": {"color": "#374151", "width": 3},
            "thickness": 0.8, "value": 80,
        },
    },
))
fig_supply.update_layout(
    height=240, margin=dict(t=50, b=20, l=40, r=40),
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_supply, use_container_width=True)

# Evolução semanal supply
df["semana"] = df["data_do_periodo"].dt.to_period("W").dt.start_time
semanal = df.groupby("semana").agg(
    horas_online=("horas_online", "sum"),
    horas_escaladas=("horas_escaladas", "sum"),
).reset_index()
semanal["pct_supply"] = (
    semanal["horas_online"] / semanal["horas_escaladas"].replace(0, float("nan")) * 100
).fillna(0)

fig_sem = px.bar(
    semanal, x="semana", y="horas_online",
    labels={"semana": "Semana", "horas_online": "Horas Online"},
    color_discrete_sequence=["#3b82f6"],
    text_auto=".0f",
)
fig_sem.add_scatter(
    x=semanal["semana"], y=semanal["pct_supply"],
    mode="lines+markers", name="% Supply",
    yaxis="y2", line=dict(color="#f59e0b", width=2),
    marker=dict(size=6),
)
fig_sem.update_layout(
    height=280,
    margin=dict(t=10, b=10, l=10, r=60),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis2=dict(overlaying="y", side="right", showgrid=False,
                ticksuffix="%", range=[0, 10]),
    legend=dict(orientation="h", y=1.1),
    yaxis=dict(gridcolor="#f0f0f0"),
)
st.plotly_chart(fig_sem, use_container_width=True)

st.markdown("---")

# ── Rotas ─────────────────────────────────────────────────────────────────
st.markdown("### 🗺️ Rotas")

total_ofertadas  = int(df["numero_de_corridas_ofertadas"].sum())
total_aceitas    = int(df["numero_de_corridas_aceitas"].sum())
total_rejeitadas = int(df["numero_de_corridas_rejeitadas"].sum())
total_completas  = int(df["numero_de_corridas_completadas"].sum())
pct_aceitas    = total_aceitas    / total_ofertadas  * 100 if total_ofertadas  > 0 else 0
pct_completas  = total_completas  / total_aceitas    * 100 if total_aceitas    > 0 else 0
pct_rejeitadas = total_rejeitadas / total_ofertadas  * 100 if total_ofertadas  > 0 else 0

r1, r2, r3, r4 = st.columns(4)
r1.metric("Ofertadas",  f"{total_ofertadas:,}")
r2.metric("Aceitas",    f"{total_aceitas:,}",
          delta=f"{pct_aceitas:.1f}%", delta_color="normal")
r3.metric("Rejeitadas", f"{total_rejeitadas:,}",
          delta=f"{pct_rejeitadas:.1f}%", delta_color="inverse")
r4.metric("Completas",  f"{total_completas:,}",
          delta=f"{pct_completas:.1f}%", delta_color="normal")

# Funil de rotas
col_funil, col_evo = st.columns(2)
with col_funil:
    st.markdown("#### Funil de Rotas")
    fig_funil = go.Figure(go.Funnel(
        y=["Ofertadas", "Aceitas", "Completas"],
        x=[total_ofertadas, total_aceitas, total_completas],
        textinfo="value+percent initial",
        marker=dict(color=["#3b82f6", "#10b981", "#059669"]),
    ))
    fig_funil.update_layout(
        height=280, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_funil, use_container_width=True)

with col_evo:
    st.markdown("#### Evolução Semanal de Rotas")
    semanal_rotas = df.groupby("semana").agg(
        aceitas=("numero_de_corridas_aceitas", "sum"),
        completas=("numero_de_corridas_completadas", "sum"),
        rejeitadas=("numero_de_corridas_rejeitadas", "sum"),
    ).reset_index()
    fig_rotas = px.line(
        semanal_rotas, x="semana",
        y=["aceitas", "completas", "rejeitadas"],
        markers=True,
        labels={"semana": "Semana", "value": "Rotas", "variable": "Tipo"},
        color_discrete_map={
            "aceitas":   "#10b981",
            "completas": "#3b82f6",
            "rejeitadas":"#ef4444",
        },
    )
    fig_rotas.update_layout(
        height=280, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.1),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_rotas, use_container_width=True)

st.markdown("---")

# ── Performance por subpraça ───────────────────────────────────────────────
st.markdown("### 🏙️ Performance por Subpraça")

sub = df.groupby("sub_praca").agg(
    horas=("horas_online", "sum"),
    ofertadas=("numero_de_corridas_ofertadas", "sum"),
    completas=("numero_de_corridas_completadas", "sum"),
    entregadores=("id_da_pessoa_entregadora", "nunique"),
).reset_index()
sub["pct_completas"] = (sub["completas"] / sub["ofertadas"].replace(0, float("nan")) * 100).fillna(0)
sub = sub.sort_values("horas", ascending=False)
sub.columns = ["Subpraça","Horas Online","Ofertadas","Completas","Entregadores","% Completas"]
sub["Horas Online"] = sub["Horas Online"].apply(lambda x: f"{x:,.0f}h")
sub["% Completas"]  = sub["% Completas"].apply(lambda x: f"{x:.1f}%")

st.dataframe(sub, use_container_width=True, hide_index=True)
