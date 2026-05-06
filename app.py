import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA (Layout Largo e Tema Escuro Nativo) ---
st.set_page_config(
    page_title="Fluxo de Caixa - BOIANI",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💰"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    /* Fundo da aplicação */
    .stApp {
        background-color: #111116;
        color: #FFFFFF;
    }
    /* Estilização do Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1A1A22;
        border-right: 1px solid #303030;
    }
    /* Títulos e Subtítulos */
    h1, h2, h3 {
        color: #FFFFFF !important;
    }
    /* Botão Principal Verde (Salvar Lançamento) */
    div.stButton > button:first-child {
        background-color: #28A745;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #218838;
    }
    /* Inputs, Selectbox e DateInput */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #22222A !important;
        border-radius: 5px;
    }
    /* Estilo para os botões de ação na tabela (Editar/Excluir) */
    .stButton > button {
        padding: 2px 8px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS (SQLITE) ---
DB_NAME = "fluxo_caixa_v3.db"

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

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
    return df

def salvar_registro(data, tipo, categoria, valor, descricao, id_registro=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    valor_final = valor if tipo == "Receita" else -abs(valor)
    if id_registro:
        c.execute('''
            UPDATE movimentacoes 
            SET data=?, tipo=?, categoria=?, valor=?, descricao=? 
            WHERE id=?
        ''', (data.strftime('%Y-%m-%d'), tipo, categoria, valor_final, descricao, id_registro))
    else:
        c.execute('''
            INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao)
            VALUES (?, ?, ?, ?, ?)
        ''', (data.strftime('%Y-%m-%d'), tipo, categoria, valor_final, descricao))
    conn.commit()
    conn.close()

def excluir_registro(id_registro):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM movimentacoes WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()

init_db()

# --- ESTADO DA SESSÃO (PARA EDIÇÃO) ---
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None
if 'dados_form' not in st.session_state:
    st.session_state.dados_form = {}

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    # URL da logo conforme a imagem. Substitua pelo caminho local se preferir.
    st.image("https://raw.githubusercontent.com/oseas-rezende/caixa_app/main/logo_boiani.png", width=120)
with col_titulo:
    st.title("Gestão de Fluxo de Caixa")

st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🗓️ Filtros de Relatório")
    data_inicio = st.date_input("Início", value=datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", value=datetime(2026, 4, 28), format="DD/MM/YYYY")
    
    st.markdown("---")
    st.markdown("### 📥 Exportar")
    
    df_base = carregar_dados()
    if not df_base.empty:
        # Gera EXCEL Real (XLSX)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export = df_base.copy()
            df_export['data'] = pd.to_datetime(df_export['data']).dt.strftime('%d/%m/%Y')
            df_export[['data', 'tipo', 'categoria', 'valor', 'descricao']].to_excel(writer, index=False, sheet_name='Fluxo de Caixa')
        
        st.download_button(
            label="📊 Baixar Relatório Excel",
            data=output.getvalue(),
            file_name=f"fluxo_caixa_boiani_{data_inicio.strftime('%d%m')}_{data_fim.strftime('%d%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# --- FORMULÁRIO DE LANÇAMENTO (Fiel à imagem) ---
expander_label = "➕ Realizar Novo Lançamento" if st.session_state.editing_id is None else "📝 Editar Lançamento"
with st.expander(expander_label, expanded=(st.session_state.editing_id is not None)):
    
    # Preenche o formulário se estiver em modo de edição
    if st.session_state.editing_id and not st.session_state.dados_form:
        conn = sqlite3.connect(DB_NAME)
        res = conn.execute("SELECT * FROM movimentacoes WHERE id=?", (st.session_state.editing_id,)).fetchone()
        conn.close()
        if res:
            st.session_state.dados_form = {
                "data": datetime.strptime(res[1], '%Y-%m-%d'),
                "tipo": res[2],
                "cat": res[3],
                "valor": abs(res[4]),
                "desc": res[5]
            }
    elif not st.session_state.editing_id:
        st.session_state.dados_form = {
            "data": datetime.now(),
            "tipo": "Receita",
            "cat": "Vendas",
            "valor": 0.0,
            "desc": ""
        }

    with st.form("form_lancamento", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        dt_lan = c1.date_input("Data", value=st.session_state.dados_form.get("data"), format="DD/MM/YYYY")
        tipo_lan = c2.selectbox("Tipo", ["Receita", "Despesa"], index=(0 if st.session_state.dados_form.get("tipo") == "Receita" else 1))
        
        # Campo de valor numérico. Para a máscara automática, o Streamlit nativo não suporta,
        # mas este campo aceita apenas números e formata com duas casas decimais.
        valor_lan = c3.number_input("Valor (R$)", value=st.session_state.dados_form.get("valor"), min_value=0.0, step=0.01, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat_lan = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"], 
                               index=["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"].index(st.session_state.dados_form.get("cat", "Outros")))
        desc_lan = c5.text_input("Descrição / Detalhes", value=st.session_state.dados_form.get("desc"), placeholder="Ex: Pão caseiro")
        
        c_btn1, c_btn2 = st.columns([1, 0.2])
        submit = c_btn1.form_submit_button("✅ Salvar Lançamento", use_container_width=True)
        
        # Botão de cancelar edição
        if st.session_state.editing_id:
            if c_btn2.form_submit_button("Cancelar"):
                st.session_state.editing_id = None
                st.session_state.dados_form = {}
                st.rerun()

        if submit:
            if valor_lan > 0:
                salvar_registro(dt_lan, tipo_lan, cat_lan, valor_lan, desc_lan, st.session_state.editing_id)
                st.session_state.editing_id = None # Limpa estado de edição
                st.session_state.dados_form = {}
                st.success("Lançamento salvo com sucesso!")
                st.rerun()
            else:
                st.warning("O valor deve ser maior que zero.")

# --- VISUALIZAÇÃO DOS DADOS FILTRADOS ---
df_total = carregar_dados()

if not df_total.empty:
    st.markdown("---")
    st.subheader("📊 Movimentações do Período")
    
    # Filtro usando a coluna oculta de datetime
    mask = (df_total['data_dt'].dt.date >= data_inicio) & (df_total['data_dt'].dt.date <= data_fim)
    df = df_total.loc[mask].copy()

    if not df.empty:
        # Métricas rápidas (Dashboard simples)
        rec = df[df["valor"] > 0]["valor"].sum()
        desp = df[df["valor"] < 0]["valor"].sum()
        saldo = rec + desp

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total de Entradas", f"R$ {rec:,.2f}")
        col_m2.metric("Total de Saídas", f"R$ {abs(desp):,.2f}", delta_color="inverse")
        col_m3.metric("Saldo do Período", f"R$ {saldo:,.2f}")
        
        st.divider()

        # --- TABELA DE HISTÓRICO COM BOTÕES DE AÇÃO ---
        # Criamos colunas manuais para simular uma tabela com botões nas linhas
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
            # Aplica cor verde para receita e vermelha para despesa
            cor = "green" if row['valor'] > 0 else "red"
            r4.write(f":{cor}[R$ {abs(row['valor']):,.2f}]")
            r5.write(row['descricao'])
            
            # Botões de Ação (Editar e Excluir)
            btn_edit_col, btn_del_col = r6.columns(2)
            if btn_edit_col.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.editing_id = row['id']
                st.session_state.dados_form = {} # Força a recarga dos dados do banco
                st.rerun()
            if btn_del_col.button("🗑️", key=f"del_{row['id']}"):
                excluir_registro(row['id'])
                st.warning(f"Lançamento '{row['descricao']}' excluído.")
                st.rerun()
    else:
        st.info("Nenhum lançamento encontrado para o período filtrado.")
else:
    st.info("O banco de dados está vazio. Comece realizando um novo lançamento!")
