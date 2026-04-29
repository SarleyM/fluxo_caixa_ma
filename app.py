import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import io
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Pro", layout="wide")

# Lógica de formatação nativa
def format_brl(val):
    clean_val = "".join(filter(str.isdigit, val))
    if not clean_val: return "R$ 0,00"
    float_val = float(clean_val) / 100
    return f"R$ {float_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def to_float(val_str):
    clean_val = "".join(filter(str.isdigit, val_str))
    return float(clean_val) / 100 if clean_val else 0.0

# --- CONEXÃO ---
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
    except:
        st.error("Erro de permissão na planilha!")
        return False

# Inicialização de estados
df = carregar_dados()
if 'v_mask' not in st.session_state: st.session_state.v_mask = "R$ 0,00"

# --- CABEÇALHO ---
c_logo, c_titulo = st.columns([1, 10])
with c_logo:
    if os.path.exists("logo_ma.png"): st.image("logo_ma.png", width=80)
    else: st.title("📊")
with c_titulo:
    st.markdown("<h1 style='margin:0;'>Gestão de Fluxo de Caixa</h1>", unsafe_allow_html=True)

st.divider()

# --- LANÇAMENTO ---
with st.expander("➕ Novo Lançamento", expanded=True):
    col1, col2, col3 = st.columns(3)
    data_mov = col1.date_input("Data", date.today(), format="DD/MM/YYYY")
    tipo = col2.selectbox("Tipo", ["Receita", "Despesa"])
    
    # Máscara Nativa (Mais estável para o servidor)
    val_input = col3.text_input("Valor (R$)", value=st.session_state.v_mask)
    if val_input != st.session_state.v_mask:
        st.session_state.v_mask = format_brl(val_input)
        st.rerun()

    c4, c5 = st.columns(2)
    cat = c4.selectbox("Categoria", ["Vendas", "Fornecedores", "Aluguel", "Impostos", "Salários", "Outros"])
    desc = c5.text_input("Descrição")
    
    if st.button("✅ Salvar Lançamento", use_container_width=True):
        final_val = to_float(st.session_state.v_mask)
        if final_val > 0:
            novo = pd.DataFrame([{'Data': data_mov, 'Tipo': tipo, 'Categoria': cat, 'Valor': final_val, 'Descrição': desc}])
            if salvar_dados(pd.concat([df, novo], ignore_index=True)):
                st.session_state.v_mask = "R$ 0,00"
                st.success("Salvo com sucesso!")
                st.rerun()

# --- DASHBOARD ---
if not df.empty:
    t_rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
    t_des = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas", f"R$ {t_rec:,.2f}")
    m2.metric("Saídas", f"R$ {t_des:,.2f}")
    m3.metric("Saldo", f"R$ {t_rec - t_des:,.2f}")
    
    st.subheader("📋 Movimentações")
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
