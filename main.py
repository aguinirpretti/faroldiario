import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Configuração do Streamlit
st.set_page_config(layout="wide", page_title="Visualização de Eventos de Telemetria", page_icon="📅")

# CSS para estilização
st.markdown("""
    <style>
        .st-emotion-cache-15ecox0 {  /* Menu lateral de deploy e configuração */
            display: none;
        }
        .styles_terminalResizable__BBKio {  /* Menu lateral de deploy e configuração */
            display: none;
            
    </style>
""", unsafe_allow_html=True)

# Função para carregar e filtrar dados
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y')
    return df

# Função para plotar o calendário com eventos
def plot_calendar(df):
    status_colors = {
        'NOVO PENDENTE': 'green',
        'Finalizado Positivo': 'lightblue',
        'Pendente de documentação': 'orange',
        'Outro': 'gray'
    }

    df_calendar = df.copy()
    df_calendar['Day'] = df_calendar['DATA'].dt.date
    df_calendar['Month'] = df_calendar['DATA'].dt.to_period('M')

    months = sorted(df_calendar['Month'].unique())
    num_rows = len(months)

    fig = make_subplots(
        rows=num_rows, 
        cols=1, 
        subplot_titles=[f"Calendário - {month}" for month in months], 
        shared_xaxes=True,
        vertical_spacing=0.05
    )

    for i, month in enumerate(months):
        month_df = df_calendar[df_calendar['Month'] == month]
        num_days = (datetime(month.year, month.month + 1, 1) - timedelta(days=1)).day if month.month < 12 else (datetime(month.year + 1, 1, 1) - timedelta(days=1)).day

        calendar_matrix = [['' for _ in range(7)] for _ in range((num_days + 6) // 7)]

        for day in range(1, num_days + 1):
            day_date = datetime(month.year, month.month, day).date()
            status_doc = month_df[month_df['Day'] == day_date]['STATUS_DOC']
            if not status_doc.empty:
                color = status_colors.get(status_doc.values[0], 'gray')
            else:
                color = 'gray'

            row = (day - 1) // 7
            col = (day - 1) % 7
            calendar_matrix[row][col] = (day, color)

        heatmap = go.Heatmap(
            z=[[1] * len(row) for row in calendar_matrix],
            colorscale=[[0, 'white'], [1, 'white']],
            zmin=0,
            zmax=1,
            showscale=False
        )

        fig.add_trace(
            heatmap,
            row=i + 1, col=1
        )

        for row_idx, row in enumerate(calendar_matrix):
            for col_idx, cell in enumerate(row):
                if cell:
                    day, color = cell
                    fig.add_trace(
                        go.Scatter(
                            x=[col_idx],
                            y=[-row_idx],
                            mode='markers+text',
                            text=[f'<b>{day}</b>'],
                            textposition='middle center',
                            marker=dict(color=color, size=30, line=dict(width=2, color='black')),
                            textfont=dict(size=14, color='black'),
                            showlegend=False
                        ),
                        row=i + 1, col=1
                    )

        fig.update_xaxes(
            ticktext=['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            row=i + 1, col=1
        )

        fig.update_yaxes(
            visible=False,
        )

    fig.update_layout(
        title_text="Calendário de Eventos",
        height=600,
        showlegend=False,
        xaxis_title="Dia da Semana",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    st.plotly_chart(fig)

# Função para plotar gráficos de infratores
def plot_infratores(df, top_n):
    df_motoristas = df.groupby('MOTORISTA').size().reset_index(name='Quantidade')
    df_motoristas = df_motoristas.sort_values(by='Quantidade', ascending=False)

    df_motoristas = df_motoristas.head(top_n)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_motoristas['MOTORISTA'],
            y=df_motoristas['Quantidade'],
            text=df_motoristas['Quantidade'],
            textposition='outside'
        )
    )

    fig.update_layout(
        title=f"Top {top_n} Motoristas com Mais Eventos",
        xaxis_title="Motorista",
        yaxis_title="Quantidade de Eventos",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    st.plotly_chart(fig)

# Função principal da aplicação Streamlit
def main():
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Escolha uma página", ["Página Principal", "Top Motoristas"])

    file_path = "05_2024.csv"
    df = load_data(file_path)

    df['STATUS'] = df['STATUS'].fillna('Desconhecido').astype(str)
    df['STATUS_DOC'] = df['STATUS_DOC'].fillna('Desconhecido').astype(str)

    if page == "Página Principal":
        st.title("Visualização de Eventos de Telemetria")

        # Seleção do Polo
        polos = sorted(df['POLO'].unique())
        polo = st.selectbox("Escolha o Polo", ['Todos'] + polos)

        if polo != 'Todos':
            df = df[df['POLO'] == polo]

        # Seleção da Unidade
        unidades_disponiveis = sorted(df['UNIDADE'].unique())
        unidade = st.selectbox("Escolha a Unidade", ['Todos'] + unidades_disponiveis)

        if unidade != 'Todos':
            df = df[df['UNIDADE'] == unidade]

        # Seleção do Tipo de Evento
        tipos_evento_disponiveis = sorted(df['TIPO'].unique())
        tipo_evento = st.selectbox("Escolha o Tipo de Evento", ['Todos'] + tipos_evento_disponiveis)

        if tipo_evento != 'Todos':
            df = df[df['TIPO'] == tipo_evento]

        # Filtro por Data
        start_date = st.date_input("Data de Início", df['DATA'].min().date(), format="DD/MM/YYYY")
        end_date = st.date_input("Data de Fim", df['DATA'].max().date(), format="DD/MM/YYYY")

        df = df[(df['DATA'] >= pd.to_datetime(start_date)) & (df['DATA'] <= pd.to_datetime(end_date))]

        st.subheader("Cores no Calendário")
        st.write("""
            - **NOVO PENDENTE**: Verde
            - **Atribuído - Pendente de documentação**: Laranja
            - **Finalizado Com Anexo**: Azul
            - **Sem Eventos e/ou Mix**: Cinza
        """)

        st.subheader("Calendário de Eventos")
        if not df.empty:
            plot_calendar(df)
        else:
            st.write("Nenhum dado disponível para os filtros selecionados.")

        st.subheader("Status das Tratativas")
        status_options = sorted(df['STATUS'].unique())
        status = st.selectbox("Escolha o Status", ['Todos'] + status_options)

        if status != 'Todos':
            df = df[df['STATUS'] == status]

        df = df.sort_values(by='DATA')

        df_display = df.copy()
        df_display['DATA'] = df_display['DATA'].dt.strftime('%d/%m/%Y')

        st.write(df_display)

        today = datetime.now().date()

        def calculate_prazo(row):
            if row['STATUS_DOC'] == 'Finalizado Positivo':
                return 'Resolvido'
            else:
                data = row['DATA'].date()
                days_diff = (today - data).days
                if days_diff > 5:
                    return 'Atrasado'
                elif days_diff == 3:
                    return 'Próximo'
                elif 1 <= days_diff < 3:
                    return 'Dentro do Prazo'
                else:
                    return 'Dentro do Prazo'

        df['Prazos'] = df.apply(calculate_prazo, axis=1)

        st.subheader("Prazos de Tratamento")
        
        # Filtrar apenas pendentes
        df_pendentes = df[df['Prazos'] != 'Resolvido']

        df_pendentes = df_pendentes.sort_values(by='DATA')

        df_display = df_pendentes.copy()
        df_display['DATA'] = df_display['DATA'].dt.strftime('%d/%m/%Y')

        def color_prazos(val):
            if val == 'Atrasado':
                return 'background-color: lightcoral'
            elif val == 'Próximo':
                return 'background-color: lightyellow'
            elif val == 'Dentro do Prazo':
                return 'background-color: lightgreen'
            else:
                return ''
        
        styled_df = df_display.style.applymap(color_prazos, subset=['Prazos'])
        st.write(styled_df)

    elif page == "Top Motoristas":
        st.title("Top Motoristas com Mais Eventos")

        # Seleção do Polo
        polos = sorted(df['POLO'].unique())
        polo = st.selectbox("Escolha o Polo", ['Todos'] + polos, key="top_motoristas_polo")

        if polo != 'Todos':
            df = df[df['POLO'] == polo]

        # Seleção da Unidade
        unidades_disponiveis = sorted(df['UNIDADE'].unique())
        unidade = st.selectbox("Escolha a Unidade", ['Todos'] + unidades_disponiveis, key="top_motoristas_unidade")

        if unidade != 'Todos':
            df = df[df['UNIDADE'] == unidade]

        # Seleção do Tipo de Evento
        tipos_evento_disponiveis = sorted(df['TIPO'].unique())
        tipo_evento = st.selectbox("Escolha o Tipo de Evento", ['Todos'] + tipos_evento_disponiveis, key="top_motoristas_tipo_evento")

        if tipo_evento != 'Todos':
            df = df[df['TIPO'] == tipo_evento]

        # Filtro por Data
        start_date = st.date_input("Data de Início", df['DATA'].min().date(), format="DD/MM/YYYY", key="top_motoristas_start_date")
        end_date = st.date_input("Data de Fim", df['DATA'].max().date(), format="DD/MM/YYYY", key="top_motoristas_end_date")

        df = df[(df['DATA'] >= pd.to_datetime(start_date)) & (df['DATA'] <= pd.to_datetime(end_date))]

        # Escolha do número de motoristas
        max_motoristas = df['MOTORISTA'].nunique()
        num_motoristas = st.selectbox("Escolha o Número de Top Motoristas", list(range(1, max_motoristas + 1)), index=min(9, max_motoristas - 1), key="top_motoristas_num_motoristas")

        if not df.empty:
            plot_infratores(df, num_motoristas)
        else:
            st.write("Nenhum dado disponível para os filtros selecionados.")

    # Rodapé discreto
    st.markdown("""
        <div style="position: fixed; bottom: 10px; right: 10px; font-size: 12px; color: gray;">
            Desenvolvido por Aguinir Pretti
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
