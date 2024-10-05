import streamlit as st
import pandas as pd
from io import StringIO
from io import BytesIO
import json

# Lendo o arquivo JSON com os cursos
with open('cursos.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
# Extraindo a lista de cursos
cursos = data['cursos']

# Função para processar os dados de cada professor
def process_professor_data(df, quantidade_respostas, start_col, end_col, professor_name, disciplina_name, curso_name, periodo_name):
    df_selected = df.iloc[0:quantidade_respostas+1, start_col:end_col].copy()
    # Adiciona informações sobre o curso, professor, e outras informações relevantes
    df_selected['CURSO'] = curso_name
    df_selected['PROFESSOR (A-Z)'] = professor_name
    df_selected['DISCIPLINA'] = disciplina_name
    df_selected['PERIODO'] = periodo_name
    
    return df_selected

# Interface do Streamlit
st.title("Processador de Avaliação de Professores")

# Idenditicação da avaliação
ano_semestre = st.text_input("Identificação da avaliação (por exemplo: 2024-02)", value="2024-02")

# Seleção de curso e período
curso_name = st.selectbox("Selecione o Curso", cursos)
periodo_name = st.selectbox("Selecione o Período", [f"{i}º" for i in range(1, 11)])

# Tamanho do bloco de colunas para cada professor
professor_block_size = st.number_input("Tamanho do bloco de colunas de dados de cada professor", value=13)

# Quantidade de respondentes
quantidade_respostas = st.number_input("Quantidade de respondentes por professor", value=18)

# Upload do arquivo XLS
uploaded_file = st.file_uploader("Carregue o arquivo Excel e processe a planilha", type=["xls", "xlsx"])

if uploaded_file is not None:
    # Leitura do arquivo Excel
    df = pd.read_excel(uploaded_file, header=None)

    # Remover as primeiras 9 colunas (A-J) e as últimas 3 colunas
    df = df.drop(df.columns[:10], axis=1)
    df = df.drop(df.columns[-3:], axis=1)

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


    nova_ordem =[
       'CURSO','PERIODO','DISCIPLINA','PROFESSOR (A-Z)', 
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
    
    # Mostra o DataFrame final
    st.write("Amostra do dados processados:")
    st.dataframe(final_df.head(5))

   # Função para converter o DataFrame para CSV com separador ';' e codificação UTF-8 (usando BytesIO)
    def to_csv(df):
        output = BytesIO()
        df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')  # Força a escrita em UTF-8 com BOM
        processed_data = output.getvalue()
        return processed_data

    csv_data = to_csv(final_df)

    # Gera o nome do arquivo baseado no curso e no período
    file_name = f"{ano_semestre}_{curso_name.replace(' ', '_')}_periodo_{periodo_name.replace('º', '')}.csv"

    # Botão para download do arquivo CSV
    st.download_button(
        label="Baixar arquivo CSV",
        data=csv_data,
        file_name=file_name,
        mime='text/csv'
    )
