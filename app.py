import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(page_title="Fluxo de Caixa Pro", layout="wide")

# --- Lógica de Máscara Nativa (Evita erros de Node/JS) ---
def formatar_moeda_br(valor_texto):
    # Remove tudo o que não é número
    apenas_numeros = "".join(filter(str.isdigit, valor_texto))
    if not apenas_numeros:
        return "R$ 0,00"
    # Converte para float (centavos)
    valor_float = float(apenas_numeros) / 100
    return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def extrair_valor_float(valor_formatado):
    numeros = "".join(filter(str.isdigit, valor_formatado))
    return float(numeros) / 100 if numeros else 0.0

# --- Conexão com Google Sheets ---
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
        return False

# Inicialização do estado da máscara
if 'mascara_valor' not in st.session_state:
    st.session_state.mascara_valor = "R$ 0,00"

df = carregar_dados()

# --- Cabeçalho ---
col_l, col_t = st.columns([1, 10])
with col_l:
    if os.path.exists("logo_ma.png"):
        st.image("logo_ma.png", width=80)
    else:
        st.write("📊")
with col_t:
    st.markdown("<h1 style='margin:0;'>Gestão de Fluxo de Caixa</h1>", unsafe_allow_html=True)

st.divider()

# --- Novo Lançamento ---
with st.expander("➕ Novo Lançamento", expanded=True):
    c1, c2, c3 = st.columns(3)
    data_lan = c1.date_input("Data", date.today(), format="DD/MM/YYYY")
    tipo_lan = c2.selectbox("Tipo", ["Receita", "Despesa"])
    
    # Campo com máscara em tempo real (Nativo e Seguro)
    entrada_texto = c3.text_input("Valor (R$)", value=st.session_state.mascara_valor)
    if entrada_texto != st.session_state.mascara_valor:
        st.session_state.mascara_valor = formatar_moeda_br(entrada_texto)
        st.rerun()

    c4, c5 = st.columns(2)
    cat_lan = c4.selectbox("Categoria", ["Vendas", "Fornecedores", "Aluguel", "Impostos", "Salários", "Marketing", "Outros"])
    desc_lan = c5.text_input("Descrição / Detalhes")
    
    if st.button("✅ Salvar no Google Sheets", use_container_width=True):
        valor_final = extrair_valor_float(st.session_state.mascara_valor)
        if valor_final > 0:
            novo_registro = pd.DataFrame([{
                'Data': data_lan, 'Tipo': tipo_lan, 'Categoria': cat_lan,
                'Valor': valor_final, 'Descrição': desc_lan
            }])
            sucesso = salvar_dados(pd.concat([df, novo_registro], ignore_index=True))
            if sucesso:
                st.session_state.mascara_valor = "R$ 0,00"
                st.success("Lançamento realizado!")
                st.rerun()
            else:
                st.error("ERRO DE PERMISSÃO: Aceda à sua Planilha Google -> Partilhar -> Altere para 'Qualquer pessoa com o link' como 'EDITOR'.")
        else:
            st.warning("Introduza um valor válido.")

# --- Visualização ---
if not df.empty:
    st.subheader("📋 Resumo Financeiro")
    rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
    des = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Entradas", f"R$ {rec:,.2f}")
    m2.metric("Total Saídas", f"R$ {des:,.2f}")
    m3.metric("Saldo", f"R$ {rec - des:,.2f}")
    
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
