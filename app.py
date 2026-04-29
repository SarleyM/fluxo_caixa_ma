import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Pro", layout="wide")

# --- LÓGICA DE MÁSCARA NATIVA (Segura e sem erros de JS) ---
def formatar_brl(texto):
    numeros = "".join(filter(str.isdigit, texto))
    if not numeros: return "R$ 0,00"
    valor_float = float(numeros) / 100
    return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def para_float(texto_formatado):
    numeros = "".join(filter(str.isdigit, texto_formatado))
    return float(numeros) / 100 if numeros else 0.0

# --- CONEXÃO COM GOOGLE SHEETS ---
# Utilizaremos o segredo "connections.gsheets" configurado no Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # worksheet="Página1" deve ser o nome exato da aba
        df = conn.read(worksheet="Página1", ttl="0s")
        if df.empty:
            return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])

def salvar_dados(df_novo):
    try:
        # Converter datas para string antes de enviar para evitar erros de formato
        df_salvar = df_novo.copy()
        df_salvar['Data'] = df_salvar['Data'].astype(str)
        conn.update(worksheet="Página1", data=df_salvar)
        return True
    except Exception as e:
        st.sidebar.error(f"Detalhe técnico: {e}")
        return False

# --- INICIALIZAÇÃO ---
if 'v_mask' not in st.session_state:
    st.session_state.v_mask = "R$ 0,00"

df = carregar_dados()

# --- INTERFACE ---
col_l, col_t = st.columns([1, 10])
with col_l:
    if os.path.exists("logo_ma.png"): st.image("logo_ma.png", width=80)
    else: st.write("📊")
with col_t:
    st.markdown("<h1 style='margin:0;'>Gestão de Fluxo de Caixa</h1>", unsafe_allow_html=True)

st.divider()

# --- NOVO LANÇAMENTO ---
with st.expander("➕ Novo Lançamento", expanded=True):
    c1, c2, c3 = st.columns(3)
    dt = c1.date_input("Data", date.today(), format="DD/MM/YYYY")
    tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
    
    # Máscara em tempo real sem bibliotecas externas
    val_raw = c3.text_input("Valor (R$)", value=st.session_state.v_mask)
    if val_raw != st.session_state.v_mask:
        st.session_state.v_mask = formatar_brl(val_raw)
        st.rerun()

    c4, c5 = st.columns(2)
    cat = c4.selectbox("Categoria", ["Vendas", "Fornecedores", "Aluguel", "Salários", "Impostos", "Outros"])
    desc = c5.text_input("Descrição")
    
    if st.button("✅ Gravar Lançamento", use_container_width=True):
        valor_final = para_float(st.session_state.v_mask)
        if valor_final > 0:
            novo = pd.DataFrame([{'Data': dt, 'Tipo': tp, 'Categoria': cat, 'Valor': valor_final, 'Descrição': desc}])
            sucesso = salvar_dados(pd.concat([df, novo], ignore_index=True))
            if sucesso:
                st.session_state.v_mask = "R$ 0,00"
                st.success("Dados gravados com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao gravar. Verifique se as 'Secrets' do Streamlit Cloud estão configuradas corretamente.")
        else:
            st.warning("Introduza um valor válido.")

# --- DASHBOARD ---
if not df.empty:
    st.divider()
    rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
    des = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas", f"R$ {rec:,.2f}")
    m2.metric("Saídas", f"R$ {des:,.2f}")
    m3.metric("Saldo", f"R$ {rec - des:,.2f}")
    
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
