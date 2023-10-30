import openai
import ast
from decouple import config
import streamlit as st
from user_context import user_context

# Importando as funções para carregar os dataframes
from dataframe import load_df_compras, load_df_final, load_df_vendas_estoque, load_previsoes

MAX_TRIES = 3

def reformulate_question(original_question):
    reformulations = {
        "Quais são os produtos de alta criticidade?": 
        "Mostre-me o código para obter os produtos de alta criticidade.",
        "Quero ver o histórico de vendas.": 
        "Mostre-me o código para visualizar o histórico de vendas.",
    }
    return reformulations.get(original_question, original_question)

def contains_code_keywords(response_content):
    code_keywords = [
        "df", "groupby", "dataframe", ".loc", ".iloc", 
        "plot", "filter", "merge", "join", "set_index", 
        "reset_index", "pivot_table", "concat", "read_csv", 
        "fillna", "dropna", "sort_values", "apply", "lambda", 
        "map", "unique", "nunique", "value_counts", "astype", 
        "to_datetime", "cut", "qcut", "rolling", "shift", 
        "head", "tail", "mean", "sum", "median", "min", "max", 
        "std", "var", "corr", "describe", "python", "dataframe", "print",
        "df_final", "df_vendas_estoque", "df_compras", "previsoes"
    ]
    
    general_python_keywords = [
        "for ", "while ", "if ", "elif ", "else:", "def ", "return", 
        "import ", "from ", "with ", "as ", "print(", "class ", 
        "try:", "except:", "raise", "assert ", "break", "continue", 
        "global ", "pass", "yield", "list(", "dict(", "set(", "tuple("
    ]
    
    combined_keywords = code_keywords + general_python_keywords
    return any(keyword in response_content for keyword in combined_keywords)

def validate_code(code):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id not in code:
                return False, f"Variável '{node.id}' não definida"
        return True, None
    except Exception as e:
        return False, str(e)

def get_chatgpt_response(user_input, user_context):
    openai_api_key = config('OPENAI_API_KEY')
    if not openai_api_key:
        st.error("Chave API da OpenAI não configurada.")
        raise ValueError("Chave API da OpenAI não encontrada!")
    openai.api_key = openai_api_key
    
    with st.spinner('Aguarde enquanto a análise é realizada...'):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": user_context},
                {"role": "user", "content": f'Os dataframes a seguir correspondem à métricas de gestão de estoque, ruptura, venda e previsão de demanda. Com base nesses dataframes df_final, previsoes, df_vendas_estoque, forneça uma resposta para {user_input}. Se a resposta envolver uma análise de dados, forneça um código Python adequado para executar no dataframe correspondente.'},
            ]
        )
        return response['choices'][0]['message']['content']

def main():
    df_compras = load_df_compras()
    df_final = load_df_final()
    df_vendas_estoque = load_df_vendas_estoque()
    previsoes = load_previsoes()

    for _ in range(MAX_TRIES):
        response_content = get_chatgpt_response(complete_question, user_context)
        if contains_code_keywords(response_content):
            code_blocks = response_content.split("```python")
            python_code = code_blocks[-1].split("```")[0].strip()
            is_valid, error_msg = validate_code(python_code)
            if is_valid:
                st.code(python_code)
                break
            else:
                st.error(f"Erro encontrado no código: {error_msg}")
                complete_question += " Por favor, corrija e tente novamente."
        else:
            st.write(response_content)
    else:
        st.write("Não foi possível obter uma resposta adequada. Por favor, reformule sua pergunta ou tente mais tarde.")