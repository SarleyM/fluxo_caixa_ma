import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão Financeira", layout="wide")

DB_NAME = "fluxo_caixa_v2.db"

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

def excluir_registro(id_reg):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM movimentacoes WHERE id=?", (id_reg,))
    conn.commit()
    conn.close()
    st.rerun()

init_db()

# --- ESTADO DE EDIÇÃO ---
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- SIDEBAR (Filtros e Exportação) ---
with st.sidebar:
    st.title("Filtros")
    data_inicio = st.date_input("Início", datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", datetime(2026, 5, 30), format="DD/MM/YYYY")
    
    st.markdown("---")
    df_base = carregar_dados()
    if not df_base.empty:
        output = io.BytesIO()
        # IMPORTANTE: Use 'openpyxl' como alternativa se o xlsxwriter der erro
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export = df_base.copy()
                df_export['data'] = pd.to_datetime(df_export['data']).dt.strftime('%d/%m/%Y')
                df_export[['data', 'tipo', 'categoria', 'valor', 'descricao']].to_excel(writer, index=False)
        except:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_base.to_excel(writer, index=False)
        
        st.download_button("📥 Baixar Excel", output.getvalue(), "fluxo_caixa.xlsx", 
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- FORMULÁRIO (DINÂMICO PARA NOVO OU EDITAR) ---
titulo_form = "📝 Editar Lançamento" if st.session_state.edit_id else "➕ Novo Lançamento"
with st.expander(titulo_form, expanded=True):
    # Busca dados se estiver editando
    dados_edicao = {"data": datetime.now(), "tipo": "Receita", "valor": 0.0, "cat": "Outros", "desc": ""}
    if st.session_state.edit_id:
        conn = sqlite3.connect(DB_NAME)
        res = conn.execute("SELECT * FROM movimentacoes WHERE id=?", (st.session_state.edit_id,)).fetchone()
        conn.close()
        if res:
            dados_edicao = {"data": datetime.strptime(res[1], '%Y-%m-%d'), "tipo": res[2], "cat": res[3], "valor": abs(res[4]), "desc": res[5]}

    with st.form("form_financeiro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input("Data", dados_edicao["data"], format="DD/MM/YYYY")
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"], index=0 if dados_edicao["tipo"]=="Receita" else 1)
        vl = c3.number_input("Valor", value=dados_edicao["valor"], min_value=0.0, step=0.01, format="%.2f")
        
        cat = st.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Outros"], 
                           index=["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Outros"].index(dados_edicao["cat"]))
        desc = st.text_input("Descrição", value=dados_edicao["desc"])
        
        col_btn1, col_btn2 = st.columns([1, 0.2])
        if st.form_submit_button("✅ Salvar Lançamento", use_container_width=True):
            vl_final = vl if tp == "Receita" else -vl
            conn = sqlite3.connect(DB_NAME)
            if st.session_state.edit_id:
                conn.execute("UPDATE movimentacoes SET data=?, tipo=?, categoria=?, valor=?, descricao=? WHERE id=?",
                           (dt.strftime('%Y-%m-%d'), tp, cat, vl_final, desc, st.session_state.edit_id))
                st.session_state.edit_id = None
            else:
                conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                           (dt.strftime('%Y-%m-%d'), tp, cat, vl_final, desc))
            conn.commit()
            conn.close()
            st.rerun()
        
        if st.session_state.edit_id:
            if st.form_submit_button("Cancelar Edição"):
                st.session_state.edit_id = None
                st.rerun()

# --- TABELA COM BOTÕES DE AÇÃO ---
st.markdown("### 📋 Histórico de Movimentações")
df = carregar_dados()

if not df.empty:
    df_filt = df[(df['data_dt'].dt.date >= data_inicio) & (df['data_dt'].dt.date <= data_fim)].copy()
    
    # Cabeçalho da tabela manual
    h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1, 1.2, 1, 2, 1])
    h1.write("**Data**")
    h2.write("**Tipo**")
    h3.write("**Categoria**")
    h4.write("**Valor**")
    h5.write("**Descrição**")
    h6.write("**Ações**")
    st.divider()

    for _, row in df_filt.iterrows():
        r1, r2, r3, r4, r5, r6 = st.columns([1.2, 1, 1.2, 1, 2, 1])
        
        r1.write(row['data_dt'].strftime('%d/%m/%Y'))
        r2.write(row['tipo'])
        r3.write(row['categoria'])
        cor = "green" if row['valor'] > 0 else "red"
        r4.write(f":{cor}[R$ {abs(row['valor']):.2f}]")
        r5.write(row['descricao'])
        
        # Botões de Ação
        btn_col1, btn_col2 = r6.columns(2)
        if btn_col1.button("✏️", key=f"edit_{row['id']}"):
            st.session_state.edit_id = row['id']
            st.rerun()
        if btn_col2.button("🗑️", key=f"del_{row['id']}"):
            excluir_registro(row['id'])
else:
    st.info("Nenhum dado encontrado.")
