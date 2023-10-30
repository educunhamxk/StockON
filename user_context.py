user_context = """

Os dataframes df_final, df_compras, previsoes e df_vendas_estoque já estão carregados na memória e não precisam ser lidos de um arquivo.

Você pode me pedir para:
- Analisar sugestões de compras usando 'df_final'.
- Demonstrar a previsão de vendas com 'previsoes'.
- Consultar estoque e vendas do último ano em 'df_vendas_estoque'.

Se a pergunta for referente à: sugestão de compras, requisições de compras, reabastecimento de produto, Classificação ABC, Curva ABC, Criticidade e Estoque minimo, consulte o 'df_final'.
Se a pergunta for referente à: previsões de demandas, previsões de vendas, consulte o dataframe 'previsoes'.
Se a pergunta for referente à: quantidade de estoque, quantidade de venda no ultimo ano, meses, semanas ou dias, ruptura, consulte o 'df_vendas_estoque'.

1. df_vendas_estoque: Esta tabela mostra o histórico diário de vendas e estoque. As colunas incluem:
- Produto_ID e Nome_Produto2: Identificadores do produto.
- Data: A data da entrada.
- Quantidade Vendida: Quantidade do produto vendida naquela data.
- Quantidade_Estoque: Quantidade do produto em estoque naquela data.
- Ruptura_Historica: Registros históricos de ruptura do produto.
- % Ruptura: Percentual de ruptura do produto naquela data.

2. previsoes: Este dataframe prevê a demanda de venda para os próximos 30 dias por produto. A primeira coluna é 'Index' representando os dias, e as outras colunas, como '1,2,3,...', são os códigos do Produto_ID mostrando a demanda prevista.

3. df_final: Um resumo que inclui:
- Produto_ID e Nome_Produto2: Identificadores do produto.
- Classificacao ABC: É a Cuvrva ABC baseada na representatividade da venda.
- Estoque_Minimo: A quantidade mínima recomendada em estoque para o produto.
- Criticidade e Criticidade_Num: Classificações baseadas na quantidade de fornecedores e na classificação ABC.
- Lead_Time_Dias: Tempo de entrega após a requisição de compra do produto.
- Sugestao_Compra: Quantidade sugerida de compra para o produto baseado na previsão de venda e estoque atual.

"""