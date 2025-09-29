# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os


# --- MODELO PARA RECEBER DADOS DA AVALIAÇÃO ---
class Rating(BaseModel):
    user_id: int
    anime_id: int
    rating: int


# --- VARIÁVEIS GLOBAIS PARA ARMAZENAR O MODELO ---
df_merged = None
item_similarity_df = None
RATING_FILE_PATH = '../datasets/rating.csv'
ANIME_FILE_PATH = '../datasets/anime.csv'


# --- FUNÇÃO PARA CARREGAR E PROCESSAR OS DADOS ---
def load_and_process_data():
    global df_merged, item_similarity_df

    if not os.path.exists(ANIME_FILE_PATH) or not os.path.exists(RATING_FILE_PATH):
        raise FileNotFoundError("Arquivos de dataset não encontrados.")

    df_anime = pd.read_csv(ANIME_FILE_PATH)
    df_rating = pd.read_csv(RATING_FILE_PATH)

    df_rating = df_rating[df_rating['rating'] != -1]
    df_merged = pd.merge(df_rating, df_anime[['anime_id', 'name']], on='anime_id')

    user_item_matrix = df_merged.pivot_table(
        index='name', columns='user_id', values='rating'
    ).fillna(0)

    item_similarity_df = pd.DataFrame(
        cosine_similarity(user_item_matrix),
        index=user_item_matrix.index,
        columns=user_item_matrix.index
    )
    print("Modelo de recomendação recarregado.")


# --- API com FastAPI ---
app = FastAPI()


# --- EVENTO DE STARTUP: CARREGA O MODELO AO INICIAR ---
@app.on_event("startup")
def startup_event():
    load_and_process_data()


# --- ENDPOINTS EXISTENTES ---
def get_recommendations(user_id, num_recs=5):
    # ... (a função get_recommendations e evaluate_accuracy permanecem as mesmas)
    user_ratings = df_merged[df_merged['user_id'] == user_id]
    if user_ratings.empty:
        return []

    best_rated_anime_name = user_ratings.loc[user_ratings['rating'].idxmax()]['name']
    similar_scores = item_similarity_df[best_rated_anime_name]
    similar_animes = similar_scores.sort_values(ascending=False).drop(best_rated_anime_name)

    watched_animes = user_ratings['name'].tolist()
    recommendations = similar_animes[~similar_animes.index.isin(watched_animes)].head(num_recs)

    return recommendations.index.tolist()


@app.get("/recomendar/{user_id}")
def recommend_for_user(user_id: int):
    # Verifica se o user_id existe nos dados carregados
    if user_id not in df_merged['user_id'].unique():
        return {"error": f"Usuário com ID {user_id} não encontrado ou ainda não fez avaliações."}
    recs = get_recommendations(user_id)
    if not recs:
        return {"error": "Não foi possível gerar recomendações."}
    return {"user_id": user_id, "recommendations": recs}


# ... (a função evaluate_accuracy permanece a mesma)
@app.get("/evaluate_accuracy/{test_user_id}")
def evaluate_accuracy(test_user_id: int, num_recs: int = 10):
    user_ratings = df_merged[df_merged['user_id'] == test_user_id]
    high_rated = user_ratings[user_ratings['rating'] >= 7]
    if len(high_rated) < 5:
        return {"error": "Usuário não tem avaliações positivas suficientes (mínimo de 5)."}
    high_rated = high_rated.sample(frac=1, random_state=42)
    holdout_size = int(len(high_rated) * 0.2)
    if holdout_size == 0: holdout_size = 1
    ground_truth_set = high_rated.iloc[:holdout_size]
    train_set = high_rated.iloc[holdout_size:]
    train_animes = train_set['name'].tolist()
    train_ratings = train_set['rating'].tolist()
    train_similarity = item_similarity_df.loc[train_animes]
    weighted_scores = train_similarity.T.dot(train_ratings) / sum(train_ratings)
    weighted_scores = weighted_scores.drop(train_animes, errors='ignore')
    recommendations = weighted_scores.nlargest(num_recs)
    recommendations_list = recommendations.index.tolist()
    hits_list = [anime for anime in recommendations_list if anime in ground_truth_set['name'].tolist()]
    hits = len(hits_list)
    precision_at_n = hits / num_recs
    return {
        "test_user_id": test_user_id,
        "ground_truth": ground_truth_set['name'].tolist(),
        "recommendations": recommendations_list,
        "hits": hits,
        "total_recommendations": num_recs,
        "accuracy": precision_at_n
    }


# --- NOVO ENDPOINT PARA ADICIONAR AVALIAÇÃO ---
@app.post("/add_rating")
def add_rating(rating: Rating):
    try:
        # Formata a nova linha para o CSV
        new_rating_line = f"{rating.user_id},{rating.anime_id},{rating.rating}\n"

        # Abre o arquivo em modo 'append' (adicionar ao final) e escreve a nova linha
        with open(RATING_FILE_PATH, 'a') as f:
            f.write(new_rating_line)

        # Recarrega o modelo para incluir a nova avaliação
        load_and_process_data()

        return {"status": "success", "message": "Avaliação adicionada e modelo atualizado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- NOVO ENDPOINT PARA GERAR AMOSTRA DA MATRIZ ---
@app.get("/utility_matrix_sample")
def get_utility_matrix_sample(num_users: int = 25, num_animes: int = 25):
    """
    Gera uma sub-matriz com os usuários mais ativos e os animes mais populares.
    """
    # Encontra os usuários mais ativos
    most_active_users = df_merged['user_id'].value_counts().nlargest(num_users).index

    # Encontra os animes mais populares
    most_popular_animes = df_merged['name'].value_counts().nlargest(num_animes).index

    # Filtra o dataframe para conter apenas esses usuários e animes
    sample_df = df_merged[
        df_merged['user_id'].isin(most_active_users) &
        df_merged['name'].isin(most_popular_animes)
        ]

    # Cria a sub-matriz de utilidade
    sample_utility_matrix = sample_df.pivot_table(
        index='name', columns='user_id', values='rating'
    ).fillna(0)

    # Converte para JSON para enviar pela API
    return sample_utility_matrix.to_json(orient='split')