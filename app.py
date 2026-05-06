import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_NAME = "fluxo_caixa.db"

def init_db():
    """Cria a tabela se ela não existir."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            descricao TEXT,
            categoria TEXT,
            valor REAL,
            tipo TEXT
        )
    ''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes", conn)
    conn.close()
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df

def salvar_registro(data, descricao, categoria, valor, tipo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO movimentacoes (data, descricao, categoria, valor, tipo)
        VALUES (?, ?, ?, ?, ?)
    ''', (data.strftime('%Y-%m-%d'), descricao, categoria, valor, tipo))
    conn.commit()
    conn.close()

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Fluxo de Caixa - SQLite", layout="wide")
init_db()

st.title("📊 Gestão de Fluxo de Caixa (Banco de Dados)")

# --- FORMULÁRIO LATERAL ---
with st.sidebar:
    st.header("Novo Lançamento")
    with st.form("form_registro", clear_on_submit=True):
        data_sel = st.date_input("Data", datetime.now())
        desc_sel = st.text_input("Descrição")
        valor_sel = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        tipo_sel = st.selectbox("Tipo", ["Receita", "Despesa"])
        cat_sel = st.selectbox("Categoria", ["Vendas", "Serviços", "Fixo", "Marketing", "Outros"])
        
        if st.form_submit_button("Salvar no Banco"):
            if desc_sel and valor_sel > 0:
                valor_final = valor_sel if tipo_sel == "Receita" else -valor_sel
                salvar_registro(data_sel, desc_sel, cat_sel, valor_final, tipo_sel)
                st.success("Dados salvos!")
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente.")

# --- DASHBOARD ---
df = carregar_dados()

if not df.empty:
    # Métricas
    receitas = df[df["valor"] > 0]["valor"].sum()
    despesas = df[df["valor"] < 0]["valor"].sum()
    saldo = receitas + despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {receitas:,.2f}")
    c2.metric("Despesas", f"R$ {abs(despesas):,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")

    st.divider()
    st.subheader("Histórico de Lançamentos")
    st.dataframe(df.sort_values("data", ascending=False), use_container_width=True)
    
    # Exportar para Excel (opcional para o cliente)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Baixar Backup (CSV)", csv, "fluxo_caixa_backup.csv", "text/csv")

else:
    st.info("Aguardando o primeiro lançamento...")
else:
    st.write("Nenhum lançamento encontrado. Use o menu lateral para começar.")
