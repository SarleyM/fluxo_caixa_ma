import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÕES DO ARQUIVO ---
ARQUIVO_EXCEL = "fluxo_caixa_local.xlsx"

def carregar_dados():
    """Carrega o arquivo Excel ou cria um novo DataFrame se não existir."""
    if os.path.exists(ARQUIVO_EXCEL):
        try:
            df = pd.read_excel(ARQUIVO_EXCEL)
            # Garante que a coluna de Data esteja no formato correto
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except Exception:
            return criar_dataframe_vazio()
    else:
        return criar_dataframe_vazio()

def criar_dataframe_vazio():
    return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"])

def salvar_dados(df):
    """Salva o DataFrame no arquivo Excel local."""
    df.to_excel(ARQUIVO_EXCEL, index=False)

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Fluxo de Caixa Profissional", layout="wide")

st.title("📊 Gestão de Fluxo de Caixa")
st.info("Os dados estão sendo salvos localmente no arquivo: " + ARQUIVO_EXCEL)

# Inicialização dos dados
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# --- ÁREA DE LANÇAMENTO ---
with st.sidebar:
    st.header("Novo Lançamento")
    with st.form("form_novo_registro", clear_on_submit=True):
        data_sel = st.date_input("Data", datetime.now())
        desc_sel = st.text_input("Descrição (Ex: Venda de produto)")
        valor_sel = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        tipo_sel = st.selectbox("Tipo", ["Receita", "Despesa"])
        cat_sel = st.selectbox("Categoria", ["Vendas", "Serviços", "Aluguel", "Infraestrutura", "Marketing", "Outros"])
        
        btn_enviar = st.form_submit_button("Salvar Registro")
        
        if btn_enviar:
            if desc_sel == "" or valor_sel == 0:
                st.error("Preencha a descrição e o valor!")
            else:
                # Ajusta o sinal do valor conforme o tipo
                valor_final = valor_sel if tipo_sel == "Receita" else -valor_sel
                
                novo_registro = {
                    "Data": pd.to_datetime(data_sel),
                    "Descrição": desc_sel,
                    "Categoria": cat_sel,
                    "Valor": valor_final,
                    "Tipo": tipo_sel
                }
                
                # Atualiza o DataFrame
                st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([novo_registro])], ignore_index=True)
                salvar_dados(st.session_state.dados)
                st.success("Lançamento realizado!")
                st.rerun()

# --- DASHBOARD E VISUALIZAÇÃO ---
df_exibicao = st.session_state.dados.copy()

if not df_exibicao.empty:
    # Métricas principais
    receitas = df_exibicao[df_exibicao["Valor"] > 0]["Valor"].sum()
    despesas = df_exibicao[df_exibicao["Valor"] < 0]["Valor"].sum()
    saldo_total = receitas + despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas Totais", f"R$ {receitas:,.2f}")
    col2.metric("Despesas Totais", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
    col3.metric("Saldo em Caixa", f"R$ {saldo_total:,.2f}")

    st.divider()

    # Tabela de registros
    st.subheader("Histórico de Movimentações")
    # Formatação para exibição
    df_formatado = df_exibicao.sort_values(by="Data", ascending=False)
    st.dataframe(df_formatado, use_container_width=True)

    # Botão para limpar tudo (Cuidado!)
    if st.button("Limpar Todos os Dados"):
        if st.checkbox("Tenho certeza que desejo apagar o arquivo local"):
            st.session_state.dados = criar_dataframe_vazio()
            salvar_dados(st.session_state.dados)
            st.warning("Dados apagados.")
            st.rerun()
else:
    st.write("Nenhum lançamento encontrado. Use o menu lateral para começar.")
