import streamlit as st

# Função para carregar e executar o arquivo Python
def executar_arquivo(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as file:
            codigo = file.read()
            exec(codigo, globals())  
    except Exception as e:
        st.error(f"Erro ao executar o arquivo {caminho}: {e}")


def pagina_cpa():
    executar_arquivo('cpa.py')

def pagina_lote():
    executar_arquivo('lote.py')


# Dicionário de páginas
paginas = {
	"Processo Arquivo Individual": pagina_cpa,
    "Processa Arquivos em Lote": pagina_lote,
    
}

# Menu na barra lateral para navegação
st.sidebar.title("Menu de Navegação")
escolha = st.sidebar.radio("Escolha a página:", list(paginas.keys()))

# Executa a página selecionada
paginas[escolha]()
