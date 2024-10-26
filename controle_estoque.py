import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Estilização do Streamlit
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .css-1lcbmhc {background-color: #1E1E1E;}
    .css-1d391kg {background-color: #272727;}
    .css-16huue1 {background-color: #1E1E1E;}
    .css-1v3fvcr {background-color: #1E1E1E;}
    </style>
    """,
    unsafe_allow_html=True
)

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('estoque.db')
cursor = conn.cursor()

# Criar tabela de produtos, se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        preco REAL,
        quantidade INTEGER
    )
''')
conn.commit()

# Criar tabela de vendas, se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_produto TEXT,
        quantidade INTEGER,
        preco_total REAL,
        data_venda TEXT
    )
''')
conn.commit()

# Simulação de produtos e vendas
def simular_dados():
    produtos_simulados = [
        ("Mouse", 49.9, 30),
        ("Teclado", 99.9, 20),
        ("Monitor", 599.9, 10),
        ("Headset", 199.9, 15),
        ("Webcam", 129.9, 25)
    ]
    for nome, preco, quantidade in produtos_simulados:
        cursor.execute('INSERT OR IGNORE INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)', 
                       (nome, preco, quantidade))
    conn.commit()

    vendas_simuladas = [
        ("Mouse", 5, 249.5, "2024-10-20 14:30:00"),
        ("Teclado", 3, 299.7, "2024-10-21 10:00:00"),
        ("Monitor", 2, 1199.8, "2024-10-22 09:45:00"),
        ("Headset", 4, 799.6, "2024-10-22 11:00:00"),
        ("Webcam", 3, 389.7, "2024-10-23 16:00:00")
    ]
    for nome_produto, quantidade, preco_total, data_venda in vendas_simuladas:
        cursor.execute('INSERT OR IGNORE INTO vendas (nome_produto, quantidade, preco_total, data_venda) VALUES (?, ?, ?, ?)',
                       (nome_produto, quantidade, preco_total, data_venda))
    conn.commit()

# Simular dados se estiver vazio
simular_dados()

# Função para obter a lista de produtos
def obter_produtos():
    cursor.execute('SELECT nome FROM produtos')
    produtos = cursor.fetchall()
    return [produto[0] for produto in produtos]

# Função para obter os dados de um produto específico
def obter_dados_produto(nome):
    cursor.execute('SELECT * FROM produtos WHERE nome = ?', (nome,))
    return cursor.fetchone()

# Função para cadastrar uma venda e atualizar o estoque
def cadastrar_venda(nome, quantidade_venda):
    produto = obter_dados_produto(nome)
    if produto:
        preco_unitario = produto[2]
        quantidade_estoque = produto[3]

        if quantidade_venda > quantidade_estoque:
            st.error(f"Quantidade insuficiente em estoque. Disponível: {quantidade_estoque}")
        else:
            # Atualizar estoque
            nova_quantidade = quantidade_estoque - quantidade_venda
            cursor.execute('UPDATE produtos SET quantidade = ? WHERE nome = ?', (nova_quantidade, nome))
            conn.commit()

            # Registrar venda
            preco_total = preco_unitario * quantidade_venda
            data_venda = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('INSERT INTO vendas (nome_produto, quantidade, preco_total, data_venda) VALUES (?, ?, ?, ?)',
                           (nome, quantidade_venda, preco_total, data_venda))
            conn.commit()

            st.success(f"Venda de {quantidade_venda} unidades de '{nome}' cadastrada com sucesso!")

# Função para visualizar o estoque de forma organizada
def visualizar_estoque():
    cursor.execute('SELECT nome, preco, quantidade FROM produtos')
    produtos = cursor.fetchall()
    if produtos:
        df = pd.DataFrame(produtos, columns=['Nome do Produto', 'Preço', 'Quantidade'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("O estoque está vazio.")

# Função para visualizar as vendas registradas
def visualizar_vendas():
    cursor.execute('SELECT nome_produto, quantidade, preco_total, data_venda FROM vendas')
    vendas = cursor.fetchall()
    if vendas:
        df = pd.DataFrame(vendas, columns=['Produto', 'Quantidade', 'Preço Total', 'Data da Venda'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada.")

# Função para criar a dashboard de vendas aprimorada
def criar_dashboard():
    cursor.execute('SELECT nome_produto, SUM(quantidade), SUM(preco_total) FROM vendas GROUP BY nome_produto')
    vendas_produtos = cursor.fetchall()

    if vendas_produtos:
        df_vendas = pd.DataFrame(vendas_produtos, columns=['Produto', 'Quantidade Vendida', 'Total de Vendas'])
        
        # Resumo das vendas
        total_vendas = df_vendas['Total de Vendas'].sum()
        total_produtos_vendidos = df_vendas['Quantidade Vendida'].sum()
        produto_mais_vendido = df_vendas.loc[df_vendas['Quantidade Vendida'].idxmax(), 'Produto']

        # Criar cards de resumo
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Produtos Vendidos", total_produtos_vendidos)
        with col2:
            st.metric("Total em Vendas (R$)", f"{total_vendas:.2f}")
        with col3:
            st.metric("Produto Mais Vendido", produto_mais_vendido)

        # Gráfico de quantidade vendida por produto
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=df_vendas, x='Produto', y='Quantidade Vendida', palette='coolwarm', ax=ax)
        ax.set_title('Quantidade Vendida por Produto', fontsize=16, color='white', pad=20)
        ax.set_xlabel('Produto', fontsize=12, color='white')
        ax.set_ylabel('Quantidade Vendida', fontsize=12, color='white')
        ax.tick_params(colors='white')
        fig.patch.set_facecolor('#1E1E1E')
        ax.set_facecolor('#272727')
        for p in ax.patches:
            ax.annotate(int(p.get_height()), (p.get_x() + p.get_width() / 2, p.get_height()),
                        ha='center', va='bottom', color='white')
        st.pyplot(fig)

        # Gráfico de vendas por data
        cursor.execute('SELECT data_venda, SUM(quantidade) FROM vendas GROUP BY data_venda')
        vendas_por_data = cursor.fetchall()

        if vendas_por_data:
            df_vendas_data = pd.DataFrame(vendas_por_data, columns=['Data da Venda', 'Quantidade Vendida'])
            df_vendas_data['Data da Venda'] = pd.to_datetime(df_vendas_data['Data da Venda'])

            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=df_vendas_data, x='Data da Venda', y='Quantidade Vendida', marker='o', color='orange', ax=ax)
            ax.set_title('Quantidade Vendida ao Longo do Tempo', fontsize=16, color='white', pad=20)
            ax.set_xlabel('Data da Venda', fontsize=12, color='white')
            ax.set_ylabel('Quantidade Vendida', fontsize=12, color='white')
            ax.tick_params(colors='white')
            fig.patch.set_facecolor('#1E1E1E')
            ax.set_facecolor('#272727')
            st.pyplot(fig)
    else:
        st.info("Nenhuma venda registrada para gerar a dashboard.")

# Interface do usuário com Streamlit
st.title("Sistema de Controle de Estoque e Vendas")

# Menu principal de opções
opcao = st.sidebar.selectbox(
    "Selecione uma opção",
    ["Adicionar Produto", "Atualizar Produto", "Excluir Produto", "Vendas"]
)

if opcao == "Adicionar Produto":
    st.header("Adicionar Produto")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço do Produto", min_value=0.0, step=0.01)
    quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
    if st.button("Adicionar"):
        cursor.execute('INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)', (nome, preco, quantidade))
        conn.commit()
        st.success(f"Produto '{nome}' adicionado com sucesso!")

elif opcao == "Atualizar Produto":
    st.header("Atualizar Produto")
    
    produtos_existentes = obter_produtos()
    nome_selecionado = st.selectbox("Selecione um Produto para Atualizar", options=produtos_existentes)
    nome_digitado = st.text_input("Ou digite o nome do produto")
    nome = nome_digitado if nome_digitado else nome_selecionado

    preco = st.number_input("Novo Preço do Produto", min_value=0.0, step=0.01)
    quantidade = st.number_input("Nova Quantidade em Estoque", min_value=0, step=1)
    
    if st.button("Atualizar"):
        cursor.execute('UPDATE produtos SET preco = ?, quantidade = ? WHERE nome = ?', (preco, quantidade, nome))
        conn.commit()
        st.success(f"Produto '{nome}' atualizado com sucesso!")

elif opcao == "Excluir Produto":
    st.header("Excluir Produto")
    
    produtos_existentes = obter_produtos()
    nome_selecionado = st.selectbox("Selecione um Produto para Excluir", options=produtos_existentes)
    nome_digitado = st.text_input("Ou digite o nome do produto")
    nome = nome_digitado if nome_digitado else nome_selecionado

    excluir_tudo = st.checkbox("Excluir todo o produto")
    if not excluir_tudo:
        quantidade_excluir = st.number_input("Quantidade a ser removida", min_value=1, step=1)
    else:
        quantidade_excluir = None

    if st.button("Excluir"):
        if excluir_tudo:
            cursor.execute('DELETE FROM produtos WHERE nome = ?', (nome,))
        else:
            produto = obter_dados_produto(nome)
            if produto and quantidade_excluir <= produto[3]:
                nova_quantidade = produto[3] - quantidade_excluir
                cursor.execute('UPDATE produtos SET quantidade = ? WHERE nome = ?', (nova_quantidade, nome))
            else:
                st.error("Quantidade insuficiente ou produto inexistente.")
        conn.commit()
        st.success(f"Produto '{nome}' excluído com sucesso!")

elif opcao == "Vendas":
    st.header("Gerenciamento de Vendas")

    sub_opcao = st.radio(
        "Escolha uma ação",
        ["Cadastrar Venda", "Visualizar Vendas", "Dashboard de Vendas"]
    )

    if sub_opcao == "Cadastrar Venda":
        st.subheader("Cadastrar Venda")
        
        produtos_existentes = obter_produtos()
        nome = st.selectbox("Selecione o Produto", options=produtos_existentes)
        quantidade_venda = st.number_input("Quantidade a Vender", min_value=1, step=1)
        
        if st.button("Vender"):
            cadastrar_venda(nome, quantidade_venda)

    elif sub_opcao == "Visualizar Vendas":
        st.subheader("Vendas Registradas")
        visualizar_vendas()

    elif sub_opcao == "Dashboard de Vendas":
        st.subheader("Dashboard de Vendas")
        criar_dashboard()

# Botões separados para Visualizar Estoque e Sair
if st.sidebar.button("Visualizar Estoque"):
    st.header("Visualizar Estoque")
    visualizar_estoque()

if st.sidebar.button("Sair"):
    st.write("Obrigado por utilizar o sistema de controle de estoque e vendas!")

# Fechar a conexão com o banco de dados ao finalizar
conn.close()
