import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa", layout="wide", page_icon="📊")

# --- BANCO DE DADOS (SQLITE) ---
DB_NAME = "fluxo_caixa_v2.db"

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

def salvar_no_banco(data, tipo, categoria, valor, descricao):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    valor_ajustado = valor if tipo == "Receita" else -abs(valor)
    # Salva no formato ISO (YYYY-MM-DD) para ordenação correta no SQL
    c.execute('''
        INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (data.strftime('%Y-%m-%d'), tipo, categoria, valor_ajustado, descricao))
    conn.commit()
    conn.close()

def carregar_dados_do_banco():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        # Converte a coluna de texto para datetime real
        df['data_dt'] = pd.to_datetime(df['data'])
        # Cria a coluna formatada para exibição (DD/MM/AAAA)
        df['Data'] = df['data_dt'].dt.strftime('%d/%m/%Y')
    return df

# Inicializa o banco
init_db()

# --- CSS PARA ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (FILTROS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10543/10543122.png", width=80) 
    st.title("Filtros")
    
    # Define o primeiro e último dia do mês corrente de forma dinâmica
    hoje = date.today()
    primeiro_dia_mes = date(hoje.year, hoje.month, 1)
    # Uma aproximação simples para o fim do mês corrente (dia 28 ou 31 dependendo do mês)
    ultimo_dia_mes = date(hoje.year, hoje.month, 28) if hoje.month == 2 else date(hoje.year, hoje.month, 30 if hoje.month in [4,6,9,11] else 31)
    
    # Filtros usando o formato brasileiro de exibição (format="DD/MM/YYYY")
    data_inicio = st.date_input("Início", value=primeiro_dia_mes, format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", value=ultimo_dia_mes, format="DD/MM/YYYY")

# --- CABEÇALHO ---
col_l, col_r = st.columns([1, 5])
with col_l:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) 
with col_r:
    st.title("Gestão de Fluxo de Caixa")

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.expander("➕ REALIZAR NOVO LANÇAMENTO", expanded=True):
    with st.form("meu_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 1, 1.5])
        # Campo de inserção de data também formatado em PT-BR
        data_f = c1.date_input("Data", value=datetime.now(), format="DD/MM/YYYY")
        tipo_f = c2.selectbox("Tipo", ["Receita", "Despesa"])
        valor_f = c3.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat_f = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"])
        desc_f = c5.text_input("Descrição / Detalhes")
        
        submit = st.form_submit_button("✅ SALVAR LANÇAMENTO", use_container_width=True)
        
        if submit:
            if valor_f > 0:
                salvar_no_banco(data_f, tipo_f, cat_f, valor_f, desc_f)
                st.success(f"Salvo: {data_f.strftime('%d/%m/%Y')}")
                st.rerun()
            else:
                st.error("O valor precisa ser maior que zero.")

# --- DASHBOARD E TABELA ---
df_total = carregar_dados_do_banco()

if not df_total.empty:
    # Aplica o filtro de data no DataFrame usando os inputs da sidebar
    mask = (df_total['data_dt'].dt.date >= data_inicio) & (df_total['data_dt'].dt.date <= data_fim)
    df = df_total.loc[mask]

    # Cálculos das métricas com base no período filtrado
    rec = df[df["valor"] > 0]["valor"].sum()
    desp = df[df["valor"] < 0]["valor"].sum()
    saldo = rec + desp

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Receitas", f"R$ {rec:,.2f}")
    m2.metric("Total Despesas", f"R$ {abs(desp):,.2f}", delta_color="inverse")
    m3.metric("Saldo do Período", f"R$ {saldo:,.2f}")

    st.markdown("### 📋 Histórico de Movimentações")
    # Exibe a tabela estruturada com a coluna "Data" formatada em DD/MM/AAAA
    st.dataframe(
        df[["Data", "tipo", "categoria", "valor", "descricao"]],
        use_container_width=True,
        column_config={
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            "Data": st.column_config.TextColumn("Data", width="small")
        }
    )
else:
    st.info("Nenhum dado cadastrado ou encontrado para o período selecionado.")
