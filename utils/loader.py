import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _path(nome: str) -> Path:
    from config import ARQUIVOS
    return DATA_DIR / ARQUIVOS[nome]


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_base() -> pd.DataFrame:
    df = pd.read_excel(_path("base"), sheet_name="Sheet1", dtype={"ID": str})
    df.columns = df.columns.str.strip()
    df["Data de nascimento"] = pd.to_datetime(df["Data de nascimento"], dayfirst=True, errors="coerce")
    df["ativo"] = df["ativo"].str.strip().str.lower()
    df["Modal"] = df["Modal"].str.strip().str.upper()
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_financeiro() -> pd.DataFrame:
    df = pd.read_excel(_path("financeiro"), dtype={"id_da_pessoa_entregadora": str})
    df.columns = df.columns.str.strip()
    for col in ["data_do_lancamento_financeiro", "data_do_periodo_de_referencia", "data_do_repasse"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["subpraca"] = df["subpraca"].fillna("Livre (São Paulo)")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_performance() -> pd.DataFrame:
    df = pd.read_excel(_path("performance"), dtype={"id_da_pessoa_entregadora": str})
    df.columns = df.columns.str.strip()
    df["data_do_periodo"] = pd.to_datetime(df["data_do_periodo"], errors="coerce")
    df["sub_praca"] = df["sub_praca"].fillna("Livre (São Paulo)")

    # Converter tempo_disponivel_absoluto (HH:MM:SS) para horas decimais
    def hms_para_horas(s):
        try:
            if pd.isna(s):
                return 0.0
            partes = str(s).split(":")
            return int(partes[0]) + int(partes[1]) / 60 + int(partes[2]) / 3600
        except Exception:
            return 0.0

    df["horas_online"] = df["tempo_disponivel_absoluto"].apply(hms_para_horas)
    df["horas_escaladas"] = pd.to_numeric(df["tempo_disponivel_escalado"], errors="coerce").fillna(0)
    return df


def filtrar_por_periodo(df: pd.DataFrame, col_data: str, inicio, fim) -> pd.DataFrame:
    inicio = pd.Timestamp(inicio)
    fim = pd.Timestamp(fim)
    mask = (df[col_data] >= inicio) & (df[col_data] <= fim)
    return df.loc[mask].copy()


def aniversariantes_hoje(df_base: pd.DataFrame) -> pd.DataFrame:
    hoje = pd.Timestamp.today()
    mask = (
        (df_base["Data de nascimento"].dt.month == hoje.month) &
        (df_base["Data de nascimento"].dt.day == hoje.day) &
        (df_base["ativo"] == "ativo")
    )
    return df_base.loc[mask, ["Nome", "Data de nascimento", "Modal", "Telefone"]].copy()
