import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

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
    c.execute('''
        INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (data.strftime('%Y-%m-%d'), tipo, categoria, valor_ajustado, descricao))
    conn.commit()
    conn.close()

def excluir_registro(id_registro):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM movimentacoes WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()

def carregar_dados_do_banco():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
        df['Data Formatada'] = df['data_dt'].dt.strftime('%d/%m/%Y')
    return df

init_db()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10543/10543122.png", width=80) 
    st.title("Filtros")
    data_inicio = st.date_input("Início", value=datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", value=datetime(2026, 5, 30), format="DD/MM/YYYY")
    
    st.markdown("---")
    st.markdown("### 📥 Exportar")
    
    df_para_exportar = carregar_dados_do_banco()
    if not df_para_exportar.empty:
        # Lógica para gerar EXCEL real (XLSX) e não CSV
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Selecionamos as colunas limpas para o Excel
            df_excel = df_para_exportar[['Data Formatada', 'tipo', 'categoria', 'valor', 'descricao']]
            df_excel.columns = ['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição']
            df_excel.to_excel(writer, index=False, sheet_name='Fluxo de Caixa')
        
        st.download_button(
            label="📊 Baixar Relatório Excel",
            data=output.getvalue(),
            file_name=f"fluxo_caixa_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

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
        data_f = c1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        tipo_f = c2.selectbox("Tipo", ["Receita", "Despesa"])
        valor_f = c3.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat_f = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"])
        desc_f = c5.text_input("Descrição / Detalhes")
        
        if st.form_submit_button("✅ SALVAR LANÇAMENTO", use_container_width=True):
            if valor_f > 0:
                salvar_no_banco(data_f, tipo_f, cat_f, valor_f, desc_f)
                st.rerun()

# --- DASHBOARD E TABELA ---
df_total = carregar_dados_do_banco()

if not df_total.empty:
    mask = (df_total['data_dt'].dt.date >= data_inicio) & (df_total['data_dt'].dt.date <= data_fim)
    df = df_total.loc[mask]

    if not df.empty:
        # Métricas
        rec = df[df["valor"] > 0]["valor"].sum()
        desp = df[df["valor"] < 0]["valor"].sum()
        saldo = rec + desp

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Receitas", f"R$ {rec:,.2f}")
        m2.metric("Total Despesas", f"R$ {abs(desp):,.2f}", delta_color="inverse")
        m3.metric("Saldo do Período", f"R$ {saldo:,.2f}")

        st.markdown("### 📋 Histórico de Movimentações")
        
        # Tabela com Editor (Permite excluir e editar rápido)
        st.write("Dica: Para excluir, selecione a linha e aperte 'Delete' ou use o menu abaixo.")
        
        # Exibição principal
        st.dataframe(
            df[["Data Formatada", "tipo", "categoria", "valor", "descricao"]],
            use_container_width=True,
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "Data Formatada": "Data"
            }
        )

        # --- SEÇÃO DE EXCLUSÃO/EDIÇÃO ---
        st.markdown("---")
        st.subheader("🛠️ Gerenciar Lançamentos")
        col_edit, col_del = st.columns(2)
        
        with col_del:
            opcoes_del = {row['id']: f"{row['Data Formatada']} - {row['descricao']} (R$ {row['valor']:.2f})" for _, row in df.iterrows()}
            id_para_deletar = st.selectbox("Selecione um lançamento para apagar:", options=list(opcoes_del.keys()), format_func=lambda x: opcoes_del[x])
            if st.button("🗑️ Apagar Lançamento Selecionado", use_container_width=True):
                excluir_registro(id_para_deletar)
                st.success("Lançamento removido!")
                st.rerun()
    else:
        st.warning("Sem dados para o intervalo selecionado.")
else:
    st.info("Nenhum dado cadastrado.")
