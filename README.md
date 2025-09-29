# 🎌 Animatch: Sistema de Recomendação de Animes

Este projeto foi desenvolvido como parte da avaliação da disciplina de **Oficina de Des. de Sistemas I**, seguindo as diretrizes do guia fornecido. O Animatch é um sistema de recomendação funcional que utiliza técnicas de filtragem colaborativa para sugerir animes aos usuários de forma personalizada e interativa.

## 👥 Equipe

* Emanoel da Conceição Cardoso Junior
* Gabriel da Silva Lima

## 🎯 Objetivo do Sistema

O objetivo principal do Animatch é aplicar os conceitos de sistemas de recomendação para criar uma aplicação completa, com as seguintes características:
* **Backend Robusto (FastAPI)**: Processa os dados, calcula as similaridades e serve as recomendações através de uma API.
* **Frontend Interativo (Streamlit)**: Permite que os usuários obtenham recomendações, adicionem novas avaliações e visualizem a performance do modelo.
* **Modelo Dinâmico**: O sistema é capaz de incorporar novas avaliações em tempo real, atualizando o modelo para que as recomendações permaneçam relevantes.
* **Avaliação de Performance**: Inclui uma metodologia clara para calcular a acurácia do sistema, conforme exigido pelo guia do projeto.

---

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e executar o Animatch em sua máquina local.

### Pré-requisitos
* Python 3.8+
* Pip (Gerenciador de pacotes do Python)

### 1. Estrutura de Pastas
Certifique-se de que o projeto mantém a seguinte estrutura:

```
/Animatch
├── /backend
│   ├── main.py
│   └── requirements.txt
├── /frontend
│   ├── app.py
│   └── requirements.txt
├── /datasets
│   ├── anime.csv
│   └── rating.csv
└── README.md
```

### 2. Configuração e Execução do Backend
O backend é o cérebro do sistema. Ele precisa ser iniciado primeiro.

```bash
# 1. Navegue até a pasta do backend
cd backend

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o servidor da API
uvicorn main:app --reload
```

O servidor estará rodando em `http://127.0.0.1:8000`. Deixe este terminal aberto.

### 3. Configuração e Execução do Frontend

O frontend é a interface com o usuário. Ele deve ser executado em um novo terminal.

```bash
# 1. Navegue até a pasta do frontend (a partir da raiz do projeto)
cd frontend

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie a aplicação web
streamlit run app.py
```

A aplicação estará disponível no seu navegador em `http://localhost:8501`.

## 🧠 Como o Sistema Funciona: A Lógica de Recomendação

O Animatch utiliza **Filtragem Colaborativa Baseada em Itens (Item-Based Collaborative Filtering)**. A ideia central é que as melhores recomendações vêm da sabedoria coletiva da comunidade de usuários.

O conceito é: Animes são considerados "similares" não por seus gêneros ou estúdios, mas porque os mesmos usuários tendem a avaliá-los de forma parecida. Por exemplo, se muitos usuários que deram nota alta para "Cowboy Bebop" também deram nota alta para "Samurai Champloo", o sistema aprende que esses dois animes são conceitualmente similares no gosto do público.

O processo ocorre em três etapas principais:

1.  **Criação da Matriz de Utilidade**: O sistema transforma os dados de `rating.csv` em uma grande matriz onde as linhas são os animes, as colunas são os usuários e as células contêm as notas. Células vazias são preenchidas com 0.

2.  **Cálculo de Similaridade**: Usando essa matriz, o sistema calcula um "índice de similaridade" entre cada par de animes. Para isso, utilizamos a métrica de **Similaridade de Cosseno**.

3.  **Geração de Recomendações**: Quando um usuário pede uma recomendação, o sistema identifica os animes que ele mais gostou (suas maiores notas). Em seguida, ele encontra os animes mais similares àqueles que o usuário já ama e os recomenda, garantindo que o usuário ainda não os tenha visto.

### Métrica de Similaridade: Por que a Similaridade de Cosseno?

A Similaridade de Cosseno foi escolhida por sua eficácia em ambientes de recomendação. Ela mede o ângulo entre os vetores de avaliação de dois animes. Isso a torna ideal para nosso cenário porque ela foca na *direção* dos gostos em vez da *magnitude* das notas. Ou seja, ela consegue identificar que dois animes são similares mesmo que um usuário tenda a dar notas 8-10 e outro, mais conservador, dê notas 6-8. O padrão de preferência é o que importa.

## 📈 Avaliação de Acurácia: Medindo a Performance

Como a Acurácia Funciona no Animatch:

1.  **Seleção do Usuário**: Na aba "Avaliar Acurácia", um usuário de teste é selecionado.

2.  **Divisão dos Dados**: O histórico de animes que este usuário avaliou bem (nota 7 ou superior) é dividido aleatoriamente em duas partes:

    *   **Parte 1 (Conjunto de Treino - 80% dos dados)**: Simula o conhecimento que o sistema tem sobre os gostos do usuário.

    *   **Parte 2 (Conjunto de Gabarito - 20% restantes)**: Fica "escondida" do modelo e serve para validar se as recomendações estão corretas.

3.  **Geração das Recomendações**: O sistema gera uma lista de N (no nosso caso, 10) animes recomendados, baseando-se apenas nos animes da Parte 1.

4.  **Cálculo dos Acertos**: O sistema verifica quantos dos 10 animes recomendados também estão presentes na Parte 2 (o gabarito).

A métrica final é calculada da seguinte forma:
$$Precisão = \frac{\text{Número de Acertos}}{\text{N (Total de Recomendações)}} $$

Por exemplo, se recomendamos 10 animes e 2 deles estavam no conjunto de gabarito, a precisão do modelo para aquele usuário é de 20%. Este método é muito mais estável e informativo do que tentar adivinhar um único item, fornecendo uma visão realista da performance do Animatch.

## ⚙️ Funcionamento da API e Endpoints

O backend, construído com FastAPI, expõe uma API RESTful para interagir com o sistema de recomendação.

### `GET /recomendar/{user_id}`

*   **Descrição**: Retorna uma lista de animes recomendados para um usuário específico.
*   **Parâmetros**:
    *   `user_id` (int): O ID do usuário para o qual as recomendações devem ser geradas.
*   **Como Funciona**:
    1.  Identifica o anime mais bem avaliado pelo usuário.
    2.  Busca na matriz de similaridade os animes mais parecidos com aquele.
    3.  Filtra os animes que o usuário já assistiu.
    4.  Retorna os `N` animes mais similares restantes.
*   **Exemplo de Resposta**:
    ```json
    {
      "user_id": 123,
      "recommendations": [
        "Samurai Champloo",
        "Trigun",
        "Outlaw Star"
      ]
    }
    ```

### `POST /add_rating`

*   **Descrição**: Adiciona uma nova avaliação de um usuário para um anime e atualiza o modelo de recomendação em tempo real.
*   **Corpo da Requisição** (JSON):
    ```json
    {
      "user_id": 123,
      "anime_id": 456,
      "rating": 9
    }
    ```
*   **Como Funciona**:
    1.  Recebe a nova avaliação.
    2.  Adiciona a avaliação ao final do arquivo `rating.csv`.
    3.  Dispara a função `load_and_process_data()`, que reconstrói a matriz de utilidade e a matriz de similaridade de cosseno com os dados atualizados.
*   **Exemplo de Resposta**:
    ```json
    {
      "status": "success",
      "message": "Avaliação adicionada e modelo atualizado."
    }
    ```

### `GET /evaluate_accuracy/{test_user_id}`

*   **Descrição**: Executa o processo de avaliação de acurácia (Precisão@N) para um usuário de teste.
*   **Parâmetros**:
    *   `test_user_id` (int): O ID do usuário a ser usado para o teste.
*   **Como Funciona**:
    1.  Pega o histórico de animes bem avaliados (nota >= 7) do usuário.
    2.  Divide esse histórico em um conjunto de treino (80%) e um conjunto de gabarito (20%).
    3.  Gera 10 recomendações com base apenas no conjunto de treino.
    4.  Compara as recomendações com o conjunto de gabarito para contar os "acertos".
    5.  Retorna a precisão, a lista de recomendações e a lista de acertos.
*   **Exemplo de Resposta**:
    ```json
    {
        "test_user_id": 1,
        "ground_truth": ["Naruto"],
        "recommendations": ["Bleach", "One Piece", "Dragon Ball Z"],
        "hits": 1,
        "total_recommendations": 10,
        "accuracy": 0.1
    }
    ```

---

## ✨ Funcionalidades Adicionais

* **Visualização de Dados**: Uma aba dedicada para explorar os datasets `anime.csv` e `rating.csv`.
* **Adição de Avaliações em Tempo Real**: Na aba "Adicionar Avaliações", qualquer usuário (novo ou existente) pode adicionar notas para animes. O backend recebe a nova avaliação, salva-a no `rating.csv` e recalcula todo o modelo de similaridade imediatamente, garantindo que a nova informação já influencie as próximas recomendações.

---

