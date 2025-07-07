import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(
    page_title="Dashboard de TI - Inventário",
    page_icon="📊",
    layout="wide"
)

# Lê a chave do arquivo de secrets
escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
chave_json = st.secrets["GOOGLE_SERVICE_ACCOUNT"]
credenciais = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(chave_json), escopo)
cliente = gspread.authorize(credenciais)

@st.cache_data(ttl=300)
def carregar_dados(nome_aba, headers):
    planilha = cliente.open_by_key("1KhGmSq5WEsF3l0iA1hBs98OiduIdnJlHlFclNr-TUZg")
    aba = planilha.worksheet(nome_aba)
    dados = aba.get_all_records(expected_headers=headers)
    return pd.DataFrame(dados)

df_toners = carregar_dados("Toners", ["MODELO", "LACRADO/ABERTO", "QUANTIDADE"])
df_perifericos = carregar_dados("Periféricos", ["PERIFÉRICOS", "QUANTIDADE"])
df_tintas = carregar_dados("Tintas", ["CÓDIGO", "COR", "QUANTIDADE"])

df_toners["QUANTIDADE"] = pd.to_numeric(df_toners["QUANTIDADE"], errors="coerce")
df_perifericos["QUANTIDADE"] = pd.to_numeric(df_perifericos["QUANTIDADE"], errors="coerce")
df_tintas["QUANTIDADE"] = pd.to_numeric(df_tintas["QUANTIDADE"], errors="coerce")
df_tintas["CÓDIGO"] = df_tintas["CÓDIGO"].astype(str)

with st.sidebar:
    st.title("Filtros")
    st.markdown("Selecione os filtros para visualizar os dados.")
    toner_status = st.selectbox("Status do Toner", options=["Todos", "LACRADO", "ABERTO"])
    cor_tinta = st.multiselect("Cores de Tinta", options=df_tintas["COR"].unique(), default=df_tintas["COR"].unique())

st.title("📊 Inventário de TI")
st.markdown("Visualização completa do estoque de toners, periféricos e tintas.")

tab1, tab2, tab3 = st.tabs(["Toners", "Periféricos", "Tintas"])

# ===== TAB 1: TONERS =====
with tab1:
    st.header("Toners")

    # Filtro por status
    if toner_status == "LACRADO":
        df_toners_filtrado = df_toners[df_toners["LACRADO/ABERTO"] == "LACRADO"]
    elif toner_status == "ABERTO":
        df_toners_filtrado = df_toners[df_toners["LACRADO/ABERTO"] == "ABERTO"]
    else:
        df_toners_filtrado = df_toners

    # Remove linhas com quantidade nula ou zero
    df_toners_filtrado = df_toners_filtrado[df_toners_filtrado["QUANTIDADE"] > 0]

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total de Toners", value=int(df_toners_filtrado["QUANTIDADE"].sum()))
    with col2:
        st.metric(label="Modelos Diferentes", value=df_toners_filtrado["MODELO"].nunique())

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição de Status")
        fig_pie = px.pie(
            df_toners_filtrado,
            names="LACRADO/ABERTO",
            values="QUANTIDADE",
            hole=0.3,
            color="LACRADO/ABERTO",
            color_discrete_map={"LACRADO": "#006400", "ABERTO": "#7CFC00"}
        )
        fig_pie.update_traces(textinfo='percent+label', textfont_size=14)
        fig_pie.update_layout(showlegend=True, legend_title="Status")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Quantidade por Modelo")
        df_grouped = df_toners_filtrado.groupby(["MODELO", "LACRADO/ABERTO"], as_index=False)["QUANTIDADE"].sum()
        df_grouped_sorted = df_grouped.sort_values("QUANTIDADE", ascending=False)

        fig_bar = px.bar(
            df_grouped_sorted,
            x="MODELO",
            y="QUANTIDADE",
            color="LACRADO/ABERTO",
            barmode="group",
            text="QUANTIDADE",
            color_discrete_map={"LACRADO": "#006400", "ABERTO": "#7CFC00"}
        )
        fig_bar.update_traces(textposition="outside", textfont_size=12)
        fig_bar.update_layout(
            xaxis_title="Modelos",
            yaxis_title="Quantidade",
            legend_title="Status",
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=False),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ===== TAB 2: PERIFÉRICOS =====
with tab2:
    st.header("Periféricos")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Periféricos", int(df_perifericos["QUANTIDADE"].sum()))
    with col2:
        st.metric("Tipos Diferentes", df_perifericos["PERIFÉRICOS"].nunique())

    st.subheader("Quantidade por Tipo")
    fig_bar_perifericos = px.bar(
        df_perifericos,
        x="PERIFÉRICOS",
        y="QUANTIDADE",
        text="QUANTIDADE",
        color="PERIFÉRICOS",
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    fig_bar_perifericos.update_traces(textposition="outside")
    st.plotly_chart(fig_bar_perifericos, use_container_width=True)

# ===== TAB 3: TINTAS =====
with tab3:
    st.header("Tintas")
    df_tintas_filtrado = df_tintas[df_tintas["COR"].isin(cor_tinta)]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Tintas", int(df_tintas_filtrado["QUANTIDADE"].sum()))
    with col2:
        st.metric("Cores Diferentes", df_tintas_filtrado["COR"].nunique())

    st.subheader("Quantidade por Código e Cor")
    fig_bar_tintas = px.bar(
        df_tintas_filtrado,
        x="CÓDIGO",
        y="QUANTIDADE",
        color="COR",
        text="QUANTIDADE",
        barmode="group",
        category_orders={"CÓDIGO": sorted(df_tintas["CÓDIGO"].unique())},
        color_discrete_map={
            "CYAN": "#00FFFF",
            "MAGENTA": "#FF00FF",
            "YELLOW": "#FFFF00",
            "BLACK": "#000000"
        }
    )
    fig_bar_tintas.update_xaxes(type='category')
    fig_bar_tintas.update_traces(textposition="outside")
    st.plotly_chart(fig_bar_tintas, use_container_width=True)

st.markdown("---")
st.caption("Criado por MSE Engenharia - TI")
