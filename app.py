import streamlit as st
import sys
from pathlib import Path
from config import USUARIOS, PAGINAS_POR_PERFIL
from utils.loader import carregar_base, carregar_financeiro, carregar_performance
from utils.helpers import sidebar_filtro_data

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
PAGES_DIR = ROOT / "pages_"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "utils"))


# ── Configuração da página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)
# page_icon="🛵",

# ── CSS customizado ────────────────────────────────────────────────────────
with open(ROOT / "assets" / "style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.perfil = None
    st.session_state.nome_usuario = None

# ── Mapeamento página → arquivo ────────────────────────────────────────────
MAPA_PAGINAS = {
    "Visão Geral Financeira": PAGES_DIR / "fin_visao_geral.py",
    "Receitas": PAGES_DIR / "fin_receitas.py",
    "Despesas": PAGES_DIR / "fin_despesas.py",
    "Visão Geral Performance": PAGES_DIR / "perf_visao_geral.py",
    "Perfil do Entregador": PAGES_DIR / "perf_driver.py",
    "Subpraças": PAGES_DIR / "perf_subpracas.py",
}


# ── Tela de login ──────────────────────────────────────────────────────────
def tela_login():
    st.markdown("""<style>[data-testid="stSidebar"]{display:none}</style>""",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        #  MOVEE
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align:center; margin-bottom:2rem;'>
                <h1 style='font-size:2.5rem; font-weight:800; color:#fffff; letter-spacing:2px;'>
                    🛵 Logística
                </h1>
                <p style='color:#8494a7; font-size:0.9rem;'>Soluções Logísticas LTDA</p>
                <p style='color:#b0bac5; font-size:0.8rem;'>Dashboard de Gestão</p>
            </div>""", unsafe_allow_html=True)

        with st.form("login_form"):
            usuario = st.text_input("Usuário", placeholder="seu usuário")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                st.session_state.perfil = USUARIOS[usuario]["perfil"]
                st.session_state.nome_usuario = USUARIOS[usuario]["nome"]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")


# ── Sidebar com navegação ──────────────────────────────────────────────────
def montar_sidebar(df_fin, df_perf):
    perfil = st.session_state.perfil
    nome = st.session_state.nome_usuario

    with st.sidebar:
        st.markdown("""
            <div class='sidebar-logo'>
                <h1>🛵 Logística</h1>
                <p>Soluções Logísticas</p>
            </div>""", unsafe_allow_html=True)

        classe_perfil = "perfil-financeiro" if perfil == "financeiro" else "perfil-suporte"
        label_perfil = "Financeiro" if perfil == "financeiro" else "Suporte"
        st.markdown(f"""
            <div style='text-align:center; margin-bottom:1.2rem;'>
                <span style='font-size:0.8rem; color:#a8b4c0;'>👤 {nome}</span><br>
                <span class='perfil-badge {classe_perfil}'>{label_perfil}</span>
            </div>""", unsafe_allow_html=True)

        paginas_disponiveis = PAGINAS_POR_PERFIL[perfil]
        pagina = st.selectbox("📂 Navegação", paginas_disponiveis, key="pagina_atual")

        inicio, fim = sidebar_filtro_data(df_fin, df_perf)

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    return pagina, inicio, fim


# ── Executa a página via st.navigation com position="hidden" ──────────────
def rotear(pagina, df_base, df_fin, df_perf, inicio, fim):
    # Dados disponíveis para as páginas via session_state
    st.session_state["df_base"] = df_base
    st.session_state["df_fin"] = df_fin
    st.session_state["df_perf"] = df_perf
    st.session_state["inicio"] = inicio
    st.session_state["fim"] = fim

    arquivo = MAPA_PAGINAS.get(pagina)
    if arquivo and arquivo.exists():
        pg = st.navigation([st.Page(str(arquivo))], position="hidden")
        pg.run()
    else:
        st.warning(f"Página '{pagina}' não encontrada.")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.autenticado:
        tela_login()
        return

    with st.spinner("Carregando dados..."):
        df_base = carregar_base()
        df_fin = carregar_financeiro()
        df_perf = carregar_performance()

    pagina, inicio, fim = montar_sidebar(df_fin, df_perf)
    rotear(pagina, df_base, df_fin, df_perf, inicio, fim)


if __name__ == "__main__":
    main()
