import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import io
from streamlit_gsheets import GSheetsConnection
from streamlit_currency_input import currency_input

# 1. CONFIGURAÇÕES
st.set_page_config(page_title="Fluxo de Caixa Pro", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(worksheet="Página1", ttl="0s")
        if df.empty:
            return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])

def salvar_dados(df_novo):
    try:
        df_salvar = df_novo.copy()
        df_salvar['Data'] = df_salvar['Data'].astype(str)
        conn.update(worksheet="Página1", data=df_salvar)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: Verifique as permissões da planilha.")
        return False

# Inicialização
df = carregar_dados()
categorias = ["Vendas", "Fornecedores", "Aluguel", "Impostos", "Salários", "Marketing", "Outros"]

# 2. CABEÇALHO
col_logo, col_titulo = st.columns([1, 10])
with col_logo:
    if os.path.exists("logo_ma.png"):
        st.image("logo_ma.png", width=80)
    else:
        st.title("📊")

with col_titulo:
    st.markdown("<h1 style='margin-top: 10px;'>Gestão de Fluxo de Caixa</h1>", unsafe_allow_html=True)

st.divider()

# 3. NOVO LANÇAMENTO
with st.expander("➕ Novo Lançamento", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    data_mov = col1.date_input("Data", date.today(), format="DD/MM/YYYY")
    tipo = col2.selectbox("Tipo", ["Receita", "Despesa"])
    
    # Máscara em tempo real
    with col3:
        valor = currency_input(
            "Valor (R$)", 
            key="valor_caixa", 
            currency="R$ ", 
            decimal_separator=",", 
            thousands_separator=".",
            initial_value=0.0
        )
    
    c4, c5 = st.columns(2)
    categoria = c4.selectbox("Categoria", categorias)
    descricao = c5.text_input("Descrição / Detalhes")
    
    if st.button("✅ Salvar Lançamento", use_container_width=True):
        if valor > 0:
            novo_item = pd.DataFrame([{
                'Data': data_mov, 'Tipo': tipo, 'Categoria': categoria,
                'Valor': valor, 'Descrição': descricao
            }])
            df_final = pd.concat([df, novo_item], ignore_index=True)
            if salvar_dados(df_final):
                st.success("Salvo!")
                st.rerun()
        else:
            st.error("Insira um valor.")

# 4. DASHBOARD
if not df.empty:
    st.divider()
    t_rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
    t_des = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas", f"R$ {t_rec:,.2f}")
    m2.metric("Saídas", f"R$ {t_des:,.2f}")
    m3.metric("Saldo", f"R$ {t_rec - t_des:,.2f}")

    # Lista de Lançamentos
    st.subheader("📋 Últimos Lançamentos")
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
