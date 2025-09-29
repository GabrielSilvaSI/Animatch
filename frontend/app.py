# frontend/app.py
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuração da Página ---
st.set_page_config(page_title="AnimeRec", layout="wide")


# --- Carregamento dos Dados ---
@st.cache_data
def load_data():
    try:
        anime_df = pd.read_csv('../datasets/anime.csv')
        rating_df = pd.read_csv('../datasets/rating.csv')
        user_counts = rating_df['user_id'].value_counts()
        relevant_users = user_counts[user_counts > 50].index
        return anime_df, rating_df, sorted(relevant_users)
    except FileNotFoundError:
        st.error("Arquivos de dataset não encontrados.")
        return None, None, []


anime_df, rating_df, user_ids = load_data()

# --- Abas da Aplicação ---
st.title("Sistema de Recomendação de Animes 🎌")

if anime_df is not None:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Recomendações",
        "Visualizar Dados",
        "Avaliar Acurácia",
        "Adicionar Avaliações"
    ])

    # --- Aba 1: Recomendações ---
    with tab1:
        st.header("Encontre sua próxima maratona!")
        # Atualiza a lista de usuários para garantir que novos usuários apareçam
        all_user_ids = sorted(rating_df['user_id'].unique())
        selected_user = st.selectbox("Selecione seu ID de Usuário:", all_user_ids, key="rec_user")

        if st.button("Obter Recomendações", type="primary"):
            api_url = f"http://127.0.0.1:8000/recomendar/{selected_user}"
            try:
                # ... (código da aba 1 permanece o mesmo)
                response = requests.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        st.error(data["error"])
                    else:
                        recommendations = data.get("recommendations", [])
                        st.subheader(f"Animes recomendados para o usuário {selected_user}:")
                        if recommendations:
                            cols = st.columns(len(recommendations))
                            for i, anime_name in enumerate(recommendations):
                                with cols[i]:
                                    st.caption(anime_name)
                        else:
                            st.warning("Não foi possível gerar recomendações.")
                else:
                    st.error("Erro ao contatar a API de recomendação.")
            except requests.exceptions.ConnectionError:
                st.error("Não foi possível conectar ao backend.")

    # --- Aba 2: Visualizar Dados ---
    with tab2:
        st.header("Explorando os Dados")

        st.subheader("Amostra do Catálogo de Animes")
        st.dataframe(anime_df.head(10))

        st.subheader("Amostra das Avaliações de Usuários")
        st.dataframe(rating_df.head(10))

        # --- NOVA SEÇÃO PARA VISUALIZAR A MATRIZ DE UTILIDADE ---
        st.divider()
        st.header("Visualização da Matriz de Utilidade")
        st.write("""
        A matriz de utilidade completa é gigantesca. Aqui, podemos ver uma amostra com os
        usuários mais ativos e os animes mais populares. O gráfico de calor (heatmap)
        ajuda a visualizar a **esparsidade**: a maioria dos campos é escura (nota 0),
        mostrando que poucos usuários avaliaram aqueles animes específicos.
        """)

        col1, col2 = st.columns(2)
        with col1:
            num_users_sample = st.slider("Número de usuários mais ativos:", 5, 50, 25)
        with col2:
            num_animes_sample = st.slider("Número de animes mais populares:", 5, 50, 25)

        if st.button("Gerar Amostra da Matriz"):
            api_url = f"http://127.0.0.1:8000/utility_matrix_sample?num_users={num_users_sample}&num_animes={num_animes_sample}"
            try:
                response = requests.get(api_url)
                if response.status_code == 200:
                    # Converte o JSON recebido de volta para um DataFrame
                    matrix_sample_df = pd.read_json(response.json(), orient='split')

                    st.subheader("Amostra da Matriz (Tabela)")
                    st.dataframe(matrix_sample_df)

                    st.subheader("Gráfico de Calor (Heatmap)")
                    # Cria a figura para o gráfico
                    fig, ax = plt.subplots(figsize=(12, 10))
                    sns.heatmap(matrix_sample_df, cmap="viridis", ax=ax, cbar_kws={'label': 'Nota da Avaliação'})
                    ax.set_xlabel("ID do Usuário")
                    ax.set_ylabel("Nome do Anime")
                    ax.set_title("Heatmap da Matriz de Utilidade (Amostra)")

                    # Exibe o gráfico no Streamlit
                    st.pyplot(fig)

                else:
                    st.error("Erro ao gerar a amostra da matriz.")
            except requests.exceptions.ConnectionError:
                st.error("Não foi possível conectar ao backend.")
    # --- NOVA Aba 4: Adicionar Avaliações ---
    with tab4:
        st.header("Adicione um Usuário ou Nova Avaliação")

        # Campo para inserir ID de usuário (novo ou existente)
        user_id_to_add = st.number_input("Insira seu User ID:", min_value=1, step=1, key="user_id_add")

        # Lista de animes para avaliar
        anime_list = anime_df.sort_values('name')['name'].tolist()
        selected_anime_name = st.selectbox("Escolha um anime para avaliar:", anime_list)

        # Slider para a nota
        rating_value = st.slider("Sua nota:", min_value=1, max_value=10, value=7, key="rating_add")

        if st.button("Salvar Avaliação", type="primary"):
            if selected_anime_name:
                # Encontrar o anime_id correspondente ao nome selecionado
                anime_id_to_add = anime_df[anime_df['name'] == selected_anime_name]['anime_id'].iloc[0]

                # Criar o payload para a API
                payload = {
                    "user_id": user_id_to_add,
                    "anime_id": int(anime_id_to_add),
                    "rating": rating_value
                }

                api_url = "http://127.0.0.1:8000/add_rating"
                try:
                    response = requests.post(api_url, json=payload)
                    if response.status_code == 200:
                        st.success(f"Avaliação para '{selected_anime_name}' salva com sucesso!")
                        st.info("O modelo foi atualizado. Suas novas recomendações já refletem essa avaliação.")
                        # Limpa o cache para que os dados sejam recarregados na próxima interação
                        st.cache_data.clear()
                    else:
                        st.error(f"Erro ao salvar: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Não foi possível conectar ao backend.")