import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão Financeira BOIANI", layout="wide", page_icon="💰")

# Estilo para o botão verde de salvar e layout escuro
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
    .stApp { background-color: #0E1117; color: white; }
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

# Controle de estado para edição
if 'edit_item' not in st.session_state:
    st.session_state.edit_item = None

# --- SIDEBAR (COM A CAIXINHA AZUL CORRETA) ---
with st.sidebar:
    # 📦 ESTA É A CAIXA AZUL COM SETA DA SUA FOTO
    st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/256/external-box-delivery-and-logistics-flatart-icons-flat-flatarticons-1.png", width=120)
    
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
        st.download_button("📊 Baixar Relatório XLSX", output.getvalue(), "fluxo_caixa.xlsx", use_container_width=True)

# --- CABEÇALHO ---
col_logo, col_titulo, col_perfil = st.columns([1, 4, 1])

with col_logo:
    st.image("https://raw.githubusercontent.com/oseas-rezende/caixa_app/main/logo_boiani.png", width=100) 

with col_titulo:
    st.title("Gestão de Fluxo de Caixa BOIANI")

with col_perfil:
    # 👤 ÍCONE DO PERFIL AZUL
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80) 

st.markdown("---")

# --- FORMULÁRIO (DINÂMICO PARA NOVO OU EDITAR) ---
if st.session_state.edit_item:
    label = "📝 EDITAR LANÇAMENTO"
    dados = st.session_state.edit_item
else:
    label = "➕ REALIZAR NOVO LANÇAMENTO"
    dados = {"data": datetime.now(), "tipo": "Receita", "valor": 0.0, "categoria": "Vendas", "descricao": ""}

with st.expander(label, expanded=True):
    with st.form("form_financeiro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input("Data", value=pd.to_datetime(dados['data']), format="DD/MM/YYYY")
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"], index=0 if dados['tipo'] == "Receita" else 1)
        vl = c3.number_input("Valor (R$)", value=abs(float(dados['valor'])), min_value=0.0, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        categorias = ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"]
        cat = c4.selectbox("Categoria", categorias, index=categorias.index(dados['categoria']) if dados['categoria'] in categorias else 0)
        desc = c5.text_input("Descrição / Detalhes", value=dados['descricao'])
        
        col_btn1, col_btn2 = st.columns([1, 0.2])
        if col_btn1.form_submit_button("✅ SALVAR DADOS"):
            v_final = vl if tp == "Receita" else -vl
            conn = sqlite3.connect(DB_NAME)
            if st.session_state.edit_item:
                conn.execute("UPDATE movimentacoes SET data=?, tipo=?, categoria=?, valor=?, descricao=? WHERE id=?",
                           (dt.strftime('%Y-%m-%d'), tp, cat, v_final, desc, dados['id']))
                st.session_state.edit_item = None
            else:
                conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                           (dt.strftime('%Y-%m-%d'), tp, cat, v_final, desc))
            conn.commit()
            conn.close()
            st.rerun()
        
        if st.session_state.edit_item:
            if col_btn2.form_submit_button("CANCELAR"):
                st.session_state.edit_item = None
                st.rerun()

# --- DASHBOARD E LISTAGEM ---
df_total = carregar_dados()
if not df_total.empty:
    df_f = df_total[(df_total['data_dt'].dt.date >= data_inicio) & (df_total['data_dt'].dt.date <= data_fim)].copy()
    
    if not df_f.empty:
        # Resumo
        rec, desp = df_f[df_f["valor"] > 0]["valor"].sum(), abs(df_f[df_f["valor"] < 0]["valor"].sum())
        m1, m2, m3 = st.columns(3)
        m1.metric("Entradas", f"R$ {rec:,.2f}")
        m2.metric("Saídas", f"R$ {desp:,.2f}")
        m3.metric("Saldo Líquido", f"R$ {rec-desp:,.2f}")

        # Tabela Detalhada com Botão Editar na Frente
        st.markdown("### 📋 Histórico de Movimentações")
        
        # Cabeçalho manual da tabela
        h1, h2, h3, h4, h5, h6 = st.columns([0.5, 1, 1, 1, 2, 1])
        h1.write("**Ação**")
        h2.write("**Data**")
        h3.write("**Tipo**")
        h4.write("**Valor**")
        h5.write("**Descrição**")
        h6.write("**Excluir**")

        for _, row in df_f.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([0.5, 1, 1, 1, 2, 1])
            
            # Botão EDITAR (Na frente como pedido)
            if r1.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_item = row
                st.rerun()
                
            r2.write(row['data_dt'].strftime('%d/%m/%Y'))
            r3.write(row['tipo'])
            cor = "green" if row['valor'] > 0 else "red"
            r4.markdown(f":{cor}[R$ {abs(row['valor']):,.2f}]")
            r5.write(row['descricao'])
            
            # Botão EXCLUIR
            if r6.button("🗑️", key=f"del_{row['id']}"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
