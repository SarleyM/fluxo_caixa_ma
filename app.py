import streamlit as st
import pandas as pd
import os

# Configuração do arquivo local
NOME_ARQUIVO = "fluxo_caixa.xlsx"

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        return pd.read_excel(NOME_ARQUIVO)
    else:
        # Cria a estrutura inicial caso o arquivo não exista
        return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"])

def salvar_dados(df):
    df.to_excel(NOME_ARQUIVO, index=False)

st.title("📊 Fluxo de Caixa (Versão Local)")

# Carrega os dados
df = carregar_dados()

# --- Formulário de Entrada ---
with st.expander("Novo Lançamento"):
    with st.form("form_registro"):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        descricao = col2.text_input("Descrição")
        
        col3, col4 = st.columns(2)
        valor = col3.number_input("Valor", min_value=0.0, step=0.01)
        tipo = col4.selectbox("Tipo", ["Receita", "Despesa"])
        
        categoria = st.selectbox("Categoria", ["Vendas", "Serviços", "Aluguel", "Salários", "Outros"])
        
        if st.form_submit_button("Registrar"):
            # Ajusta o valor se for despesa
            valor_final = valor if tipo == "Receita" else -valor
            
            novo_dado = pd.DataFrame({
                "Data": [pd.to_datetime(data)],
                "Descrição": [descricao],
                "Categoria": [categoria],
                "Valor": [valor_final],
                "Tipo": [tipo]
            })
            
            df = pd.concat([df, novo_dado], ignore_index=True)
            salvar_dados(df)
            st.success("Registrado com sucesso!")
            st.rerun()

# --- Visualização ---
st.divider()
st.subheader("Registros Atuais")
st.dataframe(df, use_container_width=True)

# Cálculo de Saldo
receita = df[df["Valor"] > 0]["Valor"].sum()
despesa = df[df["Valor"] < 0]["Valor"].sum()
saldo = receita + despesa

c1, c2, c3 = st.columns(3)
c1.metric("Receitas", f"R$ {receita:,.2f}")
c2.metric("Despesas", f"R$ {abs(despesa):,.2f}")
c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
