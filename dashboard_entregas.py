import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title='Dashboard de Entregas', layout='wide')

# Estilos personalizados
st.markdown('''
    <style>
        .main {
            background-color: #F0FFFF;
        }
        .card {
            background-color: #00CED1;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
            text-align: center;
        }
        .card h2 {
            font-size: 30px;
            color: #f1c40f;
        }
        .card p {
            font-size: 18px;
        }
    </style>
''', unsafe_allow_html=True)

st.title('Dashboard ABJP SEMANAL')

# Criação das abas de navegação
aba_selecionada = st.sidebar.selectbox('Selecione a aba', ['Performance', 'Valores'])

if aba_selecionada == 'Performance':
    st.header('📊 Performance dos Entregadores')

    uploaded_file = st.file_uploader('Carregar dados entregadores', type=['xlsx'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name='Analise')

        # Filtros
        st.sidebar.title('Filtros')
        filtro_sub = st.sidebar.multiselect('Selecione a Sub-Praça', df['sub_praca'].unique())
        filtro_periodo = st.sidebar.multiselect('Selecione os Turnos', df['periodo'].unique())
        filtro_data = st.sidebar.date_input('Selecione as Datas', [])
        

        if filtro_periodo:
            df = df[df['periodo'].isin(filtro_periodo)]
        if filtro_sub:
            df = df[df['sub_praca'].isin(filtro_sub)]
        if filtro_data and len(filtro_data) == 2:
            df['data_do_periodo'] = pd.to_datetime(df['data_do_periodo'], errors='coerce').dt.date
            start_date = pd.to_datetime(filtro_data[0]).date()
            end_date = pd.to_datetime(filtro_data[1]).date()
            df = df[(df['data_do_periodo'] >= start_date) & (df['data_do_periodo'] <= end_date)]

        # Corrigir caracteres especiais e usar o ID do entregador
        df['pessoa_entregadora'] = df['pessoa_entregadora'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

        # Converter tempo_disponivel_absoluto para timedelta
        df['tempo_disponivel_absoluto'] = pd.to_timedelta(df['tempo_disponivel_absoluto'].astype(str), errors='coerce')

        # Agrupar dados por ID do entregador
        df_agrupado = df.groupby(['id_da_pessoa_entregadora', 'pessoa_entregadora']).agg({
            'numero_de_corridas_ofertadas': 'sum',
            'numero_de_corridas_aceitas': 'sum',
            'numero_de_corridas_rejeitadas': 'sum',
            'tempo_disponivel_absoluto': 'sum'
        }).reset_index()

        # Calcular porcentagens
        df_agrupado['Taxa de Aceite (%)'] = ((df_agrupado['numero_de_corridas_aceitas'] / df_agrupado['numero_de_corridas_ofertadas']) * 100).round(2)
        df_agrupado['Porcentagem Tempo Online (%)'] = ((df_agrupado['tempo_disponivel_absoluto'].dt.total_seconds() / (8 * 3600 * len(df['data_do_periodo'].unique()))) * 100).round(2)

        # Renomear colunas
        df_agrupado = df_agrupado.rename(columns={
            'pessoa_entregadora': 'Entregador',
            'numero_de_corridas_ofertadas': 'Rotas Ofertadas',
            'numero_de_corridas_aceitas': 'Rotas Aceitas',
            'numero_de_corridas_rejeitadas': 'Rotas Rejeitadas'
        })

        st.dataframe(df_agrupado[['Entregador', 'Rotas Ofertadas', 'Rotas Aceitas', 'Rotas Rejeitadas', 'Taxa de Aceite (%)', 'Porcentagem Tempo Online (%)']])

        # Botão para exibir detalhes do entregador
        entregador_selecionado = st.selectbox('Selecione o Entregador para ver detalhes', df_agrupado['Entregador'].unique())
        if st.button('Ver Detalhes do Entregador') and entregador_selecionado:
            entregador_detalhes = df[df['pessoa_entregadora'] == entregador_selecionado]
            st.subheader(f'Detalhes do Entregador: {entregador_selecionado}')
            entregador_detalhes = entregador_detalhes.groupby(['data_do_periodo']).agg({
                'numero_de_corridas_ofertadas': 'sum',
                'numero_de_corridas_aceitas': 'sum',
                'numero_de_corridas_rejeitadas': 'sum',
                
            }).reset_index()

            entregador_detalhes['Taxa de Aceite (%)'] = ((entregador_detalhes['numero_de_corridas_aceitas'] / entregador_detalhes['numero_de_corridas_ofertadas']) * 100).round(2)
            st.dataframe(entregador_detalhes)

    else:
        st.info('Envie o arquivo Excel para visualizar a performance.')

elif aba_selecionada == 'Valores':
    st.header('💰 Valores da Semana')
    saldo_files = st.file_uploader('Envie até dois arquivos Excel de Saldo Semanal', type=['xlsx'], accept_multiple_files=True)

    valor_minimo = st.number_input('Filtrar Total acima de:', min_value=0.0, step=100.0)

    if saldo_files:
        for saldo_file in saldo_files:
            df_saldo = pd.read_excel(saldo_file)
            if valor_minimo > 0:
                df_saldo = df_saldo[df_saldo['Total'] >= valor_minimo]
            st.subheader(f'Valores - {saldo_file.name}')
            st.dataframe(df_saldo)
    else:
        st.info('Envie os arquivos Excel para visualizar os valores da semana.')
