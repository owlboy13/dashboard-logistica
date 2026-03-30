import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import fmt_brl

DESC_FRANQUIA = {"Franquia XY", "XY", "FREQUENCIA - APR FRANQUIA", "FREQUENCIA"}
DESC_FEE = {"Percentual atingido de rotas completas", "Percentual atingido de hora online"}

df_fin = st.session_state.get("df_fin")
inicio = st.session_state.get("inicio")
fim = st.session_state.get("fim")

st.markdown("""
    <div class='page-header'>
        <h2>📤 Despesas & Resultado</h2>
        <p>Custos operacionais e resultado líquido da franquia</p>
    </div>""", unsafe_allow_html=True)

# ── Faturamento bruto do período ───────────────────────────────────────────
mask = (df_fin["data_do_periodo_de_referencia"] >= inicio) & \
       (df_fin["data_do_periodo_de_referencia"] <= fim)
df = df_fin[mask]
fat_bruto = df["valor"].sum()
royalties_auto = fat_bruto * 0.03

# ── Entradas manuais das despesas ─────────────────────────────────────────
st.markdown("### ✏️ Informe as Despesas do Período")
st.info("💡 Os campos abaixo são preenchidos manualmente. Os valores são usados para calcular o resultado líquido da franquia.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Estrutura Operacional**")
    aluguel = st.number_input("Aluguel (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    agua_luz = st.number_input("Água e Luz (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")
    colaboradores = st.number_input("Colaboradores (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    contabilidade = st.number_input("Contabilidade (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")

with col2:
    st.markdown("**Sistemas & Serviços**")
    advogados = st.number_input("Advogados (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    erp_omie = st.number_input("Sistema ERP - Omie (R$)", min_value=0.0, value=0.0, step=10.0,  format="%.2f")
    transfeera = st.number_input("Pagamentos - Transfeera (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f")
    authentique = st.number_input("Contratos - Authentique (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f")

with col3:
    st.markdown("**Impostos & Outros**")
    iss = st.number_input("ISS (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")
    irpj_csll = st.number_input("IRPJ/CSLL (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")
    pis_cofins = st.number_input("PIS/Cofins (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")
    ir_aluguel = st.number_input("IR Aluguel (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")
    inss = st.number_input("INSS (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")
    promocoes = st.number_input("Promoções (R$)", min_value=0.0, value=0.0, step=50.0,  format="%.2f")

# ── Totais calculados ─────────────────────────────────────────────────────
total_impostos = iss + irpj_csll + pis_cofins + ir_aluguel + inss
total_sistemas = erp_omie + transfeera + authentique
total_estrutura = aluguel + agua_luz + colaboradores + contabilidade
total_outros   = advogados + promocoes
total_despesas = royalties_auto + total_estrutura + total_sistemas + total_impostos + total_outros
resultado      = fat_bruto - total_despesas

st.markdown("---")
st.markdown("### 📊 Resumo Financeiro")

# KPIs resultado
c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento Bruto",  fmt_brl(fat_bruto))
c2.metric("Total de Despesas",  fmt_brl(total_despesas),
          delta=f"-{fmt_brl(total_despesas)}", delta_color="inverse")
c3.metric("Royalties (3%)",     fmt_brl(royalties_auto),
          help="Calculado automaticamente: 3% do faturamento bruto")
resultado_delta = f"+{fmt_brl(resultado)}" if resultado >= 0 else fmt_brl(resultado)
c4.metric("Resultado Líquido",  fmt_brl(resultado),
          delta=resultado_delta,
          delta_color="normal" if resultado >= 0 else "inverse")

st.markdown("---")

# ── Gráficos ──────────────────────────────────────────────────────────────
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("#### Composição das Despesas")
    dados_desp = {
        "Royalties":   royalties_auto,
        "Estrutura":   total_estrutura,
        "Impostos":    total_impostos,
        "Sistemas":    total_sistemas,
        "Outros":      total_outros,
    }
    dados_desp = {k: v for k, v in dados_desp.items() if v > 0}
    if dados_desp:
        df_pizza = pd.DataFrame(list(dados_desp.items()), columns=["Categoria","Valor"])
        fig = px.pie(df_pizza, values="Valor", names="Categoria", hole=0.4,
                     color_discrete_sequence=["#ef4444","#f97316","#eab308","#22c55e","#3b82f6"])
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Preencha as despesas acima para visualizar o gráfico.")

with col_g2:
    st.markdown("#### Impostos Individuais")
    impostos = {
        "ISS": iss, "IRPJ/CSLL": irpj_csll,
        "PIS/Cofins": pis_cofins, "IR Aluguel": ir_aluguel, "INSS": inss,
    }
    impostos = {k: v for k, v in impostos.items() if v > 0}
    if impostos:
        df_imp = pd.DataFrame(list(impostos.items()), columns=["Imposto","Valor"])
        fig2 = px.bar(df_imp, x="Imposto", y="Valor", text_auto=".2s",
                      color="Valor", color_continuous_scale=["#fca5a5","#dc2626"])
        fig2.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Preencha os impostos acima para visualizar.")

# ── Waterfall receita x despesas ──────────────────────────────────────────
st.markdown("#### Resultado: Receita → Despesas → Líquido")
itens = [
    ("Faturamento Bruto", fat_bruto),
    ("Royalties",         -royalties_auto),
    ("Estrutura",         -total_estrutura),
    ("Impostos",          -total_impostos),
    ("Sistemas",          -total_sistemas),
    ("Outros",            -total_outros),
]
itens = [(n, v) for n, v in itens if v != 0 or n == "Faturamento Bruto"]
nomes  = [i[0] for i in itens] + ["Resultado Líquido"]
valores= [i[1] for i in itens]
cores  = ["#22c55e"] + ["#ef4444" if v < 0 else "#22c55e" for v in valores[1:]] + ["#3b82f6"]

fig3 = go.Figure(go.Waterfall(
    name="", orientation="v",
    measure=["absolute"] + ["relative"] * (len(valores)-1) + ["total"],
    x=nomes,
    y=valores + [None],
    connector={"line": {"color": "#d1d5db"}},
    decreasing={"marker": {"color": "#ef4444"}},
    increasing={"marker": {"color": "#22c55e"}},
    totals={"marker":    {"color": "#3b82f6"}},
    text=[fmt_brl(abs(v)) for v in valores] + [""],
    textposition="outside",
))
fig3.update_layout(
    height=360, margin=dict(t=20,b=10,l=10,r=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    yaxis=dict(gridcolor="#f0f0f0"),
)
st.plotly_chart(fig3, use_container_width=True)

# ── Tabela resumo ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📋 Tabela Detalhada de Despesas")
linhas = [
    ("Royalties (3% automático)", fmt_brl(royalties_auto), "Automático"),
    ("Aluguel",                   fmt_brl(aluguel),         "Manual"),
    ("Água e Luz",                fmt_brl(agua_luz),        "Manual"),
    ("Colaboradores",             fmt_brl(colaboradores),   "Manual"),
    ("Contabilidade",             fmt_brl(contabilidade),   "Manual"),
    ("Advogados",                 fmt_brl(advogados),       "Manual"),
    ("Promoções",                 fmt_brl(promocoes),       "Manual"),
    ("ERP Omie",                  fmt_brl(erp_omie),        "Manual"),
    ("Transfeera",                fmt_brl(transfeera),      "Manual"),
    ("Authentique",               fmt_brl(authentique),     "Manual"),
    ("ISS",                       fmt_brl(iss),             "Manual"),
    ("IRPJ/CSLL",                 fmt_brl(irpj_csll),       "Manual"),
    ("PIS/Cofins",                fmt_brl(pis_cofins),      "Manual"),
    ("IR Aluguel",                fmt_brl(ir_aluguel),      "Manual"),
    ("INSS",                      fmt_brl(inss),            "Manual"),
    ("**TOTAL DESPESAS**",        f"**{fmt_brl(total_despesas)}**", ""),
    ("**RESULTADO LÍQUIDO**",     f"**{fmt_brl(resultado)}**",      ""),
]
df_tab = pd.DataFrame(linhas, columns=["Despesa","Valor","Origem"])
st.dataframe(df_tab, use_container_width=True, hide_index=True)
