import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from streamlit_currency_input_text import currency_input

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_NAME = "fluxo_caixa.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            valor REAL,
            descricao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def carregar_dados(data_inicio, data_fim):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM movimentacoes WHERE data BETWEEN ? AND ?"
    df = pd.read_sql_query(query, conn, params=(data_inicio.strftime('%Y-%m-%d'), data_fim.strftime('%Y-%m-%d')))
    conn.close()
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df

def salvar_registro(data, tipo, categoria, valor, descricao):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    valor_final = valor if tipo == "Receita" else -valor
    c.execute('''
        INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (data.strftime('%Y-%m-%d'), tipo, categoria, valor_final, descricao))
    conn.commit()
    conn.close()

# --- INTERFACE ---
st.set_page_config(page_title="Gestão de Fluxo de Caixa", layout="wide")
init_db()

# --- SIDEBAR (Filtros e Exportar) ---
with st.sidebar:
    st.markdown("### 🗓️ Filtros de Relatório")
    data_inicio = st.date_input("Início", value=datetime(2026, 4, 1))
    data_fim = st.date_input("Fim", value=datetime(2026, 4, 28))
    
    st.markdown("---")
    st.markdown("### 📥 Exportar")
    if st.button("Gerar Relatório Excel"):
        st.info("Função de exportação pronta para os dados filtrados.")

# --- CORPO PRINCIPAL ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # Substitua pelo caminho da sua imagem ou URL
    st.image("https://via.placeholder.com/150x150.png?text=BOIANI", width=120) 
with col_titulo:
    st.title("Gestão de Fluxo de Caixa")

st.markdown("---")

# --- FORMULÁRIO DE LANÇAMENTO (Conforme a Imagem) ---
with st.expander("➕ Realizar Novo Lançamento", expanded=True):
    with st.form("form_novo_lancamento", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        data_lan = col1.date_input("Data", datetime.now())
        tipo_lan = col2.selectbox("Tipo", ["Receita", "Despesa"])
        
        # CAMPO DE MOEDA AUTOMÁTICO
        valor_lan = currency_input("Valor (R$)", value=0.00, key="moeda_input")
        
        col4, col5 = st.columns([1, 2])
        cat_lan = col4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Outros"])
        desc_lan = col5.text_input("Descrição / Detalhes", placeholder="Ex: Pão caseiro")
        
        submit = st.form_submit_button("✅ Salvar Lançamento", use_container_width=True)
        
        if submit:
            if valor_lan > 0:
                salvar_registro(data_lan, tipo_lan, cat_lan, valor_lan, desc_lan)
                st.success("Lançamento salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Insira um valor maior que zero.")

# --- EXIBIÇÃO DOS DADOS FILTRADOS ---
df_filtrado = carregar_dados(data_inicio, data_fim)

if not df_filtrado.empty:
    st.subheader("📊 Movimentações do Período")
    
    # Cálculos para o Dashboard
    rec = df_filtrado[df_filtrado["valor"] > 0]["valor"].sum()
    desp = df_filtrado[df_filtrado["valor"] < 0]["valor"].sum()
    saldo = rec + desp
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Receitas", f"R$ {rec:,.2f}")
    m2.metric("Total Despesas", f"R$ {abs(desp):,.2f}", delta_color="inverse")
    m3.metric("Saldo Período", f"R$ {saldo:,.2f}")
    
    st.dataframe(df_filtrado.sort_values("data", ascending=False), use_container_width=True)
else:
    st.info("Nenhum dado encontrado para o período selecionado.")
