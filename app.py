import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fluxo de Caixa - BOIANI", layout="wide", page_icon="💰")

# --- ESTILO PARA O BOTÃO VERDE ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #28A745;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "fluxo_caixa_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS movimentacoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, categoria TEXT, valor REAL, descricao TEXT)''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
    return df

init_db()

# --- SIDEBAR (COM A CAIXINHA AZUL) ---
with st.sidebar:
    # 📦 A CAIXINHA AZUL QUE VOCÊ QUERIA
    st.image("https://cdn-icons-png.flaticon.com/512/2850/2850343.png", width=100) 
    st.title("Filtros de Relatório")
    
    data_inicio = st.date_input("Início", datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", datetime(2026, 4, 28), format="DD/MM/YYYY")
    
    st.divider()
    st.markdown("### 📥 Exportar")
    df_base = carregar_dados()
    if not df_base.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_base.to_excel(writer, index=False)
        st.download_button("📊 Baixar XLSX", output.getvalue(), "fluxo_caixa.xlsx", use_container_width=True)

# --- CABEÇALHO (COM O BONECO AZUL) ---
col_logo, col_titulo, col_boneco = st.columns([1, 4, 1])

with col_logo:
    # Sua logo oficial
    st.image("https://raw.githubusercontent.com/oseas-rezende/caixa_app/main/logo_boiani.png", width=100) 

with col_titulo:
    st.title("Gestão de Fluxo de Caixa BOIANI")

with col_boneco:
    # 👤 ÍCONE DO BONECO AZUL (Suporte/Usuário)
    st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=80) 

st.markdown("---")

# --- FORMULÁRIO ---
with st.expander("➕ Realizar Novo Lançamento", expanded=True):
    with st.form("form_registro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt_reg = c1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        tp_reg = c2.selectbox("Tipo", ["Receita", "Despesa"])
        vl_reg = c3.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat_reg = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"])
        desc_reg = c5.text_input("Descrição / Detalhes", placeholder="Ex: Pão caseiro")
        
        if st.form_submit_button("✅ Salvar Lançamento"):
            vl_final = vl_reg if tp_reg == "Receita" else -vl_reg
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                       (dt_reg.strftime('%Y-%m-%d'), tp_reg, cat_reg, vl_final, desc_reg))
            conn.commit()
            conn.close()
            st.success("Salvo!")
            st.rerun()

# --- HISTÓRICO COM BOTÕES DE AÇÃO ---
df_total = carregar_dados()
if not df_total.empty:
    df = df_total[(df_total['data_dt'].dt.date >= data_inicio) & (df_total['data_dt'].dt.date <= data_fim)].copy()
    
    if not df.empty:
        st.subheader("📋 Movimentações Detalhadas")
        
        # Cabeçalho da tabela manual
        h1, h2, h3, h4, h5, h6 = st.columns([1, 1, 1, 1, 2, 1])
        h1.write("**Data**")
        h2.write("**Tipo**")
        h3.write("**Categoria**")
        h4.write("**Valor**")
        h5.write("**Descrição**")
        h6.write("**Ações**")

        for _, row in df.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 2, 1])
            r1.write(row['data_dt'].strftime('%d/%m/%Y'))
            r2.write(row['tipo'])
            r3.write(row['categoria'])
            cor = "green" if row['valor'] > 0 else "red"
            r4.markdown(f":{cor}[R$ {abs(row['valor']):,.2f}]")
            r5.write(row['descricao'])
            
            # Botões Editar e Excluir
            btn_ed, btn_del = r6.columns(2)
            if btn_ed.button("✏️", key=f"ed_{row['id']}"):
                st.info("Função de edição ativa no formulário (em breve)")
            if btn_del.button("🗑️", key=f"del_{row['id']}"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
