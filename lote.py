import streamlit as st
import zipfile
import pandas as pd
import io
import re
import unicodedata
import json

with open('mapping_cursos.json', 'r', encoding='utf-8') as f:
    mapping_cursos = json.load(f)


st.title("Processamento em LOTE TODOS CURSOS por período")

st.markdown("""
    <div style="border: 1px solid #FF5733; padding: 15px; background-color: #FFE6E6; border-radius: 10px;">
        <p style="color: #8B0000;">Todos os arquivos que contêm dados devem ter a mesma estrutura de colunas e cabeçalho.</p>
        <p style="color: #B22222;">É importante que o nome dos arquivos de dados sigam a seguinte estrutura (respeitando a acentuação ou não do exemplo):</p>
        <p style="font-weight: bold; color: #8B0000;">Avaliacao_CPA_1Período_TDS_20242.xlsx</p>
        <p style="font-weight: bold; color: #8B0000;">Avaliacao_CPA_1Período_Psicologia_20242.xlsx</p>
    </div>
    """, unsafe_allow_html=True)

# Idenditicação da avaliação
ano_semestre = st.text_input("Identificação da avaliação (por exemplo: 2024-02)", value="2024-02")


# Seleção de curso e período
start_block_size = st.number_input("Quantas colunas existem antes de começar a coluna de dados", value=10)
end_block_size = st.number_input("Quantidade de colunas que devem ser desprezadas no final", value=3)
professor_block_size = st.number_input("Tamanho do bloco de colunas de dados de cada professor", value=13)
quantidade_respostas = st.number_input("Quantidade de respondentes (linhas) por professor", value=18)


def extrair_informacoes_gerais(nome_arquivo):
    nome_arquivo = unicodedata.normalize('NFC', nome_arquivo)
    match = re.search(r'Avaliacao_CPA_(\d+)Periodo_(\d+).zip', nome_arquivo)
    if match:
        periodo = match.group(1)  
        ano_semestre = match.group(2)  
        return periodo, ano_semestre
    return None, None


def extrair_informacoes_cursos(nome_arquivo):
    nome_arquivo = unicodedata.normalize('NFC', nome_arquivo)
    match = re.search(r'Avaliacao_CPA_(\d+)Período_([A-Za-zÀ-ÖØ-öø-ÿ]+)_(\d+).xlsx', nome_arquivo)

    if match:
        curso_name = match.group(2)  
        curso_name = mapping_cursos.get(curso_name, curso_name) 
        return curso_name
    return None

    
# Função para processar os dados de cada professor e concatenar no DataFrame final
def process_professor_data(df, quantidade_respostas, start_col, end_col, professor_name, disciplina_name, curso_name, periodo_name):
    df_selected = df.iloc[0:quantidade_respostas, start_col:end_col].copy()
    
    df_selected['CURSO'] = curso_name
    df_selected['PROFESSOR (A-Z)'] = professor_name
    df_selected['DISCIPLINA'] = disciplina_name
    df_selected['PERIODO'] = periodo_name
    
    return df_selected


# Função para converter o DataFrame para CSV com separador ';' e codificação UTF-8 (usando BytesIO)
def to_csv(df):
    output = io.BytesIO()
    df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')  # Força a escrita em UTF-8 com BOM
    processed_data = output.getvalue()
    return processed_data
            
# Carregando o arquivo ZIP usando o file uploader
st.markdown("""
    <div style="border: 2px solid #4CAF50; padding: 15px; background-color: #f9f9f9; border-radius: 10px;">
        <p style="color: #333333;">Escolha um arquivo no formato ZIP com todos os arquivos de pesquisa dos diversos cursos, MAS DE UM MESMO PERÍODO.</p>
        <p style="color: #555555;">É importante que o nome do arquivo siga a seguinte estrutura (respeitando a NÃO acentuação):</p>
        <p style="font-weight: bold; color: #000000;">Avaliacao_CPA_1Periodo_20242.zip</p>
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Carregue um arquivo ZIP", type=["zip"])


if uploaded_file is not None:
    with zipfile.ZipFile(uploaded_file, "r") as z:
        # Lista para armazenar todos os DataFrames processados
        todos_dfs = pd.DataFrame()

        periodo_name, ano_semestre = extrair_informacoes_gerais(uploaded_file.name)
        
        # Percorrer todos os arquivos no ZIP
        for file_info in z.infolist():
            file_name = file_info.filename  
            with z.open(file_name) as file:
                # Ler o conteúdo do arquivo Excel diretamente do buffer de memória
                df = pd.read_excel(file, header=None)
                curso_name = extrair_informacoes_cursos(file_name)

                # Remover as primeiras 9 colunas (A-J) e as últimas 3 colunas
                df = df.drop(df.columns[:start_block_size], axis=1)
                df = df.drop(df.columns[-end_block_size:], axis=1)

                # Calcular o número de professores
                num_cols = df.shape[1]
                num_professors = num_cols // professor_block_size
                
                # Extrair os nomes dos professores e disciplinas
                professores_name = []
                disciplinas_name = []

                for i in range(num_professors):
                    start_col = i * professor_block_size
                    end_col = start_col + professor_block_size
                    header_text = df.iloc[0, start_col]
                
                    professor = header_text.split("Professor(a): ")[1].split(".Autoavaliação")[0]
                    disciplina = header_text.split("Avaliação da disciplina: ")[1].split(" / Professor(a):")[0]
                
                    professores_name.append(professor)
                    disciplinas_name.append(disciplina)

                # Remove a linha zero
                df = df.drop(index=0)

                # Promove a nova linha zero como cabeçalho
                df.columns = df.iloc[0]
                df = df.drop(index=1)
                
                # Remover ':' dos nomes das colunas
                df.columns = df.columns.str.replace(':', '')

                # Cria um DataFrame final vazio
                final_df = pd.DataFrame()

                # Processa os dados de cada professor e concatena no DataFrame final
                for i in range(num_professors):
                    start_col = i * professor_block_size
                    end_col = start_col + professor_block_size

                    professor_name = professores_name[i]
                    disciplina_name = disciplinas_name[i]

                    df_professor = process_professor_data(df, quantidade_respostas, start_col, end_col, professor_name, disciplina_name, curso_name, periodo_name)
                    final_df = pd.concat([final_df, df_professor], ignore_index=True)

                final_df['Observações gerais sobre as disciplinas/professores'] = final_df['Observações gerais sobre as disciplinas/professores'].str.replace(';', '')
                
                nova_ordem = [
                               'CURSO', 'PERIODO', 'DISCIPLINA', 'PROFESSOR (A-Z)',
                               'Importância da disciplina',
                               'Apresentação do plano de ensino da disciplina',
                               'Cumprimento plano de ensino da disciplina',
                               'Domínio do conteúdo da disciplina',
                               'Assiduidade', 'Pontualidade',
                               'Qualidade das aulas “ao vivo”',
                               'Compatibilidade das avaliações com o conteúdo ministrado em sala de aula',
                               'Uso e indicação de bibliografias constantes no plano de ensino',
                               'Disponibilidade do professor para atendimento ao aluno',
                               'Satisfação geral com a disciplina',
                               'Satisfação geral com o professor',
                               'Observações gerais sobre as disciplinas/professores']

                # Aplicar a nova ordem ao DataFrame
                final_df = final_df[nova_ordem]
                todos_dfs = pd.concat([todos_dfs, final_df], ignore_index=True)

    
    # Mostra o DataFrame final
    st.write("Amostra dos dados processados:")
    st.dataframe(todos_dfs.head(5))

    csv_data = to_csv(todos_dfs)

    # Gera o nome do arquivo baseado no curso e no período
    file_name = f"{ano_semestre}_periodo_{periodo_name}.csv"

    # Botão para download do arquivo CSV
    st.download_button(
        label="Baixar arquivo CSV",
        data=csv_data,
        file_name=file_name,
        mime='text/csv'
    )