import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Configuração do Streamlit
st.set_page_config(layout="wide", page_title="Visualização de Eventos de Telemetria", page_icon="📅")

# CSS para ocultar opções padrão do Streamlit
st.markdown("""
    <style>
        .st-emotion-cache-15ecox0 {  /* Menu lateral de deploy e configuração */
            display: none;
            
        }
        .ezrtsby0 {  /* Botão de configurações na barra superior */
            display: none;
        }
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
        'Finalizado Positivo': 'blue',
        'Pendente de documentação': 'orange',
        'Outro': 'gray'
    }

    df_calendar = df.copy()
    df_calendar['Day'] = df_calendar['DATA'].dt.date
    df_calendar['Month'] = df_calendar['DATA'].dt.to_period('M')
    
    months = sorted(df_calendar['Month'].unique())
    fig = make_subplots(rows=len(months), cols=1, subplot_titles=[f"Calendário - {month}" for month in months], shared_xaxes=True)

    for i, month in enumerate(months):
        month_df = df_calendar[df_calendar['Month'] == month]
        num_days = (datetime(month.year, month.month + 1, 1) - timedelta(days=1)).day if month.month < 12 else (datetime(month.year + 1, 1, 1) - timedelta(days=1)).day

        # Criação de uma matriz para o calendário com valores padrão 'gray'
        calendar_matrix = ['gray'] * num_days
        
        # Atualização dos valores do calendário com base nos dados disponíveis
        for day in range(1, num_days + 1):
            day_date = datetime(month.year, month.month, day).date()
            status_doc = month_df[month_df['Day'] == day_date]['STATUS_DOC']
            if not status_doc.empty:
                calendar_matrix[day - 1] = status_colors.get(status_doc.values[0], 'gray')

        calendar_matrix = [calendar_matrix[i:i+7] for i in range(0, len(calendar_matrix), 7)]

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
            for col_idx, color in enumerate(row):
                fig.add_trace(
                    go.Scatter(
                        x=[col_idx],
                        y=[-row_idx],
                        mode='markers',
                        marker=dict(color=color, size=20),
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
            visible=False,  # Oculta os valores das semanas
        )

    fig.update_layout(
        title_text="Calendário de Eventos",
        height=800,
        showlegend=False,
        xaxis_title="Dia da Semana"
    )

    st.plotly_chart(fig)

# Função principal da aplicação Streamlit
def main():
    st.title("Visualização de Eventos de Telemetria")

    file_path = "05_2024.csv"
    df = load_data(file_path)

    # Tratar valores nulos na coluna 'STATUS'
    df['STATUS'] = df['STATUS'].fillna('Desconhecido').astype(str)
    df['STATUS_DOC'] = df['STATUS_DOC'].fillna('Desconhecido').astype(str)

    # Seleção do Polo
    polos = sorted(df['POLO'].unique())
    polo = st.selectbox("Escolha o Polo", ['Todos'] + polos)

    if polo != 'Todos':
        df = df[df['POLO'] == polo]

    # Seleção do Tipo de Telemetria
    sistemas_disponiveis = sorted(df['SISTEMA'].unique())
    sistema = st.selectbox("Escolha o Sistema de Telemetria", ['Todos'] + sistemas_disponiveis)

    if sistema != 'Todos':
        df = df[df['SISTEMA'] == sistema]

    # Filtro por Data
    start_date = st.date_input("Data de Início", df['DATA'].min().date(), format="DD/MM/YYYY")
    end_date = st.date_input("Data de Fim", df['DATA'].max().date(), format="DD/MM/YYYY")

    df = df[(df['DATA'] >= pd.to_datetime(start_date)) & (df['DATA'] <= pd.to_datetime(end_date))]

    # Exibição do Calendário
    st.subheader("Calendário de Eventos")
    if not df.empty:
        plot_calendar(df)
    else:
        st.write("Nenhum dado disponível para os filtros selecionados.")

    # Status das Tratativas
    st.subheader("Status das Tratativas")
    status_options = sorted(df['STATUS'].unique())
    status = st.selectbox("Escolha o Status", ['Todos'] + status_options)

    if status != 'Todos':
        df = df[df['STATUS'] == status]

    # Ordenar por data
    df = df.sort_values(by='DATA')

    # Formatando datas no padrão brasileiro para exibição
    df_display = df.copy()
    df_display['DATA'] = df_display['DATA'].dt.strftime('%d/%m/%Y')

    st.write(df_display)

    # Verificação dos prazos de tratamento
    today = datetime.now().date()

    # Atualizando a lógica de prazos
    def calculate_prazo(row):
        if row['STATUS_DOC'] == 'Finalizado Positivo':
            return 'Resolvido'
        else:
            # Convertendo o Timestamp para um objeto datetime.date
            data = row['DATA'].date()
            if data < today - timedelta(days=5):
                return 'Atrasado'
            elif data == today - timedelta(days=3):
                return 'Próximo'
            else:
                return 'Dentro do Prazo'

    df['Prazos'] = df.apply(calculate_prazo, axis=1)

    st.subheader("Prazos de Tratamento")
    prazo_options = sorted(df['Prazos'].unique())
    prazo = st.selectbox("Escolha o Prazo de Tratamento", ['Todos'] + prazo_options)

    if prazo != 'Todos':
        df = df[df['Prazos'] == prazo]

    # Ordenar por data
    df = df.sort_values(by='DATA')

    # Formatando datas no padrão brasileiro para exibição
    df_display = df.copy()
    df_display['DATA'] = df_display['DATA'].dt.strftime('%d/%m/%Y')

    st.write(df_display[['DATA', 'MOTORISTA', 'STATUS_DOC', 'Prazos']])

if __name__ == "__main__":
    main()
