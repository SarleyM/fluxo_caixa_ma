import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão Boiani", layout="wide", page_icon="💰")

# --- CSS PARA DEIXAR IDÊNTICO AO SEU LAYOUT ---
st.markdown("""
    <style>
    .stApp { background-color: #111116; color: white; }
    [data-testid="stSidebar"] { background-color: #1A1A22; }
    div.stButton > button:first-child { background-color: #28A745; color: white; width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "fluxo_caixa_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS movimentacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, categoria TEXT, valor REAL, descricao TEXT)')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty: df['data_dt'] = pd.to_datetime(df['data'])
    return df

init_db()
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

# --- SIDEBAR (COM O ÍCONE DA CAIXA) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2850/2850343.png", width=70) # Ícone da Caixa
    st.title("Filtros de Relatório")
    d1 = st.date_input("Início", datetime(2026, 4, 1), format="DD/MM/YYYY")
    d2 = st.date_input("Fim", datetime(2026, 5, 30), format="DD/MM/YYYY")
    
    st.divider()
    df_base = carregar_dados()
    if not df_base.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_base.to_excel(writer, index=False)
        st.download_button("📊 Baixar Excel", output.getvalue(), "fluxo_caixa.xlsx")

# --- CABEÇALHO (COM O BONECO) ---
c_logo, c_tit, c_boneco = st.columns([1, 4, 1])
with c_logo: st.image("https://raw.githubusercontent.com/oseas-rezende/caixa_app/main/logo_boiani.png", width=100)
with c_tit: st.title("Gestão de Fluxo de Caixa")
with c_boneco: st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=70) # Ícone do Boneco

st.divider()

# --- FORMULÁRIO ---
with st.expander("➕ REALIZAR LANÇAMENTO", expanded=True):
    with st.form("form_l", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        dt = col1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        tp = col2.selectbox("Tipo", ["Receita", "Despesa"])
        vl = col3.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        cat = st.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Outros"])
        desc = st.text_input("Descrição")
        if st.form_submit_button("✅ SALVAR LANÇAMENTO"):
            v_final = vl if tp == "Receita" else -vl
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                       (dt.strftime('%Y-%m-%d'), tp, cat, v_final, desc))
            conn.commit()
            conn.close()
            st.rerun()

# --- DASHBOARD (METRICAS E GRÁFICOS) ---
df = carregar_dados()
if not df.empty:
    df_f = df[(df['data_dt'].dt.date >= d1) & (df['data_dt'].dt.date <= d2)]
    if not df_f.empty:
        # Balões
        ent, sai = df_f[df_f['valor']>0]['valor'].sum(), abs(df_f[df_f['valor']<0]['valor'].sum())
        m1, m2, m3 = st.columns(3)
        m1.metric("Entradas", f"R$ {ent:,.2f}")
        m2.metric("Saídas", f"R$ {sai:,.2f}")
        m3.metric("Saldo", f"R$ {ent-sai:,.2f}")
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1: st.plotly_chart(px.pie(df_f[df_f['valor']<0], values=df_f[df_f['valor']<0]['valor'].abs(), names='categoria', hole=0.4, title="Gastos"), use_container_width=True)
        with g2: st.plotly_chart(px.bar(df_f.groupby('data_dt')['valor'].sum().reset_index(), x='data_dt', y='valor', title="Saldo Diário"), use_container_width=True)

        # Tabela com Editar/Excluir
        st.divider()
        for _, row in df_f.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 2, 1])
            r1.write(row['data_dt'].strftime('%d/%m/%Y'))
            r2.write(row['tipo'])
            r3.write(row['categoria'])
            r4.write(f"R$ {abs(row['valor']):.2f}")
            r5.write(row['descricao'])
            b_ed, b_del = r6.columns(2)
            if b_ed.button("✏️", key=f"e{row['id']}"): st.info("Modo edição: use o formulário acima") # Lógica simplificada
            if b_del.button("🗑️", key=f"d{row['id']}"):
                conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],)); conn.commit(); conn.close(); st.rerun()
