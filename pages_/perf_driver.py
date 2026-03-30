import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import fmt_brl, fmt_horas


def hms(s):
    try:
        p = str(s).split(":")
        return int(p[0]) + int(p[1])/60 + int(p[2])/3600
    except Exception:
        return 0.0


DESC_GORJETA = {"Gorjeta", "UNPAID_TIPS - pagamento de gorjetas retidas",
                  "Lancamento Gorjetas nao repassadas"}
DESC_NF = {"Corridas concluidas", "Valor por Hora Online",
                  "Tempo de espera na origem", "ROUTE_WITH_OCCURRENCE",
                  "ADDITIONAL_PER_ROUTE"}
DESC_PROMOCAO = {d for d in [] if "Promoc" in d or "Promo" in d}

# ── dados ──────────────────────────────────────────────────────────────────
df_base = st.session_state.get("df_base")
df_perf = st.session_state.get("df_perf")
df_fin  = st.session_state.get("df_fin")
inicio  = st.session_state.get("inicio")
fim     = st.session_state.get("fim")

st.markdown("""
    <div class='page-header'>
        <h2>👤 Perfil do Entregador</h2>
        <p>Busca individual — performance, financeiro e informações de contato</p>
    </div>""", unsafe_allow_html=True)

# Filtra performance e financeiro pelo período
mask_p = (df_perf["data_do_periodo"] >= inicio) & (df_perf["data_do_periodo"] <= fim)
mask_f = (df_fin["data_do_periodo_de_referencia"] >= inicio) & \
         (df_fin["data_do_periodo_de_referencia"] <= fim)
perf = df_perf[mask_p].copy()
fin  = df_fin[mask_f].copy()
perf["horas_online"] = perf["tempo_disponivel_absoluto"].apply(hms)
perf["sub_praca"]    = perf["sub_praca"].fillna("Livre (São Paulo)")

# ── Busca ──────────────────────────────────────────────────────────────────
col_busca, col_info = st.columns([2, 1])
with col_busca:
    termo = st.text_input(
        "🔍 Buscar entregador",
        placeholder="Digite o nome ou ID...",
        key="busca_driver",
    )

# Filtra candidatos
if termo and len(termo) >= 2:
    t = termo.strip().lower()
    candidatos = df_base[
        df_base["Nome"].str.lower().str.contains(t, na=False) |
        df_base["ID"].str.lower().str.contains(t, na=False)
    ]
else:
    candidatos = pd.DataFrame()

with col_info:
    if not candidatos.empty:
        st.caption(f"{len(candidatos)} entregador(es) encontrado(s)")

# Sem busca
if candidatos.empty:
    if termo and len(termo) >= 2:
        st.warning("Nenhum entregador encontrado. Tente outro nome ou ID.")
    else:
        st.info("Digite pelo menos 2 caracteres para buscar um entregador.")
    st.stop()

# Seleção quando há múltiplos resultados
if len(candidatos) > 1:
    opcoes = candidatos["Nome"].tolist()
    nome_sel = st.selectbox("Selecione o entregador:", opcoes, key="sel_driver")
    driver = candidatos[candidatos["Nome"] == nome_sel].iloc[0]
else:
    driver = candidatos.iloc[0]

driver_id   = driver["ID"]
driver_nome = driver["Nome"]

# ── Card do entregador ────────────────────────────────────────────────────
st.markdown("---")
modal_label = {
    "MOTORCYCLE": "🛵 Moto",
    "BICYCLE": "🚲 Bicicleta",
    "EBIKE": "⚡ E-Bike",
}.get(str(driver.get("Modal", "")), driver.get("Modal", "—"))

ativo_badge = (
    "<span style='background:#d1fae5;color:#065f46;padding:3px 10px;border-radius:20px;font-size:12px;'>✅ Ativo</span>"
    if str(driver.get("ativo", "")).lower() == "ativo"
    else "<span style='background:#fee2e2;color:#991b1b;padding:3px 10px;border-radius:20px;font-size:12px;'>❌ Inativo</span>"
)

nascimento = driver.get("Data de nascimento")
idade_str = ""
if pd.notna(nascimento):
    idade = (pd.Timestamp.today() - pd.Timestamp(nascimento)).days // 365
    idade_str = f"({idade} anos)"

st.markdown(f"""
<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;'>
    <div style='display:flex;align-items:center;gap:16px;'>
        <div style='width:52px;height:52px;border-radius:50%;background:#dbeafe;display:flex;
                    align-items:center;justify-content:center;font-size:20px;'>👤</div>
        <div>
            <h3 style='margin:0;font-size:1.2rem;color:#1e293b;'>{driver_nome}</h3>
            <div style='margin-top:4px;display:flex;gap:8px;flex-wrap:wrap;'>
                {ativo_badge}
                <span style='background:#eff6ff;color:#1d4ed8;padding:3px 10px;
                             border-radius:20px;font-size:12px;'>{modal_label}</span>
            </div>
        </div>
    </div>
    <div style='margin-top:1rem;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;font-size:13px;color:#475569;'>
        <div>📅 Nascimento: <b>{pd.Timestamp(nascimento).strftime("%d/%m/%Y") if pd.notna(nascimento) else "—"}</b> {idade_str}</div>
        <div>📞 Telefone: <b>{driver.get("Telefone","—")}</b></div>
        <div>✉️ E-mail: <b>{driver.get("email","—")}</b></div>
        <div>🪪 CPF: <b>{driver.get("CPF","—")}</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Performance no período ────────────────────────────────────────────────
perf_d = perf[perf["id_da_pessoa_entregadora"] == driver_id]

st.markdown("### 📊 Performance no Período")
if perf_d.empty:
    st.warning("Sem dados de performance para esse entregador no período selecionado.")
else:
    horas_total = perf_d["horas_online"].sum()
    ofertadas = int(perf_d["numero_de_corridas_ofertadas"].sum())
    aceitas = int(perf_d["numero_de_corridas_aceitas"].sum())
    rejeitadas = int(perf_d["numero_de_corridas_rejeitadas"].sum())
    completas = int(perf_d["numero_de_corridas_completadas"].sum())
    pct_aceitas = aceitas / ofertadas * 100 if ofertadas > 0 else 0
    pct_completas = completas / aceitas * 100 if aceitas > 0 else 0

    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Horas Online",   fmt_horas(horas_total))
    p2.metric("Ofertadas",      f"{ofertadas:,}")
    p3.metric("Aceitas",        f"{aceitas:,}",
              delta=f"{pct_aceitas:.1f}%", delta_color="normal")
    p4.metric("Rejeitadas",     f"{rejeitadas:,}",
              delta=f"{rejeitadas:.1f}%" if ofertadas > 0 else "—",
              delta_color="inverse")
    p5.metric("Completas",      f"{completas:,}",
              delta=f"{pct_completas:.1f}%", delta_color="normal")

    # Produção semanal
    st.markdown("#### 📅 Produção Semanal")
    perf_d2 = perf_d.copy()
    perf_d2["semana"] = perf_d2["data_do_periodo"].dt.to_period("W").dt.start_time
    semanal = perf_d2.groupby("semana").agg(
        horas=("horas_online", "sum"),
        completas=("numero_de_corridas_completadas", "sum"),
        aceitas=("numero_de_corridas_aceitas", "sum"),
        rejeitadas=("numero_de_corridas_rejeitadas", "sum"),
    ).reset_index()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig1 = px.bar(semanal, x="semana", y="horas", text_auto=".1f",
                      labels={"semana":"Semana","horas":"Horas Online"},
                      color_discrete_sequence=["#3b82f6"])
        fig1.update_layout(height=240, margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(gridcolor="#f0f0f0"))
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        fig2 = px.bar(semanal, x="semana",
                      y=["completas","aceitas","rejeitadas"],
                      barmode="group",
                      labels={"semana":"Semana","value":"Rotas","variable":"Tipo"},
                      color_discrete_map={
                          "completas": "#10b981",
                          "aceitas":   "#3b82f6",
                          "rejeitadas":"#ef4444",
                      })
        fig2.update_layout(height=240, margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           legend=dict(orientation="h", y=1.1),
                           yaxis=dict(gridcolor="#f0f0f0"))
        st.plotly_chart(fig2, use_container_width=True)

    # Subpraças principais
    st.markdown("#### 🏙️ Subpraças com Mais Atuação")
    subpracas = (perf_d.groupby("sub_praca")["numero_de_corridas_completadas"]
                       .sum().sort_values(ascending=False).reset_index())
    subpracas.columns = ["Subpraça","Rotas Completas"]
    fig_sub = px.bar(subpracas.head(8), x="Rotas Completas", y="Subpraça",
                     orientation="h", text_auto=True,
                     color="Rotas Completas",
                     color_continuous_scale=["#bfdbfe","#1d4ed8"])
    fig_sub.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_sub, use_container_width=True)

st.markdown("---")

# ── Financeiro do entregador ───────────────────────────────────────────────
fin_d = fin[fin["id_da_pessoa_entregadora"] == driver_id]

st.markdown("### 💰 Financeiro no Período")
if fin_d.empty:
    st.warning("Sem lançamentos financeiros para esse entregador no período.")
else:
    nota_fiscal  = fin_d[fin_d["descricao"].isin(DESC_NF)]["valor"].sum()
    gorjeta      = fin_d[fin_d["descricao"].isin(DESC_GORJETA)]["valor"].sum()
    promocoes    = fin_d[fin_d["descricao"].str.contains("Promoc|Promo|promoc|promo", na=False)]["valor"].sum()
    antecipacao  = fin_d[fin_d["descricao"].str.contains("Antecip|antecip", na=False)]["valor"].sum()
    total_repasse= fin_d["valor"].sum()

    f1, f2, f3, f4, f5 = st.columns(5)
    f1.metric("Total Repasse",  fmt_brl(total_repasse))
    f2.metric("Nota Fiscal",    fmt_brl(nota_fiscal))
    f3.metric("Gorjeta",        fmt_brl(gorjeta))
    f4.metric("Promoções",      fmt_brl(promocoes))
    f5.metric("Antecipações",   fmt_brl(antecipacao) if antecipacao > 0 else "R$ 0,00")

    # Histórico de repasses
    with st.expander("📋 Histórico de lançamentos"):
        df_hist = fin_d[["data_do_periodo_de_referencia","descricao","valor","subpraca"]].copy()
        df_hist.columns = ["Data","Descrição","Valor","Subpraça"]
        df_hist["Data"]  = df_hist["Data"].dt.strftime("%d/%m/%Y")
        df_hist["Valor"] = df_hist["Valor"].apply(fmt_brl)
        df_hist = df_hist.sort_values("Data", ascending=False)
        st.dataframe(df_hist, use_container_width=True, hide_index=True, height=320)
