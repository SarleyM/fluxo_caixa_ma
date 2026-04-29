import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fluxo de Caixa", layout="wide")

# Lógica de máscara nativa (sem bibliotecas externas para não dar erro)
def formatar_moeda(texto):
    numeros = "".join(filter(str.isdigit, texto))
    if not numeros: return "R$ 0,00"
    return f"R$ {float(numeros)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def converter_para_float(texto):
    numeros = "".join(filter(str.isdigit, texto))
    return float(numeros)/100 if numeros else 0.0

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar():
    try:
        df = conn.read(worksheet="Página1", ttl="0s")
        if df.empty:
            return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])

if 'v_mask' not in st.session_state:
    st.session_state.v_mask = "R$ 0,00"

df = carregar()

# --- INTERFACE ---
st.title("📊 Gestão de Fluxo de Caixa")
st.divider()

with st.expander("➕ Novo Lançamento", expanded=True):
    col1, col2, col3 = st.columns(3)
    dt = col1.date_input("Data", date.today())
    tp = col2.selectbox("Tipo", ["Receita", "Despesa"])
    
    # Máscara em tempo real
    txt = col3.text_input("Valor (R$)", value=st.session_state.v_mask)
    if txt != st.session_state.v_mask:
        st.session_state.v_mask = formatar_moeda(txt)
        st.rerun()

    c4, c5 = st.columns(2)
    cat = c4.selectbox("Categoria", ["Vendas", "Fornecedores", "Aluguel", "Salários", "Outros"])
    desc = c5.text_input("Descrição")
    
    if st.button("✅ Salvar Lançamento", use_container_width=True):
        valor = converter_para_float(st.session_state.v_mask)
        if valor > 0:
            novo = pd.DataFrame([{'Data': dt, 'Tipo': tp, 'Categoria': cat, 'Valor': valor, 'Descrição': desc}])
            df_final = pd.concat([df, novo], ignore_index=True)
            df_final['Data'] = df_final['Data'].astype(str)
            
            try:
                conn.update(worksheet="Página1", data=df_final)
                st.session_state.v_mask = "R$ 0,00"
                st.success("Gravado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro de Permissão: Verifique se o e-mail da conta de serviço é EDITOR na planilha.")
        else:
            st.warning("Insira um valor.")

if not df.empty:
    st.divider()
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
