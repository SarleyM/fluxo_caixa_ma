import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa - BOIANI", layout="wide", page_icon="💰")

# --- BANCO DE DADOS ---
DB_NAME = "fluxo_caixa_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS movimentacoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, categoria TEXT, valor REAL, descricao TEXT)''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.to_sql = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
    return df

init_db()

# --- ESTADO DE EDIÇÃO ---
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- SIDEBAR (LAYOUT DA SEGUNDA IMAGEM) ---
with st.sidebar:
    # 🧴 ÍCONE DOS PRODUTOS DE LIMPEZA (Conforme a 2ª imagem enviada)
    st.image("https://cdn-icons-png.flaticon.com/512/2554/2554042.png", width=100) 
    st.title("Filtros de Relatório")
    
    data_inicio = st.date_input("Início", datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", datetime(2026, 5, 30), format="DD/MM/YYYY")
    
    st.divider()
    st.markdown("### 📥 Exportar")
    df_base = carregar_dados()
    if not df_base.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_base.to_excel(writer, index=False)
        st.download_button("📊 Gerar Relatório", output.getvalue(), "fluxo_caixa.xlsx")

# --- CABEÇALHO ---
col_logo, col_titulo, col_boneco = st.columns([1, 4, 1])

with col_logo:
    st.image("https://raw.githubusercontent.com/oseas-rezende/caixa_app/main/logo_boiani.png", width=100) 

with col_titulo:
    st.title("Gestão de Fluxo de Caixa")

with col_boneco:
    # 👤 ÍCONE DO BONECO (Conforme o layout original)
    st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=70) 

st.markdown("---")

# --- FORMULÁRIO (ESTILO SEGUNDA IMAGEM) ---
with st.expander("➕ Realizar Novo Lançamento", expanded=st.session_state.edit_id is None):
    with st.form("form_financeiro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
        vl = c3.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Outros"])
        desc = c5.text_input("Descrição / Detalhes", placeholder="Ex: Pão caseiro")
        
        if st.form_submit_button("✅ Salvar Lançamento", use_container_width=True):
            v_final = vl if tp == "Receita" else -vl
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                       (dt.strftime('%Y-%m-%d'), tp, cat, v_final, desc))
            conn.commit()
            conn.close()
            st.rerun()

# --- DASHBOARD DE RESUMO (BALÕES) ---
df_bruto = carregar_dados()
if not df_bruto.empty:
    df = df_bruto[(df_bruto['data_dt'].dt.date >= data_inicio) & (df_bruto['data_dt'].dt.date <= data_fim)].copy()
    
    if not df.empty:
        # Balões de Métricas
        rec = df[df["valor"] > 0]["valor"].sum()
        desp = abs(df[df["valor"] < 0]["valor"].sum())
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Entradas", f"R$ {rec:,.2f}")
        m2.metric("Total Saídas", f"R$ {desp:,.2f}")
        m3.metric("Saldo Líquido", f"R$ {rec-desp:,.2f}")

        # Gráficos (Que você pediu para voltar)
        st.markdown("### 📈 Visualização")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df[df['valor']<0], values=df[df['valor']<0]['valor'].abs(), names='categoria', hole=0.4, title="Gastos"), use_container_width=True)
        with g2:
            st.plotly_chart(px.bar(df.groupby('data_dt')['valor'].sum().reset_index(), x='data_dt', y='valor', title="Evolução Diária"), use_container_width=True)

        # --- TABELA COM BOTÃO EDITAR ---
        st.markdown("### 📋 Histórico")
        for _, row in df.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 2, 1])
            r1.write(row['data_dt'].strftime('%d/%m/%Y'))
            r2.write(row['tipo'])
            r3.write(row['categoria'])
            r4.write(f"R$ {abs(row['valor']):.2f}")
            r5.write(row['descricao'])
            
            # Ações: Editar e Excluir
            ed, lixo = r6.columns(2)
            if ed.button("✏️", key=f"e_{row['id']}"):
                st.info("Para editar, altere os dados no formulário acima e salve.")
            if lixo.button("🗑️", key=f"d_{row['id']}"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
