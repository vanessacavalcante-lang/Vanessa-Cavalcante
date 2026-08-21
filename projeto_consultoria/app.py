import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from scipy import stats
import os
from groq import Groq
from dotenv import load_dotenv 
load_dotenv()
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.sm_exceptions import PerfectSeparationError

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Olist Consultoria BI",
    page_icon="📊",
    layout="wide"
)

PASTA = Path(__file__).parent


# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>

/* Fundo */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"]{
    background-color:#EAF4FF;
}

/* Sidebar */
[data-testid="stSidebar"]{
    background-color:#0B3D91;
}

/* Mantém textos/labels da sidebar claros SEM pintar o conteúdo do selectbox */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{
    color:white !important;
}

/* Selectbox e multiselect: fundo branco e texto escuro */
[data-testid="stSidebar"] div[data-baseweb="select"] > div{
    background-color:white !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] input,
[data-testid="stSidebar"] [role="combobox"]{
    color:#111111 !important;
    -webkit-text-fill-color:#111111 !important;
}

/* Seta do select */
[data-testid="stSidebar"] div[data-baseweb="select"] svg{
    fill:#111111 !important;
    color:#111111 !important;
}

/* Tags do multiselect */
[data-testid="stSidebar"] span[data-baseweb="tag"]{
    background-color:#FF4B4B !important;
}

[data-testid="stSidebar"] span[data-baseweb="tag"] span{
    color:white !important;
    -webkit-text-fill-color:white !important;
}

/* Radio */
[data-testid="stSidebar"] [role="radiogroup"] label p{
    color:white !important;
}

/* Títulos */
h1{
    color:#0B3D91;
    font-weight:700;
}

h2,h3{
    color:#1565C0;
}

/* Métricas */
[data-testid="metric-container"]{
    background:#D6EAF8;
    border-radius:15px;
    border:1px solid #90CAF9;
    padding:15px;
    box-shadow:0 3px 8px rgba(0,0,0,.12);
}

/* Dataframes */
[data-testid="stDataFrame"]{
    border-radius:12px;
    overflow:hidden;
}

/* Abas */
button[data-baseweb="tab"]{
    border-radius:8px;
    padding:10px 18px;
}

button[data-baseweb="tab"][aria-selected="true"]{
    background:#1976D2;
    color:white;
}

hr{
    border:1px solid #90CAF9;
}


/* Evita resíduos visuais da sidebar durante reruns */
[data-testid="stSidebarContent"]{
    overflow-y:auto;
}

/* Garante que o conteúdo principal da sidebar use o fluxo normal */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
    position:relative;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CONSTANTES
# ============================================================

REGIOES = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",

    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste",
    "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",

    "DF": "Centro-Oeste", "GO": "Centro-Oeste",
    "MT": "Centro-Oeste", "MS": "Centro-Oeste",

    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",

    "PR": "Sul", "RS": "Sul", "SC": "Sul"
}

CAPITAIS = {
    "AC": (-9.97499, -67.8243),
    "AL": (-9.66599, -35.7350),
    "AP": (0.03493, -51.0694),
    "AM": (-3.11903, -60.0217),
    "BA": (-12.9714, -38.5014),
    "CE": (-3.71722, -38.5434),
    "DF": (-15.7939, -47.8828),
    "ES": (-20.3155, -40.3128),
    "GO": (-16.6869, -49.2648),
    "MA": (-2.53073, -44.3068),
    "MT": (-15.6014, -56.0979),
    "MS": (-20.4697, -54.6201),
    "MG": (-19.9167, -43.9345),
    "PA": (-1.45583, -48.5039),
    "PB": (-7.11950, -34.8450),
    "PR": (-25.4284, -49.2733),
    "PE": (-8.04756, -34.8770),
    "PI": (-5.08921, -42.8016),
    "RJ": (-22.9068, -43.1729),
    "RN": (-5.79448, -35.2110),
    "RS": (-30.0346, -51.2177),
    "RO": (-8.76077, -63.8999),
    "RR": (2.82384, -60.6753),
    "SC": (-27.5949, -48.5482),
    "SP": (-23.5505, -46.6333),
    "SE": (-10.9472, -37.0731),
    "TO": (-10.1840, -48.3336)
}

ORDEM_REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def procurar_arquivo(nome, obrigatorio=True):
    for arquivo in PASTA.glob("*.csv"):
        if nome.lower() in arquivo.name.lower():
            return arquivo

    if obrigatorio:
        st.error(f"Arquivo não encontrado: {nome}")
        st.write("Arquivos CSV encontrados:")
        for arquivo in PASTA.glob("*.csv"):
            st.write(arquivo.name)
        st.stop()

    return None


def formatar_valor(valor):
    if pd.isna(valor):
        return "0"

    valor = float(valor)

    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:.1f} M"

    if abs(valor) >= 1_000:
        return f"{valor / 1_000:.1f} mil"

    return f"{valor:,.0f}".replace(",", ".")


def formatar_moeda(valor):
    return f"R$ {formatar_valor(valor)}"


def percentual(serie):
    total = serie.sum()
    if total == 0:
        return serie * 0
    return serie / total * 100


def sentimento_predominante_seguro(x):
    x = x.dropna()

    if x.empty:
        return "Sem comentário"

    moda = x.mode()

    if moda.empty:
        return "Sem comentário"

    return moda.iloc[0]


def distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Distância em linha reta sobre a superfície terrestre (km).
    Aceita Series/arrays do pandas/numpy.
    """
    lat1 = np.radians(lat1.astype(float))
    lon1 = np.radians(lon1.astype(float))
    lat2 = np.radians(lat2.astype(float))
    lon2 = np.radians(lon2.astype(float))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )

    a = np.clip(a, 0, 1)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return 6371.0 * c


def grafico_barras_percentual(
    dados,
    x,
    y,
    titulo,
    nome_x=None,
    nome_y="Quantidade",
    percentual_col="Percentual"
):
    dados = dados.sort_values(y, ascending=False).copy()

    fig = px.bar(
        dados,
        x=x,
        y=y,
        text=percentual_col,
        title=titulo,
        labels={
            x: nome_x or x,
            y: nome_y
        }
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis={"categoryorder": "total descending"},
        margin=dict(t=60, r=20, b=20, l=20)
    )

    return fig


def classificar_nota(score):
    if pd.isna(score):
        return "Sem avaliação"

    if score >= 4:
        return "Boa"

    if score == 3:
        return "Neutra"

    return "Ruim"


# ============================================================
# CARREGAR E TRATAR DADOS
# ============================================================

@st.cache_data(show_spinner="Carregando e preparando os dados...")
def carregar_dados():

    # --------------------------------------------------------
    # 1. Bases originais
    # --------------------------------------------------------

    orders = pd.read_csv(
        procurar_arquivo("olist_orders_dataset"),
        usecols=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    )

    items = pd.read_csv(
        procurar_arquivo("olist_order_items_dataset"),
        usecols=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value"
        ]
    )

    payments = pd.read_csv(
        procurar_arquivo("olist_order_payments_dataset"),
        usecols=[
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value"
        ]
    )

    reviews = pd.read_csv(
        procurar_arquivo("olist_order_reviews_dataset"),
        usecols=lambda c: c in {
            "review_id",
            "order_id",
            "review_score",
            "review_comment_message",
            "review_answer_timestamp"
        }
    )

    customers = pd.read_csv(
        procurar_arquivo("olist_customers_dataset"),
        usecols=[
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state"
        ]
    )

    products = pd.read_csv(
        procurar_arquivo("olist_products_dataset"),
        usecols=[
            "product_id",
            "product_category_name"
        ]
    )

    geolocation = pd.read_csv(
        procurar_arquivo("olist_geolocation_dataset"),
        usecols=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng"
        ]
    )

    translation = pd.read_csv(
        procurar_arquivo("product_category_name_translation")
    )

    sellers_path = procurar_arquivo("olist_sellers_dataset", obrigatorio=False)

    if sellers_path is not None:
        sellers = pd.read_csv(
            sellers_path,
            usecols=[
                "seller_id",
                "seller_zip_code_prefix",
                "seller_city",
                "seller_state"
            ]
        )
    else:
        sellers = pd.DataFrame()

    # --------------------------------------------------------
    # 2. Sentimentos previamente processados
    # --------------------------------------------------------

    sentimentos = pd.read_csv(
        procurar_arquivo("resultado_sentimentos")
    )

    reviews = reviews.copy()

    if "sentimento_texto" not in sentimentos.columns:
        st.error(
            "A coluna 'sentimento_texto' não foi encontrada "
            "em resultado_sentimentos.csv."
        )
        st.stop()

    # Preferir associação por review_id quando disponível.
    if (
        "review_id" in reviews.columns
        and "review_id" in sentimentos.columns
    ):
        reviews = reviews.merge(
            sentimentos[["review_id", "sentimento_texto"]]
            .drop_duplicates("review_id"),
            on="review_id",
            how="left"
        )
    elif len(sentimentos) == len(reviews):
        reviews["sentimento_texto"] = sentimentos["sentimento_texto"].values
    else:
        st.error(
            "Não foi possível associar resultado_sentimentos.csv às avaliações. "
            "O arquivo deve possuir review_id ou manter exatamente a mesma "
            "quantidade e ordem das linhas da base original."
        )
        st.stop()

    mapa_sentimentos = {
        "POS": "Positivo",
        "NEU": "Neutro",
        "NEG": "Negativo",
        "positive": "Positivo",
        "neutral": "Neutro",
        "negative": "Negativo",
        "Positivo": "Positivo",
        "Neutro": "Neutro",
        "Negativo": "Negativo"
    }

    reviews["sentimento_texto"] = (
        reviews["sentimento_texto"]
        .map(mapa_sentimentos)
    )

    # --------------------------------------------------------
    # 3. Reclamações previamente classificadas por IA
    # --------------------------------------------------------

    reclamacoes_path = procurar_arquivo(
        "resultado_reclamacoes",
        obrigatorio=False
    )

    if reclamacoes_path is not None:
        reclamacoes_ia = pd.read_csv(reclamacoes_path)

        colunas_reclamacao = [
            c for c in [
                "review_id",
                "order_id",
                "categoria_reclamacao",
                "confianca_reclamacao"
            ]
            if c in reclamacoes_ia.columns
        ]

        if "categoria_reclamacao" in reclamacoes_ia.columns:
            if (
                "review_id" in reviews.columns
                and "review_id" in reclamacoes_ia.columns
            ):
                reviews = reviews.merge(
                    reclamacoes_ia[colunas_reclamacao]
                    .drop_duplicates("review_id"),
                    on="review_id",
                    how="left",
                    suffixes=("", "_ia")
                )
            elif (
                "order_id" in reclamacoes_ia.columns
                and "order_id" in reviews.columns
            ):
                cols = [c for c in colunas_reclamacao if c != "review_id"]
                reviews = reviews.merge(
                    reclamacoes_ia[cols]
                    .drop_duplicates("order_id"),
                    on="order_id",
                    how="left",
                    suffixes=("", "_ia")
                )
            else:
                reviews["categoria_reclamacao"] = np.nan
        else:
            reviews["categoria_reclamacao"] = np.nan
    else:
        reviews["categoria_reclamacao"] = np.nan

    if "confianca_reclamacao" not in reviews.columns:
        reviews["confianca_reclamacao"] = np.nan

    # --------------------------------------------------------
    # 4. Uma avaliação por pedido
    # --------------------------------------------------------

    if "review_answer_timestamp" in reviews.columns:
        reviews["review_answer_timestamp"] = pd.to_datetime(
            reviews["review_answer_timestamp"],
            errors="coerce"
        )

        reviews_pedido = (
            reviews
            .sort_values("review_answer_timestamp")
            .drop_duplicates("order_id", keep="last")
        )
    else:
        reviews_pedido = reviews.drop_duplicates("order_id", keep="last")

    # --------------------------------------------------------
    # 5. Pagamentos agregados por pedido
    #
    # Evita multiplicar faturamento quando um pedido possui
    # vários itens e várias parcelas/tipos de pagamento.
    # --------------------------------------------------------

    pagamentos_pedido = (
        payments
        .groupby("order_id", as_index=False)
        .agg(
            payment_value=("payment_value", "sum"),
            payment_installments=("payment_installments", "max")
        )
    )

    pagamento_principal = (
        payments
        .sort_values(
            ["order_id", "payment_value"],
            ascending=[True, False]
        )
        .drop_duplicates("order_id")
        [["order_id", "payment_type"]]
    )

    pagamentos_pedido = pagamentos_pedido.merge(
        pagamento_principal,
        on="order_id",
        how="left"
    )

    # --------------------------------------------------------
    # 6. Base principal em nível de PEDIDO
    # --------------------------------------------------------

    pedidos = (
        orders
        .merge(
            pagamentos_pedido,
            on="order_id",
            how="left"
        )
        .merge(
            reviews_pedido[
                [
                    "order_id",
                    "review_score",
                    "review_comment_message",
                    "sentimento_texto",
                    "categoria_reclamacao",
                    "confianca_reclamacao"
                ]
            ],
            on="order_id",
            how="left"
        )
        .merge(
            customers,
            on="customer_id",
            how="left"
        )
    )

    # --------------------------------------------------------
    # 7. Datas e novas variáveis logísticas
    # --------------------------------------------------------

    datas = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    for col in datas:
        pedidos[col] = pd.to_datetime(
            pedidos[col],
            errors="coerce"
        )

    pedidos["ano_mes"] = (
        pedidos["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    # Tempo do prazo de entrega:
    # intervalo entre compra e data prometida.
    pedidos["prazo_entrega_dias"] = (
        pedidos["order_estimated_delivery_date"]
        - pedidos["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # Tempo real de entrega.
    pedidos["dias_entrega"] = (
        pedidos["order_delivered_customer_date"]
        - pedidos["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # Dias de atraso. Negativo = entrega antes do prazo.
    pedidos["dias_atraso"] = (
        pedidos["order_delivered_customer_date"]
        - pedidos["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    pedidos["atrasou"] = pedidos["dias_atraso"] > 0

    # Região do cliente.
    pedidos["regiao"] = (
        pedidos["customer_state"]
        .map(REGIOES)
    )

    pedidos["nota"] = (
        pedidos["review_score"]
        .apply(classificar_nota)
    )

    # Reclamação: sentimento negativo.
    # Se o resultado de sentimentos estiver disponível, este é
    # um critério consistente para selecionar textos a serem
    # tipificados pelo classificador de reclamações.
    pedidos["eh_reclamacao"] = (
        pedidos["sentimento_texto"].eq("Negativo")
    )

    # --------------------------------------------------------
    # 8. Geolocalização resumida por CEP
    # --------------------------------------------------------

    geo_resumo = (
        geolocation
        .groupby(
            "geolocation_zip_code_prefix",
            as_index=False
        )
        .agg(
            lat=("geolocation_lat", "mean"),
            lon=("geolocation_lng", "mean")
        )
    )

    # Cliente -> coordenadas.
    pedidos = pedidos.merge(
        geo_resumo.rename(
            columns={
                "geolocation_zip_code_prefix": "customer_zip_code_prefix",
                "lat": "cliente_lat",
                "lon": "cliente_lon"
            }
        ),
        on="customer_zip_code_prefix",
        how="left"
    )

    # --------------------------------------------------------
    # 9. Distância cliente -> capital do estado
    # --------------------------------------------------------

    pedidos["capital_lat"] = pedidos["customer_state"].map(
        lambda uf: CAPITAIS.get(uf, (np.nan, np.nan))[0]
    )

    pedidos["capital_lon"] = pedidos["customer_state"].map(
        lambda uf: CAPITAIS.get(uf, (np.nan, np.nan))[1]
    )

    mascara_capital = (
        pedidos["cliente_lat"].notna()
        & pedidos["cliente_lon"].notna()
        & pedidos["capital_lat"].notna()
        & pedidos["capital_lon"].notna()
    )

    pedidos["distancia_capital_km"] = np.nan

    pedidos.loc[
        mascara_capital,
        "distancia_capital_km"
    ] = distancia_haversine(
        pedidos.loc[mascara_capital, "cliente_lat"],
        pedidos.loc[mascara_capital, "cliente_lon"],
        pedidos.loc[mascara_capital, "capital_lat"],
        pedidos.loc[mascara_capital, "capital_lon"]
    )

    # --------------------------------------------------------
    # 10. Base em nível de ITEM/PRODUTO
    # --------------------------------------------------------

    itens = (
        items
        .merge(
            products,
            on="product_id",
            how="left"
        )
        .merge(
            translation,
            on="product_category_name",
            how="left"
        )
    )

    # Nome amigável da categoria.
    if "product_category_name_english" in itens.columns:
        itens["categoria_produto"] = (
            itens["product_category_name_english"]
            .fillna(itens["product_category_name"])
            .fillna("Sem categoria")
        )
    else:
        itens["categoria_produto"] = (
            itens["product_category_name"]
            .fillna("Sem categoria")
        )

    # Vendedores e distância de origem logística.
    if not sellers.empty:

        itens = itens.merge(
            sellers,
            on="seller_id",
            how="left"
        )

        itens = itens.merge(
            geo_resumo.rename(
                columns={
                    "geolocation_zip_code_prefix": "seller_zip_code_prefix",
                    "lat": "seller_lat",
                    "lon": "seller_lon"
                }
            ),
            on="seller_zip_code_prefix",
            how="left"
        )

    # Informações do pedido para os itens.
    colunas_pedido_itens = [
        "order_id",
        "customer_state",
        "regiao",
        "review_score",
        "sentimento_texto",
        "categoria_reclamacao",
        "confianca_reclamacao",
        "eh_reclamacao",
        "atrasou",
        "dias_atraso",
        "dias_entrega",
        "prazo_entrega_dias",
        "cliente_lat",
        "cliente_lon"
    ]

    itens = itens.merge(
        pedidos[colunas_pedido_itens],
        on="order_id",
        how="left"
    )

    # --------------------------------------------------------
    # 11. Distância origem logística -> cliente
    #
    # O Olist não informa um "centro de distribuição" explícito.
    # Usa-se a localização do seller como PROXY da origem logística.
    # --------------------------------------------------------

    if (
        "seller_lat" in itens.columns
        and "seller_lon" in itens.columns
    ):
        mascara_logistica = (
            itens["seller_lat"].notna()
            & itens["seller_lon"].notna()
            & itens["cliente_lat"].notna()
            & itens["cliente_lon"].notna()
        )

        itens["distancia_origem_cliente_km"] = np.nan

        itens.loc[
            mascara_logistica,
            "distancia_origem_cliente_km"
        ] = distancia_haversine(
            itens.loc[mascara_logistica, "seller_lat"],
            itens.loc[mascara_logistica, "seller_lon"],
            itens.loc[mascara_logistica, "cliente_lat"],
            itens.loc[mascara_logistica, "cliente_lon"]
        )

        distancia_pedido = (
            itens
            .groupby("order_id", as_index=False)
            .agg(
                distancia_origem_cliente_media_km=(
                    "distancia_origem_cliente_km",
                    "mean"
                )
            )
        )

        pedidos = pedidos.merge(
            distancia_pedido,
            on="order_id",
            how="left"
        )

    else:
        pedidos["distancia_origem_cliente_media_km"] = np.nan
        itens["distancia_origem_cliente_km"] = np.nan

    return pedidos, itens, geo_resumo


# ============================================================
# CARREGAR
# ============================================================

df, df_itens, geo_resumo = carregar_dados()


# ============================================================
# SIDEBAR / FILTROS
# ============================================================

logo = PASTA / "imagem.jpeg"

with st.sidebar:

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    if logo.exists():

        st.image(
            str(logo),
            use_container_width=True
        )

    # --------------------------------------------------------
    # TÍTULO DOS FILTROS
    # --------------------------------------------------------

    st.title("Filtros")

    # --------------------------------------------------------
    # FILTRO DE REGIÃO
    # --------------------------------------------------------

    regioes_disponiveis = [
        "Todas",
        "Norte",
        "Nordeste",
        "Centro-Oeste",
        "Sudeste",
        "Sul"
    ]

    regiao_selecionada = st.selectbox(
        "Região",
        options=regioes_disponiveis,
        index=0,
        key="filtro_regiao"
    )

    if regiao_selecionada == "Todas":

        df_regiao = df.copy()

    else:

        df_regiao = df[
            df["regiao"].eq(
                regiao_selecionada
            )
        ].copy()

    # --------------------------------------------------------
    # FILTRO DE ESTADOS
    # --------------------------------------------------------

    modo_estado = st.radio(
        "Visualização dos estados",
        options=[
            "Todos os estados",
            "Selecionar estados"
        ],
        index=0,
        key="modo_estado"
    )

    estados_disponiveis = sorted(
        df_regiao[
            "customer_state"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    if modo_estado == "Todos os estados":

        estados_selecionados = (
            estados_disponiveis
        )

    else:

        estados_selecionados = st.multiselect(
            "Estado do cliente",
            options=estados_disponiveis,
            default=estados_disponiveis,
            key="filtro_estados"
        )

    # --------------------------------------------------------
    # SOBRE O PAINEL
    # --------------------------------------------------------

    st.divider()

    st.markdown("""
### Sobre o painel

Este dashboard analisa:

- Vendas e pedidos
- Entregas e atrasos
- Prazo prometido
- Distâncias logísticas
- Região e estado
- Avaliações
- Sentimentos
- Reclamações
- Produtos
""")

# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df_regiao[
    df_regiao[
        "customer_state"
    ].isin(
        estados_selecionados
    )
].copy()

ids_filtrados = set(
    df_filtrado[
        "order_id"
    ]
)

df_itens_filtrado = df_itens[
    df_itens[
        "order_id"
    ].isin(
        ids_filtrados
    )
].copy()


# ============================================================
# CABEÇALHO
# ============================================================

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    if logo.exists():
        st.image(
            str(logo),
            width=120
        )

with col_titulo:
    st.title("Olist Business Intelligence")
    st.caption(
        "Consultoria Estatística aplicada a vendas, logística, "
        "satisfação e experiência do cliente"
    )

regiao_texto = (
    "Brasil"
    if regiao_selecionada == "Todas"
    else regiao_selecionada
)

st.info(
    f"📍 Região analisada: **{regiao_texto}** | "
    f"Estados no filtro: **{len(estados_selecionados)}** | "
    f"Pedidos: **{df_filtrado['order_id'].nunique():,}**"
)


# ============================================================
# ABAS
# ============================================================

abas = st.tabs([
    "Descrição",
    "Visão Geral",
    "Análises Estatísticas",
    "Sentimento por Comentários",
    "Mapa",
    "Recomendações",
    "Dados",
    "Assistente IA"
])


# ============================================================
# ABA 0 — DESCRIÇÃO
# ============================================================

with abas[0]:

    st.header("Descrição do Projeto")

    st.markdown("""
Neste trabalho foi desenvolvido um dashboard interativo para
análise do conjunto de dados do e-commerce Olist, integrando
**Estatística, Ciência de Dados, Business Intelligence e
Inteligência Artificial**.

### Objetivo

Transformar os dados de pedidos, pagamentos, entregas,
avaliações e localização em informações úteis para tomada de
decisão, com foco em desempenho comercial, logística e
satisfação dos clientes.

### Alunos

- Jefferson Balbino Rodrigues
- Thaisa Érica da Costa Azevedo
- Vanessa Cavalcante da Silva

### Professor

- Pedro Monteiro

### Curso/Disciplina

Estatística — Consultoria Estatística

### Perguntas de negócio

- Entregas atrasadas reduzem a nota média?
- Quais estados e regiões concentram os pedidos?
- Qual é o prazo médio prometido de entrega?
- Distâncias logísticas maiores estão associadas a atrasos?
- Clientes mais distantes das capitais apresentam maior atraso?
- Os sentimentos dos comentários confirmam as notas?
- Quais são os principais tipos de reclamação?
- Qual parcela das reclamações está relacionada à entrega?
- Quais categorias/produtos concentram mais reclamações?
- Quais produtos reclamados apresentam maior taxa de atraso?

### Metodologia

Os sentimentos dos comentários são processados previamente e
salvos em `resultado_sentimentos.csv`. O dashboard apenas lê o
resultado pronto, evitando carregar o modelo de linguagem a cada
execução.

A classificação do **tipo de reclamação** também pode ser
processada previamente e salva em `resultado_reclamacoes.csv`.

### Observação sobre distância logística

A base Olist não identifica explicitamente um centro de
distribuição. Por isso, a distância entre **vendedor (seller) e
cliente** é utilizada como uma *proxy* da distância de origem
logística até a residência do cliente. A distância é calculada
pela fórmula de Haversine a partir das coordenadas médias do CEP.
""")


# ============================================================
# ABA 1 — VISÃO GERAL | ANÁLISE DESCRITIVA
# ============================================================

with abas[1]:

    st.header("Análise Descritiva dos Dados")

    receita = df_filtrado["payment_value"].sum()
    pedidos_total = df_filtrado["order_id"].nunique()
    clientes_total = df_filtrado["customer_unique_id"].nunique()
    estados_total = df_filtrado["customer_state"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Faturamento",
        formatar_moeda(receita)
    )

    col2.metric(
        "Pedidos",
        formatar_valor(pedidos_total)
    )

    col3.metric(
        "Clientes",
        formatar_valor(clientes_total)
    )

    col4.metric(
        "Estados atendidos",
        estados_total
    )

    st.divider()

    st.subheader("Estatísticas financeiras por pedido")

    resumo_financeiro = (
        df_filtrado["payment_value"]
        .describe()
        .rename({
            "count": "Quantidade",
            "mean": "Média",
            "std": "Desvio-padrão",
            "min": "Mínimo",
            "25%": "1º quartil",
            "50%": "Mediana",
            "75%": "3º quartil",
            "max": "Máximo"
        })
        .round(2)
    )

    st.dataframe(
        resumo_financeiro,
        use_container_width=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        avaliacoes = (
            df_filtrado["review_score"]
            .dropna()
            .value_counts()
            .sort_index()
            .rename_axis("Nota")
            .reset_index(name="Quantidade")
        )

        avaliacoes["Percentual"] = percentual(
            avaliacoes["Quantidade"]
        )

        fig = grafico_barras_percentual(
            avaliacoes,
            x="Nota",
            y="Quantidade",
            titulo="Distribuição das avaliações",
            nome_x="Nota"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        notas = (
            df_filtrado["nota"]
            .value_counts()
            .rename_axis("Classificação")
            .reset_index(name="Quantidade")
        )

        notas["Percentual"] = percentual(
            notas["Quantidade"]
        )

        fig = grafico_barras_percentual(
            notas,
            x="Classificação",
            y="Quantidade",
            titulo="Classificação das notas",
            nome_x="Classificação"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        pagamento = (
            df_filtrado["payment_type"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("Pagamento")
            .reset_index(name="Quantidade")
        )

        pagamento["Percentual"] = percentual(
            pagamento["Quantidade"]
        )

        fig = grafico_barras_percentual(
            pagamento,
            x="Pagamento",
            y="Quantidade",
            titulo="Tipos de pagamento",
            nome_x="Forma de pagamento"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        st.subheader("Tempo de entrega")

        entrega = (
            df_filtrado["dias_entrega"]
            .dropna()
            .describe()
            .rename({
                "count": "Quantidade",
                "mean": "Média",
                "std": "Desvio-padrão",
                "min": "Mínimo",
                "25%": "1º quartil",
                "50%": "Mediana",
                "75%": "3º quartil",
                "max": "Máximo"
            })
            .round(2)
        )

        st.dataframe(
            entrega,
            use_container_width=True
        )

    st.divider()

    ticket_medio = df_filtrado["payment_value"].mean()
    nota_media = df_filtrado["review_score"].mean()
    atraso_pct = df_filtrado["atrasou"].mean() * 100

    st.success(
        f"**Ticket médio:** R$ {ticket_medio:,.2f}  \n"
        f"**Nota média:** {nota_media:.2f}  \n"
        f"**Pedidos atrasados:** {atraso_pct:.1f}%  \n"
        f"**Faturamento:** {formatar_moeda(receita)}"
    )


# ============================================================
# ABA 1 — VISÃO GERAL | RESUMO EXECUTIVO
# ============================================================

with abas[1]:

    st.divider()

    st.header("Resumo Executivo")

    receita = df_filtrado["payment_value"].sum()
    pedidos = df_filtrado["order_id"].nunique()
    clientes = df_filtrado["customer_unique_id"].nunique()
    nota_media = df_filtrado["review_score"].mean()
    atraso_pct = df_filtrado["atrasou"].mean() * 100

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Faturamento",
        formatar_moeda(receita)
    )

    col2.metric(
        "Pedidos",
        formatar_valor(pedidos)
    )

    col3.metric(
        "Clientes",
        formatar_valor(clientes)
    )

    col4.metric(
        "Nota média",
        f"{nota_media:.2f}"
    )

    col5.metric(
        "Pedidos atrasados",
        f"{atraso_pct:.1f}%"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        pedidos_estado = (
            df_filtrado
            .groupby("customer_state")["order_id"]
            .nunique()
            .sort_values(ascending=False)
            .rename_axis("Estado")
            .reset_index(name="Quantidade")
        )

        pedidos_estado["Percentual"] = percentual(
            pedidos_estado["Quantidade"]
        )

        fig = grafico_barras_percentual(
            pedidos_estado,
            x="Estado",
            y="Quantidade",
            titulo="Pedidos por estado",
            nome_x="Estado"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        pedidos_regiao = (
            df_filtrado
            .groupby("regiao")["order_id"]
            .nunique()
            .sort_values(ascending=False)
            .rename_axis("Região")
            .reset_index(name="Quantidade")
        )

        pedidos_regiao["Percentual"] = percentual(
            pedidos_regiao["Quantidade"]
        )

        fig = grafico_barras_percentual(
            pedidos_regiao,
            x="Região",
            y="Quantidade",
            titulo="Representatividade dos pedidos por região",
            nome_x="Região"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# ABA 2 — ANÁLISES ESTATÍSTICAS | LOGÍSTICA
# ============================================================




with abas[2]:

    st.header("Análise Logística")

    st.write(
        "Esta seção apresenta o prazo prometido, o tempo real "
        "de entrega, os atrasos e as novas variáveis de distância."
    )

    prazo_medio = df_filtrado["prazo_entrega_dias"].mean()
    entrega_media = df_filtrado["dias_entrega"].mean()

    atraso_medio = df_filtrado.loc[df_filtrado["atrasou"], "dias_atraso"].mean()

    distancia_capital = df_filtrado["distancia_capital_km"].mean()

    distancia_logistica = df_filtrado["distancia_origem_cliente_media_km"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Prazo prometido médio", f"{prazo_medio:.1f} dias")

    col2.metric("Tempo real médio", f"{entrega_media:.1f} dias")

    col3.metric(
        "Atraso médio dos atrasados",
        (f"{atraso_medio:.1f} dias" if pd.notna(atraso_medio) else "Sem atrasos"),
    )

    col4.metric(
        "Distância média da capital",
        (f"{distancia_capital:.0f} km" if pd.notna(distancia_capital) else "Sem dados"),
    )

    col5.metric(
        "Distância logística média",
        (f"{distancia_logistica:.0f} km" if pd.notna(distancia_logistica) else "Sem dados"),
    )

    st.caption(
        "A distância logística usa o vendedor como proxy da origem "
        "porque a base Olist não fornece um centro de distribuição explícito."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        prazo_regiao = (
            df_filtrado.groupby("regiao", as_index=False)
            .agg(prazo_medio=("prazo_entrega_dias", "mean"))
            .sort_values("prazo_medio", ascending=False)
        )

        fig = px.bar(
            prazo_regiao,
            x="regiao",
            y="prazo_medio",
            text="prazo_medio",
            title="Prazo prometido médio por região",
            labels={"regiao": "Região", "prazo_medio": "Prazo médio (dias)"},
        )

        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        atraso_regiao = (
            df_filtrado.groupby("regiao", as_index=False)
            .agg(Percentual=("atrasou", lambda s: s.mean() * 100))
            .sort_values("Percentual", ascending=False)
        )

        fig = px.bar(
            atraso_regiao,
            x="regiao",
            y="Percentual",
            text="Percentual",
            title="Taxa de atraso por região",
            labels={"regiao": "Região", "Percentual": "Pedidos atrasados (%)"},
        )

        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        distancia_status = (
            df_filtrado.dropna(subset=["distancia_origem_cliente_media_km"])
            .assign(Status=lambda x: x["atrasou"].map({True: "Atrasada", False: "No prazo"}))
            .groupby("Status", as_index=False)
            .agg(Distância=("distancia_origem_cliente_media_km", "mean"))
        )

        if not distancia_status.empty:

            fig = px.bar(
                distancia_status,
                x="Status",
                y="Distância",
                text="Distância",
                title="Distância logística média por status",
                labels={"Distância": "Distância média (km)"},
            )

            fig.update_traces(texttemplate="%{text:.0f} km", textposition="outside")

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(
                "Não há coordenadas suficientes para calcular "
                "a distância logística neste filtro."
            )

    with col2:

        distancia_capital_status = (
            df_filtrado.dropna(subset=["distancia_capital_km"])
            .assign(Status=lambda x: x["atrasou"].map({True: "Atrasada", False: "No prazo"}))
            .groupby("Status", as_index=False)
            .agg(Distância=("distancia_capital_km", "mean"))
        )

        if not distancia_capital_status.empty:

            fig = px.bar(
                distancia_capital_status,
                x="Status",
                y="Distância",
                text="Distância",
                title="Distância da capital por status",
                labels={"Distância": "Distância média (km)"},
            )

            fig.update_traces(texttemplate="%{text:.0f} km", textposition="outside")

            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.header("Regressão Logística — Avaliação Ruim")

    st.markdown("""
A análise tem uma única variável resposta:

**Avaliação ruim = 1 quando a nota é 1 ou 2; 0 quando a nota é 3, 4 ou 5.**

O objetivo é identificar quais características da compra, da logística,
do pagamento, do produto e da localização estão associadas à
**chance de uma avaliação ruim**.

Ao alterar os filtros de região ou estado, o modelo é recalculado.
O refinamento é automático e mantém as mesmas regras estatísticas
definidas no projeto.
""")

    fluxo_modelagem = pd.DataFrame(
        {
            "Etapa": ["1", "2", "3", "4", "5", "6"],
            "Procedimento": [
                "Seleção das explicativas",
                "Tratamento das categóricas",
                "Multicolinearidade (VIF)",
                "Ajuste da regressão logística",
                "Refinamento do modelo",
                "Diagnóstico final",
            ],
            "Critério principal": [
                "Variáveis coerentes e sem vazamento da própria avaliação",
                "Agrupamento apenas quando necessário e categoria de referência",
                "VIF ≤ 10, com retirada sequencial quando necessário",
                "Modelo Logístico Binomial com link logit",
                "Se >40% não significativas, retirar a maior p uma por vez e reajustar",
                "Resíduos Pearson/deviance, influência e Hosmer-Lemeshow como diagnóstico/alerta",
            ],
        }
    )

    with st.expander("Ver sequência da modelagem", expanded=True):
        st.dataframe(fluxo_modelagem, use_container_width=True, hide_index=True)

    # ========================================================
    # FUNÇÕES AUXILIARES
    # ========================================================

    def calcular_aicc(aic, n, k):
        if pd.isna(aic) or n <= k + 1:
            return np.nan

        return aic + (2 * k * (k + 1)) / (n - k - 1)

    def remover_colinearidade(dados_modelo, colunas):
        """
        Remove variáveis constantes e dependência linear perfeita.
        """
        validas = []
        removidas = []

        for col in colunas:

            if col not in dados_modelo.columns or dados_modelo[col].dropna().nunique() <= 1:
                removidas.append(col)

            else:
                validas.append(col)

        independentes = []

        for col in validas:

            teste = independentes + [col]

            matriz = dados_modelo[teste].astype(float).to_numpy()

            matriz = np.column_stack([np.ones(len(matriz)), matriz])

            if np.linalg.matrix_rank(matriz) == matriz.shape[1]:
                independentes.append(col)

            else:
                removidas.append(col)

        return independentes, removidas

    def aplicar_vif_iterativo(dados_modelo, colunas, limite=10.0):
        """
        Calcula o VIF com intercepto e remove APENAS uma variável
        por vez: sempre a que apresentar o maior VIF.

        Após cada remoção, todos os VIFs são recalculados.
        O processo termina quando todos os VIFs ficam <= limite.
        """

        colunas_atuais = list(colunas)
        removidas_vif = []
        historico = []

        if not colunas_atuais:
            return [], [], pd.DataFrame(), [], False

        def calcular_tabela_vif(cols):

            if len(cols) == 1:
                return pd.DataFrame({"Variável": cols, "VIF": [1.0]})

            X = dados_modelo[cols].astype(float).replace([np.inf, -np.inf], np.nan).dropna().copy()

            if X.empty:
                return pd.DataFrame()

            # O VIF padrão é calculado com intercepto.
            X_const = sm.add_constant(X, has_constant="add")

            valores = []

            # Índice 0 = constante; não exibimos/removemos a constante.
            for i, col in enumerate(X_const.columns):

                if col == "const":
                    continue

                try:
                    vif = variance_inflation_factor(X_const.to_numpy(dtype=float), i)
                except Exception:
                    vif = np.inf

                if not np.isfinite(vif):
                    vif = np.inf

                valores.append({"Variável": col, "VIF": float(vif)})

            return pd.DataFrame(valores).sort_values("VIF", ascending=False).reset_index(drop=True)

        max_iter = max(1, len(colunas_atuais) + 2)

        for _ in range(max_iter):

            tabela = calcular_tabela_vif(colunas_atuais)

            if tabela.empty:
                return (colunas_atuais, removidas_vif, tabela, historico, False)

            maior_variavel = tabela.iloc[0]["Variável"]

            maior_vif = tabela.iloc[0]["VIF"]

            if pd.notna(maior_vif) and maior_vif <= limite:
                return (colunas_atuais, removidas_vif, tabela, historico, True)

            if len(colunas_atuais) <= 1:
                return (colunas_atuais, removidas_vif, tabela, historico, False)

            # Remove somente a variável de MAIOR VIF.
            historico.append(
                {"Variável removida": maior_variavel, "VIF no momento da remoção": maior_vif}
            )

            removidas_vif.append(maior_variavel)

            colunas_atuais.remove(maior_variavel)

        tabela_final = calcular_tabela_vif(colunas_atuais)

        valido = not tabela_final.empty and (tabela_final["VIF"] <= limite).all()

        return (colunas_atuais, removidas_vif, tabela_final, historico, bool(valido))

    def _status_diagnostico(atendido):
        if atendido is True:
            return "Atendido"
        if atendido is False:
            return "Não atendido"
        return "Informativo"

    def _shapiro_amostra(valores, max_n=5000):
        """
        Shapiro-Wilk em amostra de até 5.000 observações.
        Para resíduos quantílicos é usado apenas como diagnóstico
        complementar, não como critério obrigatório nos MLGs.
        """
        try:
            x = np.asarray(valores, dtype=float)

            x = x[np.isfinite(x)]

            if len(x) < 8:
                return np.nan

            if len(x) > max_n:
                rng = np.random.default_rng(20260816)
                x = rng.choice(x, size=max_n, replace=False)

            return float(stats.shapiro(x).pvalue)

        except Exception:
            return np.nan

    def _residuos_quantilicos_glm(modelo, familia, y):
        """
        Resíduos quantílicos normalizados.

        Para distribuições contínuas:
        r = Phi^-1(F(y)).

        Para distribuições discretas:
        usa randomização determinística dentro do intervalo
        [F(y-1), F(y)].
        """

        try:

            y_arr = np.asarray(y, dtype=float)

            mu = np.asarray(modelo.fittedvalues, dtype=float)

            rng = np.random.default_rng(20260816)

            eps = 1e-10

            if familia == "Gamma":

                phi = float(modelo.scale)

                if not np.isfinite(phi) or phi <= 0:
                    return np.array([])

                shape = 1.0 / phi

                escala = mu * phi

                u = stats.gamma.cdf(y_arr, a=shape, scale=escala)

            elif familia == "Gaussiano Inverso":

                phi = float(modelo.scale)

                if not np.isfinite(phi) or phi <= 0:
                    return np.array([])

                # Parametrização equivalente à variância
                # Var(Y)=phi*mu^3 usada pelo GLM.
                shape_scipy = phi * mu

                scale_scipy = 1.0 / phi

                u = stats.invgauss.cdf(y_arr, mu=shape_scipy, scale=scale_scipy)

            elif familia == "Poisson":

                y_int = y_arr.astype(int)

                inferior = stats.poisson.cdf(y_int - 1, mu)

                superior = stats.poisson.cdf(y_int, mu)

                u = inferior + (superior - inferior) * rng.random(len(y_int))

            elif familia == "Binomial":

                y_int = y_arr.astype(int)

                inferior = stats.bernoulli.cdf(y_int - 1, mu)

                superior = stats.bernoulli.cdf(y_int, mu)

                u = inferior + (superior - inferior) * rng.random(len(y_int))

            else:
                return np.array([])

            u = np.clip(u, eps, 1 - eps)

            return stats.norm.ppf(u)

        except Exception:
            return np.array([])

    def _residuos_quantilicos_nb(modelo, y):
        """
        Resíduos quantílicos normalizados para Binomial Negativa.

        A parametrização utilizada por statsmodels é:
        Var(Y) = mu + alpha * mu^2.
        """

        try:

            y_arr = np.asarray(y, dtype=int)

            mu = np.asarray(modelo.predict(), dtype=float)

            if "alpha" not in modelo.params.index:
                return np.array([])

            alpha = float(modelo.params["alpha"])

            if not np.isfinite(alpha) or alpha <= 0:
                return np.array([])

            tamanho = 1.0 / alpha

            prob = tamanho / (tamanho + mu)

            inferior = stats.nbinom.cdf(y_arr - 1, tamanho, prob)

            superior = stats.nbinom.cdf(y_arr, tamanho, prob)

            rng = np.random.default_rng(20260816)

            u = inferior + (superior - inferior) * rng.random(len(y_arr))

            u = np.clip(u, 1e-10, 1 - 1e-10)

            return stats.norm.ppf(u)

        except Exception:
            return np.array([])

    def _hosmer_lemeshow(y, probabilidades, grupos=10):
        """
        Teste de Hosmer-Lemeshow usado como diagnóstico
        complementar de calibração do modelo logístico.
        """

        try:

            dados_hl = pd.DataFrame(
                {"y": np.asarray(y, dtype=float), "p": np.asarray(probabilidades, dtype=float)}
            ).dropna()

            if len(dados_hl) < 40 or dados_hl["p"].nunique() < 4:
                return (np.nan, np.nan, 0)

            q = min(grupos, max(4, len(dados_hl) // 20))

            dados_hl["grupo"] = pd.qcut(dados_hl["p"], q=q, duplicates="drop")

            tabela = (
                dados_hl.groupby("grupo", observed=True)
                .agg(n=("y", "size"), observado=("y", "sum"), esperado=("p", "sum"))
                .reset_index(drop=True)
            )

            g = len(tabela)

            if g < 4:
                return (np.nan, np.nan, g)

            denominador = tabela["esperado"] * (1 - tabela["esperado"] / tabela["n"])

            valido = denominador > 0

            estatistica = (
                (tabela.loc[valido, "observado"] - tabela.loc[valido, "esperado"]) ** 2
                / denominador[valido]
            ).sum()

            gl = max(g - 2, 1)

            pvalor = stats.chi2.sf(estatistica, gl)

            return (float(estatistica), float(pvalor), g)

        except Exception:
            return (np.nan, np.nan, 0)

    def diagnostico_glm(modelo, y, familia, X=None):
        """
        Diagnóstico específico para:
        - Gamma
        - Gaussiano Inverso
        - Poisson
        - Logístico Binomial

        A normalidade dos resíduos comuns NÃO é exigida nos MLGs.
        O Shapiro é aplicado somente aos resíduos quantílicos e
        apresentado como diagnóstico complementar.

        Na regressão logística, os resíduos são avaliados SOMENTE
        depois que o modelo final já foi definido. Eles funcionam como
        diagnóstico/alerta e não provocam retirada automática de
        variáveis explicativas.

        Para a logística, impedem a aceitação do ajuste apenas problemas
        realmente estruturais, como:
        - resposta sem as duas classes 0/1;
        - não convergência;
        - estimativas não finitas;
        - evidência operacional de separação grave.

        Resíduos Pearson/deviance, influência e Hosmer-Lemeshow são
        apresentados como diagnóstico do modelo final.
        """

        linhas = []
        motivos = []

        y_arr = np.asarray(y, dtype=float)

        fitted = np.asarray(modelo.fittedvalues, dtype=float)

        # ----------------------------------------------------
        # Estrutura da resposta / convergência
        # ----------------------------------------------------

        convergiu = bool(getattr(modelo, "converged", True))

        linhas.append(
            {
                "Teste": "Convergência",
                "Resultado": "Sim" if convergiu else "Não",
                "Critério": "O ajuste deve convergir",
                "Situação": _status_diagnostico(convergiu),
                "Obrigatório": "Sim",
            }
        )

        if not convergiu:
            motivos.append("o algoritmo de estimação não convergiu")

        if familia in {"Gamma", "Gaussiano Inverso"}:

            resposta_ok = bool(np.all(y_arr > 0))

            criterio_resposta = "Resposta contínua e estritamente positiva"

        elif familia == "Poisson":

            resposta_ok = bool(np.all(y_arr >= 0) and np.allclose(y_arr, np.round(y_arr)))

            criterio_resposta = "Contagem inteira e não negativa"

        elif familia == "Binomial":

            valores = set(np.unique(y_arr[np.isfinite(y_arr)]).tolist())

            resposta_ok = valores.issubset({0.0, 1.0}) and len(valores) == 2

            criterio_resposta = "Resposta binária com 0 e 1 presentes"

        else:

            resposta_ok = True
            criterio_resposta = "Resposta compatível"

        linhas.append(
            {
                "Teste": "Estrutura da resposta",
                "Resultado": "Adequada" if resposta_ok else "Inadequada",
                "Critério": criterio_resposta,
                "Situação": _status_diagnostico(resposta_ok),
                "Obrigatório": "Sim",
            }
        )

        if not resposta_ok:
            motivos.append("a variável resposta não possui a estrutura exigida pela família")

        # ----------------------------------------------------
        # Resíduos Pearson e deviance
        # ----------------------------------------------------

        try:

            pearson = np.asarray(modelo.resid_pearson, dtype=float)

        except Exception:

            pearson = np.array([])

        try:

            deviance = np.asarray(modelo.resid_deviance, dtype=float)

        except Exception:

            deviance = np.array([])

        scale = float(getattr(modelo, "scale", 1.0))

        if (
            familia in {"Gamma", "Gaussiano Inverso"}
            and np.isfinite(scale)
            and scale > 0
            and pearson.size
        ):

            pearson_pad = pearson / np.sqrt(scale)

        else:

            pearson_pad = pearson

        residuos_finitos = bool(
            pearson_pad.size > 0
            and np.isfinite(pearson_pad).all()
            and (deviance.size == 0 or np.isfinite(deviance).all())
        )

        linhas.append(
            {
                "Teste": "Resíduos finitos",
                "Resultado": "Sim" if residuos_finitos else "Não",
                "Critério": (
                    "Resíduos Pearson/deviance devem ser finitos; "
                    "na logística é diagnóstico/alerta"
                ),
                "Situação": (
                    _status_diagnostico(residuos_finitos)
                    if familia != "Binomial"
                    else ("Atendido" if residuos_finitos else "Atenção")
                ),
                "Obrigatório": ("Não" if familia == "Binomial" else "Sim"),
            }
        )

        if not residuos_finitos and familia != "Binomial":
            motivos.append("foram encontrados resíduos não finitos")

        if pearson_pad.size:

            prop_extremos = float(np.mean(np.abs(pearson_pad) > 3) * 100)

            extremos_ok = prop_extremos <= 5.0

        else:

            prop_extremos = np.nan
            extremos_ok = False

        linhas.append(
            {
                "Teste": "Resíduos Pearson extremos",
                "Resultado": (f"{prop_extremos:.2f}%" if pd.notna(prop_extremos) else "NA"),
                "Critério": (
                    "Até 5% com |resíduo padronizado| > 3; " "na logística é diagnóstico/alerta"
                ),
                "Situação": (
                    _status_diagnostico(extremos_ok)
                    if familia != "Binomial"
                    else (
                        "Informativo"
                        if pd.isna(prop_extremos)
                        else ("Atendido" if extremos_ok else "Atenção")
                    )
                ),
                "Obrigatório": ("Não" if familia == "Binomial" else "Sim"),
            }
        )

        if not extremos_ok and familia != "Binomial":
            motivos.append("há proporção elevada de resíduos Pearson extremos")

        # ----------------------------------------------------
        # Padrão resíduos x ajustados
        # ----------------------------------------------------

        rho = np.nan

        if deviance.size and len(deviance) == len(fitted):

            mascara = np.isfinite(deviance) & np.isfinite(fitted)

            if mascara.sum() >= 8 and np.nanstd(fitted[mascara]) > 0:

                try:

                    rho = float(stats.spearmanr(fitted[mascara], deviance[mascara]).statistic)

                except Exception:
                    rho = np.nan

        padrao_ok = bool(pd.notna(rho) and abs(rho) <= 0.20)

        linhas.append(
            {
                "Teste": "Padrão resíduos × ajustados",
                "Resultado": (f"|rho| = {abs(rho):.3f}" if pd.notna(rho) else "NA"),
                "Critério": ("|rho de Spearman| ≤ 0,20; " "na logística é diagnóstico/alerta"),
                "Situação": (
                    _status_diagnostico(padrao_ok)
                    if familia != "Binomial"
                    else (
                        "Informativo" if pd.isna(rho) else ("Atendido" if padrao_ok else "Atenção")
                    )
                ),
                "Obrigatório": ("Não" if familia == "Binomial" else "Sim"),
            }
        )

        if not padrao_ok and familia != "Binomial":
            motivos.append(
                "os resíduos apresentam padrão relevante em relação aos valores ajustados"
            )

        # ----------------------------------------------------
        # Influência de Cook — complementar
        # ----------------------------------------------------

        prop_cook = np.nan

        try:

            influencia = modelo.get_influence()

            cooks = np.asarray(influencia.cooks_distance[0], dtype=float)

            cooks = cooks[np.isfinite(cooks)]

            if len(cooks) > 0:

                limite_cook = 4.0 / len(cooks)

                prop_cook = float(np.mean(cooks > limite_cook) * 100)

        except Exception:
            pass

        linhas.append(
            {
                "Teste": "Observações influentes (Cook)",
                "Resultado": (f"{prop_cook:.2f}%" if pd.notna(prop_cook) else "NA"),
                "Critério": "Referência: Cook > 4/n; uso complementar",
                "Situação": (
                    "Informativo"
                    if pd.isna(prop_cook)
                    else ("Atendido" if prop_cook <= 5 else "Atenção")
                ),
                "Obrigatório": "Não",
            }
        )

        # ----------------------------------------------------
        # Família específica
        # ----------------------------------------------------

        dispersao = np.nan

        if familia == "Poisson" and getattr(modelo, "df_resid", 0) > 0:

            dispersao = float(modelo.pearson_chi2 / modelo.df_resid)

            dispersao_ok = 0.7 <= dispersao <= 1.5

            linhas.append(
                {
                    "Teste": "Dispersão de Pearson",
                    "Resultado": f"{dispersao:.3f}",
                    "Critério": "0,70 ≤ dispersão ≤ 1,50",
                    "Situação": _status_diagnostico(dispersao_ok),
                    "Obrigatório": "Sim",
                }
            )

            if not dispersao_ok:
                motivos.append("a dispersão de Pearson é incompatível com o modelo de Poisson")

        if familia == "Binomial":

            eventos = int(np.sum(y_arr))

            nao_eventos = int(len(y_arr) - eventos)

            n_parametros = max(len(modelo.params) - 1, 1)

            minimo_classe = 10 * n_parametros

            eventos_ok = eventos >= minimo_classe and nao_eventos >= minimo_classe

            linhas.append(
                {
                    "Teste": "Eventos por parâmetro",
                    "Resultado": (f"{eventos} eventos | " f"{nao_eventos} não eventos"),
                    "Critério": (f"≥ {minimo_classe} em cada classe " f"(10 por parâmetro)"),
                    "Situação": _status_diagnostico(eventos_ok),
                    "Obrigatório": "Não",
                }
            )

            # O EPV já é verificado antes do ajuste da regressão.
            # Aqui ele é reapresentado apenas como confirmação do
            # modelo final, sem provocar nova retirada de variáveis.

            hl_est, hl_p, hl_g = _hosmer_lemeshow(y_arr, fitted)

            linhas.append(
                {
                    "Teste": "Hosmer-Lemeshow",
                    "Resultado": (f"p = {hl_p:.4f}" if pd.notna(hl_p) else "NA"),
                    "Critério": (
                        "p > 0,05 sugere calibração adequada; " "diagnóstico complementar"
                    ),
                    "Situação": (
                        "Informativo"
                        if pd.isna(hl_p)
                        else ("Atendido" if hl_p > 0.05 else "Atenção")
                    ),
                    "Obrigatório": "Não",
                }
            )

            brier = float(np.mean((y_arr - fitted) ** 2))

            linhas.append(
                {
                    "Teste": "Brier score",
                    "Resultado": f"{brier:.4f}",
                    "Critério": "Quanto menor, melhor; diagnóstico complementar",
                    "Situação": "Informativo",
                    "Obrigatório": "Não",
                }
            )

            # ------------------------------------------------
            # Pseudo-R² de McFadden
            # ------------------------------------------------
            # Compara o log-likelihood do modelo completo com um
            # modelo nulo contendo apenas o intercepto.
            # Não deve ser interpretado como o R² da regressão linear.
            pseudo_r2_mcfadden = np.nan
            ll_nulo = np.nan

            try:

                X_nulo = np.ones((len(y_arr), 1), dtype=float)

                modelo_nulo = sm.GLM(
                    y_arr, X_nulo, family=(sm.families.Binomial(link=(sm.families.links.Logit())))
                ).fit()

                ll_nulo = float(modelo_nulo.llf)

                ll_completo = float(modelo.llf)

                if np.isfinite(ll_nulo) and ll_nulo != 0 and np.isfinite(ll_completo):

                    pseudo_r2_mcfadden = float(1 - (ll_completo / ll_nulo))

            except Exception:

                pseudo_r2_mcfadden = np.nan
                ll_nulo = np.nan

            linhas.append(
                {
                    "Teste": "Pseudo-R² de McFadden",
                    "Resultado": (
                        f"{pseudo_r2_mcfadden:.4f}" if pd.notna(pseudo_r2_mcfadden) else "NA"
                    ),
                    "Critério": (
                        "Quanto maior, maior a melhora em relação "
                        "ao modelo sem variáveis explicativas"
                    ),
                    "Situação": "Informativo",
                    "Obrigatório": "Não",
                }
            )

        # ----------------------------------------------------
        # Resíduos quantílicos — complementar
        # ----------------------------------------------------

        if familia in {"Gamma", "Gaussiano Inverso", "Poisson", "Binomial"}:

            rqr = _residuos_quantilicos_glm(modelo, familia, y_arr)

            shapiro_q_p = _shapiro_amostra(rqr)

            linhas.append(
                {
                    "Teste": "Resíduos quantílicos (Shapiro)",
                    "Resultado": (f"p = {shapiro_q_p:.4f}" if pd.notna(shapiro_q_p) else "NA"),
                    "Critério": ("p > 0,05 é desejável; " "uso complementar nos MLGs"),
                    "Situação": (
                        "Informativo"
                        if pd.isna(shapiro_q_p)
                        else ("Atendido" if shapiro_q_p > 0.05 else "Atenção")
                    ),
                    "Obrigatório": "Não",
                }
            )

        tabela = pd.DataFrame(linhas)

        obrigatorios_ok = bool(
            (tabela.loc[tabela["Obrigatório"].eq("Sim"), "Situação"].eq("Atendido")).all()
        )

        return {
            "valido": obrigatorios_ok,
            "residuos_ok": (residuos_finitos and extremos_ok and padrao_ok),
            "dispersao": dispersao,
            "pseudo_r2_mcfadden": (
                pseudo_r2_mcfadden
                if familia == "Binomial" and "pseudo_r2_mcfadden" in locals()
                else np.nan
            ),
            "tabela_diagnostico": tabela,
            "motivos": motivos,
            "mensagem": (
                "Diagnóstico adequado."
                if obrigatorios_ok
                else ("Diagnóstico não atendido: " + "; ".join(motivos))
            ),
        }

    def diagnostico_binomial_negativa(modelo, y):
        """
        Diagnóstico específico da Binomial Negativa.

        Verifica:
        - contagem inteira e não negativa;
        - convergência;
        - alpha > 0;
        - dispersão Pearson;
        - resíduos Pearson extremos;
        - padrão resíduos x ajustados;
        - resíduos quantílicos como diagnóstico complementar.
        """

        linhas = []
        motivos = []

        y_arr = np.asarray(y, dtype=float)

        fitted = np.asarray(modelo.predict(), dtype=float)

        resposta_ok = bool(np.all(y_arr >= 0) and np.allclose(y_arr, np.round(y_arr)))

        linhas.append(
            {
                "Teste": "Estrutura da resposta",
                "Resultado": "Adequada" if resposta_ok else "Inadequada",
                "Critério": "Contagem inteira e não negativa",
                "Situação": _status_diagnostico(resposta_ok),
                "Obrigatório": "Sim",
            }
        )

        if not resposta_ok:
            motivos.append("a resposta não é uma contagem inteira não negativa")

        convergiu = bool(getattr(modelo, "mle_retvals", {}).get("converged", True))

        linhas.append(
            {
                "Teste": "Convergência",
                "Resultado": "Sim" if convergiu else "Não",
                "Critério": "O ajuste deve convergir",
                "Situação": _status_diagnostico(convergiu),
                "Obrigatório": "Sim",
            }
        )

        if not convergiu:
            motivos.append("o algoritmo da Binomial Negativa não convergiu")

        alpha = np.nan

        try:
            alpha = float(modelo.params["alpha"])
        except Exception:
            pass

        alpha_ok = bool(pd.notna(alpha) and np.isfinite(alpha) and alpha > 0)

        linhas.append(
            {
                "Teste": "Parâmetro alpha",
                "Resultado": (f"{alpha:.4f}" if pd.notna(alpha) else "NA"),
                "Critério": "alpha > 0",
                "Situação": _status_diagnostico(alpha_ok),
                "Obrigatório": "Sim",
            }
        )

        if not alpha_ok:
            motivos.append("o parâmetro de dispersão alpha não é positivo")

        try:

            pearson = np.asarray(modelo.resid_pearson, dtype=float)

        except Exception:

            pearson = np.array([])

        residuos_finitos = bool(pearson.size > 0 and np.isfinite(pearson).all())

        linhas.append(
            {
                "Teste": "Resíduos Pearson finitos",
                "Resultado": "Sim" if residuos_finitos else "Não",
                "Critério": "Todos os resíduos devem ser finitos",
                "Situação": _status_diagnostico(residuos_finitos),
                "Obrigatório": "Sim",
            }
        )

        if not residuos_finitos:
            motivos.append("foram encontrados resíduos Pearson não finitos")

        if pearson.size and getattr(modelo, "df_resid", 0) > 0:

            dispersao = float(np.sum(pearson**2) / modelo.df_resid)

        else:

            dispersao = np.nan

        dispersao_ok = bool(pd.notna(dispersao) and 0.7 <= dispersao <= 1.5)

        linhas.append(
            {
                "Teste": "Dispersão Pearson",
                "Resultado": (f"{dispersao:.3f}" if pd.notna(dispersao) else "NA"),
                "Critério": "0,70 ≤ dispersão ≤ 1,50",
                "Situação": _status_diagnostico(dispersao_ok),
                "Obrigatório": "Sim",
            }
        )

        if not dispersao_ok:
            motivos.append(
                "a dispersão residual da Binomial Negativa ficou fora do intervalo operacional"
            )

        if pearson.size:

            prop_extremos = float(np.mean(np.abs(pearson) > 3) * 100)

            extremos_ok = prop_extremos <= 5.0

        else:

            prop_extremos = np.nan
            extremos_ok = False

        linhas.append(
            {
                "Teste": "Resíduos Pearson extremos",
                "Resultado": (f"{prop_extremos:.2f}%" if pd.notna(prop_extremos) else "NA"),
                "Critério": "Até 5% com |resíduo| > 3",
                "Situação": _status_diagnostico(extremos_ok),
                "Obrigatório": "Sim",
            }
        )

        if not extremos_ok:
            motivos.append("há proporção elevada de resíduos Pearson extremos")

        rho = np.nan

        if pearson.size and len(pearson) == len(fitted):

            mascara = np.isfinite(pearson) & np.isfinite(fitted)

            if mascara.sum() >= 8 and np.nanstd(fitted[mascara]) > 0:

                try:

                    rho = float(stats.spearmanr(fitted[mascara], pearson[mascara]).statistic)

                except Exception:
                    rho = np.nan

        padrao_ok = bool(pd.notna(rho) and abs(rho) <= 0.20)

        linhas.append(
            {
                "Teste": "Padrão resíduos × ajustados",
                "Resultado": (f"|rho| = {abs(rho):.3f}" if pd.notna(rho) else "NA"),
                "Critério": "|rho de Spearman| ≤ 0,20",
                "Situação": _status_diagnostico(padrao_ok),
                "Obrigatório": "Sim",
            }
        )

        if not padrao_ok:
            motivos.append(
                "os resíduos apresentam padrão relevante em relação aos valores ajustados"
            )

        rqr = _residuos_quantilicos_nb(modelo, y_arr)

        shapiro_q_p = _shapiro_amostra(rqr)

        linhas.append(
            {
                "Teste": "Resíduos quantílicos (Shapiro)",
                "Resultado": (f"p = {shapiro_q_p:.4f}" if pd.notna(shapiro_q_p) else "NA"),
                "Critério": ("p > 0,05 é desejável; " "uso complementar"),
                "Situação": (
                    "Informativo"
                    if pd.isna(shapiro_q_p)
                    else ("Atendido" if shapiro_q_p > 0.05 else "Atenção")
                ),
                "Obrigatório": "Não",
            }
        )

        tabela = pd.DataFrame(linhas)

        obrigatorios_ok = bool(
            (tabela.loc[tabela["Obrigatório"].eq("Sim"), "Situação"].eq("Atendido")).all()
        )

        return {
            "valido": obrigatorios_ok,
            "residuos_ok": (residuos_finitos and dispersao_ok and extremos_ok and padrao_ok),
            "alpha": alpha,
            "dispersao": dispersao,
            "tabela_diagnostico": tabela,
            "motivos": motivos,
            "mensagem": (
                "Diagnóstico adequado."
                if obrigatorios_ok
                else ("Diagnóstico não atendido: " + "; ".join(motivos))
            ),
        }

    def pressupostos_gaussiano(modelo, X):
        """
        Diagnóstico do modelo Gaussiano:
        - normalidade dos resíduos;
        - homocedasticidade;
        - independência aproximada.
        """

        try:

            residuos = np.asarray(modelo.resid_response, dtype=float)

            residuos = residuos[np.isfinite(residuos)]

            if len(residuos) < 8:

                tabela = pd.DataFrame(
                    [
                        {
                            "Teste": "Tamanho para diagnóstico",
                            "Resultado": len(residuos),
                            "Critério": "Pelo menos 8 resíduos",
                            "Situação": "Não atendido",
                            "Obrigatório": "Sim",
                        }
                    ]
                )

                return {
                    "valido": False,
                    "residuos_ok": False,
                    "shapiro_p": np.nan,
                    "bp_p": np.nan,
                    "dw": np.nan,
                    "tabela_diagnostico": tabela,
                    "motivos": ["há poucos resíduos para validar o modelo Gaussiano"],
                    "mensagem": ("Poucos resíduos para validar " "o modelo Gaussiano."),
                }

            shapiro_p = float(
                stats.shapiro(
                    (
                        residuos
                        if len(residuos) <= 5000
                        else np.random.default_rng(20260816).choice(
                            residuos, size=5000, replace=False
                        )
                    )
                ).pvalue
            )

            bp = het_breuschpagan(residuos, np.asarray(X, dtype=float))

            bp_p = float(bp[1])

            dw = float(durbin_watson(residuos))

            normalidade = shapiro_p > 0.05

            homocedasticidade = bp_p > 0.05

            independencia = 1.5 <= dw <= 2.5

            valido = normalidade and homocedasticidade and independencia

            tabela = pd.DataFrame(
                [
                    {
                        "Teste": "Shapiro-Wilk",
                        "Resultado": f"p = {shapiro_p:.4f}",
                        "Critério": "p > 0,05",
                        "Situação": _status_diagnostico(normalidade),
                        "Obrigatório": "Sim",
                    },
                    {
                        "Teste": "Breusch-Pagan",
                        "Resultado": f"p = {bp_p:.4f}",
                        "Critério": "p > 0,05",
                        "Situação": _status_diagnostico(homocedasticidade),
                        "Obrigatório": "Sim",
                    },
                    {
                        "Teste": "Durbin-Watson",
                        "Resultado": f"{dw:.3f}",
                        "Critério": "1,5 ≤ DW ≤ 2,5",
                        "Situação": _status_diagnostico(independencia),
                        "Obrigatório": "Sim",
                    },
                ]
            )

            motivos = []

            if not normalidade:
                motivos.append("os resíduos não atenderam à normalidade pelo Shapiro-Wilk")

            if not homocedasticidade:
                motivos.append("a variância dos resíduos não foi constante pelo Breusch-Pagan")

            if not independencia:
                motivos.append("o Durbin-Watson indicou possível dependência residual")

            return {
                "valido": valido,
                "residuos_ok": valido,
                "shapiro_p": shapiro_p,
                "bp_p": bp_p,
                "dw": dw,
                "tabela_diagnostico": tabela,
                "motivos": motivos,
                "mensagem": (
                    "Pressupostos atendidos."
                    if valido
                    else ("Pressupostos não atendidos: " + "; ".join(motivos))
                ),
            }

        except Exception as erro:

            tabela = pd.DataFrame(
                [
                    {
                        "Teste": "Diagnóstico Gaussiano",
                        "Resultado": "Falha",
                        "Critério": "Diagnóstico deve ser calculável",
                        "Situação": "Não atendido",
                        "Obrigatório": "Sim",
                    }
                ]
            )

            return {
                "valido": False,
                "residuos_ok": False,
                "shapiro_p": np.nan,
                "bp_p": np.nan,
                "dw": np.nan,
                "tabela_diagnostico": tabela,
                "motivos": [str(erro)],
                "mensagem": (f"Não foi possível validar: {erro}"),
            }

    def construir_base_mensal(base):
        """
        Base mensal usada apenas para:
        - Receita do mês seguinte
        - Pedidos do mês seguinte
        """

        dados = base[base["order_purchase_timestamp"].notna()].copy()

        if dados.empty:
            return pd.DataFrame()

        dados["mes"] = dados["order_purchase_timestamp"].dt.to_period("M")

        dados["sent_negativo"] = (dados["sentimento_texto"].eq("Negativo")).astype(float)

        dados["sent_positivo"] = (dados["sentimento_texto"].eq("Positivo")).astype(float)

        dados["tem_sentimento"] = (dados["sentimento_texto"].notna()).astype(float)

        dados["reclamacao_classificada"] = (dados["categoria_reclamacao"].notna()).astype(float)

        termos_entrega = {"Atraso ou entrega", "Entrega", "Produto não recebido"}

        dados["reclamacao_entrega"] = (dados["categoria_reclamacao"].isin(termos_entrega)).astype(
            float
        )

        mensal = (
            dados.groupby("mes")
            .agg(
                receita=("payment_value", "sum"),
                pedidos=("order_id", "nunique"),
                ticket_medio=("payment_value", "mean"),
                nota_media=("review_score", "mean"),
                taxa_atraso=("atrasou", lambda s: s.mean() * 100),
                prazo_medio=("prazo_entrega_dias", "mean"),
                entrega_media=("dias_entrega", "mean"),
                distancia_logistica_media=("distancia_origem_cliente_media_km", "mean"),
                distancia_capital_media=("distancia_capital_km", "mean"),
                parcelas_media=("payment_installments", "mean"),
                total_sentimentos=("tem_sentimento", "sum"),
                negativos=("sent_negativo", "sum"),
                positivos=("sent_positivo", "sum"),
                reclamacoes=("reclamacao_classificada", "sum"),
                reclamacoes_entrega=("reclamacao_entrega", "sum"),
            )
            .reset_index()
            .sort_values("mes")
        )

        mensal["pct_negativos"] = np.where(
            mensal["total_sentimentos"] > 0,
            (mensal["negativos"] / mensal["total_sentimentos"] * 100),
            np.nan,
        )

        mensal["pct_positivos"] = np.where(
            mensal["total_sentimentos"] > 0,
            (mensal["positivos"] / mensal["total_sentimentos"] * 100),
            np.nan,
        )

        mensal["pct_reclamacoes"] = np.where(
            mensal["total_sentimentos"] > 0,
            (mensal["reclamacoes"] / mensal["total_sentimentos"] * 100),
            np.nan,
        )

        mensal["pct_reclamacoes_entrega"] = np.where(
            mensal["reclamacoes"] > 0,
            (mensal["reclamacoes_entrega"] / mensal["reclamacoes"] * 100),
            np.nan,
        )

        # Variáveis respostas futuras.
        mensal["receita_proximo_mes"] = mensal["receita"].shift(-1)

        mensal["pedidos_proximo_mes"] = mensal["pedidos"].shift(-1)

        # Tendência temporal = 0, 1, 2, ...
        mensal["tendencia"] = np.arange(len(mensal), dtype=float)

        mensal["distancia_logistica_media_100"] = mensal["distancia_logistica_media"] / 100.0

        mensal["distancia_capital_media_100"] = mensal["distancia_capital_media"] / 100.0

        mensal["mes_texto"] = mensal["mes"].astype(str)

        return mensal

    def agrupar_categorias_raras(
        serie, max_niveis=8, min_proporcao=0.02, min_frequencia=20, rotulo_outros="Outras"
    ):
        """
        Agrupa categorias pouco frequentes para evitar modelos com
        muitos parâmetros e estimativas instáveis.

        Mantém no máximo max_niveis categorias, contando "Outras".
        """

        s = serie.fillna("Não informado").astype(str).str.strip().replace("", "Não informado")

        contagens = s.value_counts(dropna=False)

        if contagens.empty:
            return s

        limite = max(min_frequencia, int(np.ceil(len(s) * min_proporcao)))

        elegiveis = contagens[contagens >= limite].index.tolist()

        # Sempre preserva pelo menos a categoria mais frequente.
        if not elegiveis:
            elegiveis = [contagens.index[0]]

        # Reserva um nível para "Outras".
        elegiveis = elegiveis[: max(1, max_niveis - 1)]

        agrupada = s.where(s.isin(elegiveis), rotulo_outros)

        return agrupada

    def construir_tabelas_ajuste_categorias(
        base,
        categoricas_selecionadas,
        nomes_categoricos,
        referencias_categoricas=None,
        x_cols_finais=None,
    ):
        """
        Cria tabelas para explicar, no dashboard, como cada variável
        categórica estava originalmente e como ficou após o agrupamento.

        Exibe:
        - categoria original;
        - categoria usada no modelo;
        - quantidade e percentual;
        - se foi mantida ou agrupada;
        - categoria de referência;
        - se o bloco categórico permaneceu no modelo final.
        """

        referencias_categoricas = referencias_categoricas or {}

        x_cols_finais = list(x_cols_finais) if x_cols_finais is not None else []

        # Coluna ajustada -> coluna original.
        mapa_origem = {
            "categoria_produto_modelo": "categoria_produto_pedido",
            "forma_pagamento_modelo": "payment_type",
            "regiao_modelo": "regiao",
            "estado_modelo": "customer_state",
        }

        detalhes = []
        resumos = []

        for col_ajustada in categoricas_selecionadas:

            if col_ajustada not in base.columns:
                continue

            col_original = mapa_origem.get(col_ajustada, col_ajustada)

            if col_original not in base.columns:
                continue

            nome_amigavel = nomes_categoricos.get(col_ajustada, col_ajustada)

            temp = base[[col_original, col_ajustada]].copy()

            temp[col_original] = (
                temp[col_original]
                .fillna("Não informado")
                .astype(str)
                .str.strip()
                .replace("", "Não informado")
            )

            temp[col_ajustada] = (
                temp[col_ajustada]
                .fillna("Não informado")
                .astype(str)
                .str.strip()
                .replace("", "Não informado")
            )

            total = len(temp)

            if total == 0:
                continue

            tabela = (
                temp.groupby([col_original, col_ajustada], as_index=False)
                .size()
                .rename(columns={"size": "Quantidade"})
            )

            tabela["Percentual (%)"] = tabela["Quantidade"] / total * 100

            if col_ajustada == "regiao_modelo":

                tabela["Situação"] = "Preservada sem agrupamento"

            elif col_ajustada == "estado_modelo":

                tabela["Situação"] = np.where(
                    tabela[col_original].eq(tabela[col_ajustada]),
                    "Mantida",
                    "Agrupada por baixa frequência",
                )

            else:

                tabela["Situação"] = np.where(
                    tabela[col_original].eq(tabela[col_ajustada]), "Mantida", "Agrupada"
                )

            referencia = referencias_categoricas.get(nome_amigavel, "—")

            prefixo = col_ajustada + "__"

            permaneceu_final = any(col.startswith(prefixo) for col in x_cols_finais)

            # Se só havia 2 níveis, uma dummy pode existir; se a
            # categórica ficou constante no filtro, não entra no modelo.
            if col_ajustada in x_cols_finais:
                permaneceu_final = True

            tabela["Variável"] = nome_amigavel

            tabela["Categoria de referência"] = referencia

            tabela["No modelo final"] = "Sim" if permaneceu_final else "Não"

            tabela = tabela.rename(
                columns={col_original: "Categoria original", col_ajustada: "Categoria após ajuste"}
            )

            detalhes.append(
                tabela[
                    [
                        "Variável",
                        "Categoria original",
                        "Categoria após ajuste",
                        "Situação",
                        "Quantidade",
                        "Percentual (%)",
                        "Categoria de referência",
                        "No modelo final",
                    ]
                ]
            )

            n_original = temp[col_original].nunique()

            n_ajustado = temp[col_ajustada].nunique()

            qtd_agrupadas = tabela.loc[
                tabela["Situação"].isin(["Agrupada", "Agrupada por baixa frequência"]),
                "Categoria original",
            ].nunique()

            if col_ajustada == "regiao_modelo":

                politica = "Sem agrupamento: regiões preservadas"

            elif col_ajustada == "estado_modelo":

                politica = "Agrupamento adaptativo apenas para UFs raras"

            else:

                politica = "Categorias raras podem ser reunidas"

            resumos.append(
                {
                    "Variável": nome_amigavel,
                    "Categorias antes": int(n_original),
                    "Categorias depois": int(n_ajustado),
                    "Categorias agrupadas": int(qtd_agrupadas),
                    "Tratamento": politica,
                    "Referência": referencia,
                    "No modelo final": ("Sim" if permaneceu_final else "Não"),
                }
            )

        tabela_detalhes = pd.concat(detalhes, ignore_index=True) if detalhes else pd.DataFrame()

        tabela_resumo = pd.DataFrame(resumos)

        return (tabela_resumo, tabela_detalhes)

    def preparar_matriz_modelo(
        base, y_col, numericas, categoricas, nomes_numericos, nomes_categoricos, coluna_tempo=None
    ):
        """
        Prepara a matriz da regressão:
        - mantém variáveis numéricas;
        - transforma categóricas em dummies;
        - usa como referência a categoria mais frequente;
        - devolve nomes amigáveis para interpretação.
        """

        colunas = [y_col] + numericas + categoricas

        if coluna_tempo is not None and coluna_tempo in base.columns:
            colunas = [coluna_tempo] + colunas

        colunas = list(dict.fromkeys(colunas))

        dados = base[colunas].copy()

        for col in categoricas:
            dados[col] = dados[col].fillna("Não informado").astype(str)

        # Não imputamos quantitativas: o modelo usa apenas casos
        # completos nas variáveis numéricas selecionadas.
        dados = dados.dropna(subset=[y_col] + numericas)

        nomes_amigaveis = {col: nomes_numericos.get(col, col) for col in numericas}

        referencias = {}

        x_cols = list(numericas)

        for col in categoricas:

            frequencias = dados[col].value_counts()

            if len(frequencias) <= 1:
                continue

            # Categoria mais frequente = referência.
            ordem = frequencias.index.tolist()

            referencia = ordem[0]

            dados[col] = pd.Categorical(dados[col], categories=ordem)

            dummies = pd.get_dummies(
                dados[col], prefix=col, prefix_sep="__", drop_first=True, dtype=float
            )

            referencias[nomes_categoricos.get(col, col)] = referencia

            for dummy in dummies.columns:

                nivel = dummy.split("__", 1)[1]

                nome_base = nomes_categoricos.get(col, col)

                nomes_amigaveis[dummy] = f"{nome_base}: {nivel} " f"(ref.: {referencia})"

            dados = pd.concat([dados, dummies], axis=1)

            x_cols.extend(dummies.columns.tolist())

        return (dados, x_cols, nomes_amigaveis, referencias)

    def construir_base_pedido(base):
        """
        Base em nível de pedido usada para:
        - Tempo de entrega
        - Pedido atrasado
        - Avaliação ruim
        """

        dados = base.copy()

        dados["pedido_atrasado"] = dados["atrasou"].astype(int)

        dados["avaliacao_ruim"] = np.where(
            dados["review_score"].notna(), (dados["review_score"] <= 2).astype(int), np.nan
        )

        dados["dias_atraso_positivo"] = dados["dias_atraso"].clip(lower=0)

        # Escalas mais interpretáveis e numericamente estáveis.
        dados["valor_pedido_100"] = dados["payment_value"] / 100.0

        dados["frete_10"] = (
            dados["frete_total"] / 10.0 if "frete_total" in dados.columns else np.nan
        )

        dados["distancia_logistica_100"] = dados["distancia_origem_cliente_media_km"] / 100.0

        dados["distancia_capital_100"] = dados["distancia_capital_km"] / 100.0

        # ----------------------------------------------------
        # Variáveis comerciais adicionais
        # ----------------------------------------------------

        dados["valor_itens_100"] = (
            dados["valor_itens"] / 100.0 if "valor_itens" in dados.columns else np.nan
        )

        dados["preco_medio_item_100"] = np.where(
            dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index)) > 0,
            (
                dados.get("valor_itens", pd.Series(np.nan, index=dados.index))
                / dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index))
                / 100.0
            ),
            np.nan,
        )

        dados["frete_por_item_10"] = np.where(
            dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index)) > 0,
            (
                dados.get("frete_total", pd.Series(np.nan, index=dados.index))
                / dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index))
                / 10.0
            ),
            np.nan,
        )

        dados["frete_percentual"] = np.where(
            dados.get("valor_itens", pd.Series(np.nan, index=dados.index)) > 0,
            (
                dados.get("frete_total", pd.Series(np.nan, index=dados.index))
                / dados.get("valor_itens", pd.Series(np.nan, index=dados.index))
                * 100.0
            ),
            np.nan,
        )

        dados["peso_medio_item_kg"] = np.where(
            dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index)) > 0,
            (
                dados.get("peso_total_kg", pd.Series(np.nan, index=dados.index))
                / dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index))
            ),
            np.nan,
        )

        dados["volume_medio_item_litros"] = np.where(
            dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index)) > 0,
            (
                dados.get("volume_total_litros", pd.Series(np.nan, index=dados.index))
                / dados.get("quantidade_itens", pd.Series(np.nan, index=dados.index))
            ),
            np.nan,
        )

        # ----------------------------------------------------
        # Variáveis temporais da compra
        # ----------------------------------------------------

        if "order_purchase_timestamp" in dados.columns:

            data_compra = pd.to_datetime(dados["order_purchase_timestamp"], errors="coerce")

            mapa_mes = {
                1: "Jan",
                2: "Fev",
                3: "Mar",
                4: "Abr",
                5: "Mai",
                6: "Jun",
                7: "Jul",
                8: "Ago",
                9: "Set",
                10: "Out",
                11: "Nov",
                12: "Dez",
            }

            mapa_dia = {
                0: "Segunda",
                1: "Terça",
                2: "Quarta",
                3: "Quinta",
                4: "Sexta",
                5: "Sábado",
                6: "Domingo",
            }

            dados["mes_compra_modelo"] = data_compra.dt.month.map(mapa_mes).fillna("Não informado")

            dados["dia_semana_modelo"] = data_compra.dt.dayofweek.map(mapa_dia).fillna(
                "Não informado"
            )

            dados["ano_compra_modelo"] = (
                data_compra.dt.year.astype("Int64").astype(str).replace("<NA>", "Não informado")
            )

            hora = data_compra.dt.hour

            dados["periodo_compra_modelo"] = pd.cut(
                hora, bins=[-1, 5, 11, 17, 23], labels=["Madrugada", "Manhã", "Tarde", "Noite"]
            ).astype("object")

            dados["periodo_compra_modelo"] = (
                dados["periodo_compra_modelo"].fillna("Não informado").astype(str)
            )

        else:

            dados["mes_compra_modelo"] = "Não informado"

            dados["dia_semana_modelo"] = "Não informado"

            dados["ano_compra_modelo"] = "Não informado"

            dados["periodo_compra_modelo"] = "Não informado"

        # Forma de pagamento tem poucos níveis; apenas os níveis
        # extremamente raros são reunidos.
        dados["forma_pagamento_modelo"] = agrupar_categorias_raras(
            dados["payment_type"],
            max_niveis=5,
            min_proporcao=0.005,
            min_frequencia=20,
            rotulo_outros="Outros",
        )

        # A Olist possui muitas categorias de produto.
        # Para a regressão mantemos as mais representativas do
        # filtro atual e agrupamos o restante em "Outras".
        if "categoria_produto_pedido" in dados.columns:

            dados["categoria_produto_modelo"] = agrupar_categorias_raras(
                dados["categoria_produto_pedido"],
                max_niveis=8,
                min_proporcao=0.02,
                min_frequencia=20,
                rotulo_outros="Outras",
            )

        else:

            dados["categoria_produto_modelo"] = "Não informado"

        # Região possui apenas cinco níveis e é preservada.
        dados["regiao_modelo"] = (
            dados["regiao"]
            .fillna("Não informado")
            .astype(str)
            .str.strip()
            .replace("", "Não informado")
        )

        # Estado recebe agrupamento ADAPTATIVO.
        #
        # Se todos os estados do filtro tiverem frequência suficiente,
        # cada UF é preservada. UFs muito raras podem ser reunidas em
        # "Outros estados" para reduzir instabilidade nas estimativas.
        estado_limpo = (
            dados["customer_state"]
            .fillna("Não informado")
            .astype(str)
            .str.strip()
            .replace("", "Não informado")
        )

        contagem_estado = estado_limpo.value_counts()

        limite_estado = max(30, int(np.ceil(len(estado_limpo) * 0.01)))

        estados_frequentes = contagem_estado[contagem_estado >= limite_estado].index.tolist()

        if estado_limpo.nunique() <= 12 or len(estados_frequentes) == estado_limpo.nunique():
            dados["estado_modelo"] = estado_limpo
        else:
            dados["estado_modelo"] = estado_limpo.where(
                estado_limpo.isin(estados_frequentes), "Outros estados"
            )

        return dados

    def ajustar_modelos_continuos(dados_modelo, y_col, x_cols):
        """
        Modelos candidatos para respostas contínuas:
        - Gaussiano
        - Gamma com link log
        - Gaussiano Inverso com link log

        Somente modelos que atendem aos diagnósticos obrigatórios
        entram na comparação por AICc.
        """

        X = dados_modelo[x_cols].astype(float)

        X = sm.add_constant(X, has_constant="add")

        y = dados_modelo[y_col].astype(float)

        resultados = []
        modelos = {}
        diagnosticos = {}
        falhas = []

        # ----------------------------------------------------
        # 1. GAUSSIANO
        # ----------------------------------------------------

        try:

            modelo_g = sm.GLM(y, X, family=(sm.families.Gaussian())).fit()

            diag_g = pressupostos_gaussiano(modelo_g, X)

            diagnosticos["Gaussiano"] = diag_g

            if diag_g["valido"]:

                k = len(modelo_g.params)

                aic = float(modelo_g.aic)

                resultados.append(
                    {
                        "Modelo": "Gaussiano",
                        "AIC": aic,
                        "AICc": calcular_aicc(aic, len(y), k),
                        "BIC": (-2 * modelo_g.llf + np.log(len(y)) * k),
                    }
                )

                modelos["Gaussiano"] = modelo_g

            else:

                falhas.append("Gaussiano: " + diag_g["mensagem"])

        except Exception as erro:

            falhas.append(f"Gaussiano: falha no ajuste ({erro})")

        # ----------------------------------------------------
        # 2. GAMMA
        # ----------------------------------------------------

        if (y > 0).all():

            try:

                modelo_gamma = sm.GLM(
                    y, X, family=(sm.families.Gamma(link=(sm.families.links.Log())))
                ).fit()

                diag_gamma = diagnostico_glm(modelo_gamma, y, "Gamma", X)

                diagnosticos["Gamma (link log)"] = diag_gamma

                if diag_gamma["valido"]:

                    k = len(modelo_gamma.params)

                    aic = float(modelo_gamma.aic)

                    resultados.append(
                        {
                            "Modelo": "Gamma (link log)",
                            "AIC": aic,
                            "AICc": calcular_aicc(aic, len(y), k),
                            "BIC": (-2 * modelo_gamma.llf + np.log(len(y)) * k),
                        }
                    )

                    modelos["Gamma (link log)"] = modelo_gamma

                else:

                    falhas.append("Gamma: " + diag_gamma["mensagem"])

            except Exception as erro:

                falhas.append(f"Gamma: falha no ajuste ({erro})")

            # ------------------------------------------------
            # 3. GAUSSIANO INVERSO
            # ------------------------------------------------

            try:

                modelo_ig = sm.GLM(
                    y, X, family=(sm.families.InverseGaussian(link=(sm.families.links.Log())))
                ).fit()

                diag_ig = diagnostico_glm(modelo_ig, y, "Gaussiano Inverso", X)

                nome_ig = "Gaussiano Inverso " "(link log)"

                diagnosticos[nome_ig] = diag_ig

                if diag_ig["valido"]:

                    k = len(modelo_ig.params)

                    aic = float(modelo_ig.aic)

                    resultados.append(
                        {
                            "Modelo": nome_ig,
                            "AIC": aic,
                            "AICc": calcular_aicc(aic, len(y), k),
                            "BIC": (-2 * modelo_ig.llf + np.log(len(y)) * k),
                        }
                    )

                    modelos[nome_ig] = modelo_ig

                else:

                    falhas.append("Gaussiano Inverso: " + diag_ig["mensagem"])

            except Exception as erro:

                falhas.append(("Gaussiano Inverso: " f"falha no ajuste ({erro})"))

        else:

            falhas.append(
                ("Gamma e Gaussiano Inverso: " "a resposta contém zero ou valor negativo.")
            )

        tabela = organizar_comparacao(resultados)

        if tabela.empty:

            diagnosticos["erro"] = "Nenhum modelo contínuo atendeu aos critérios. " + " | ".join(
                falhas
            )

        diagnosticos["falhas_candidatos"] = falhas

        return (tabela, modelos, diagnosticos)

    def ajustar_modelos_contagem(dados_modelo, y_col, x_cols):
        """
        Modelos candidatos para contagens:
        - Poisson
        - Binomial Negativa

        Cada modelo passa pelo diagnóstico de resíduos antes de
        entrar na comparação por AICc.
        """

        X = dados_modelo[x_cols].astype(float)

        X = sm.add_constant(X, has_constant="add")

        y = dados_modelo[y_col].astype(float)

        resultados = []
        modelos = {}
        diagnosticos = {}
        falhas = []

        resposta_contagem_ok = bool(np.all(y >= 0) and np.allclose(y, np.round(y)))

        if not resposta_contagem_ok:

            return (
                pd.DataFrame(),
                {},
                {"erro": ("A resposta de contagem contém valores " "negativos ou não inteiros.")},
            )

        # ----------------------------------------------------
        # POISSON
        # ----------------------------------------------------

        try:

            modelo_p = sm.GLM(y, X, family=(sm.families.Poisson())).fit()

            diag_p = diagnostico_glm(modelo_p, y, "Poisson", X)

            diagnosticos["Poisson"] = diag_p

            if diag_p["valido"]:

                k = len(modelo_p.params)

                aic = float(modelo_p.aic)

                resultados.append(
                    {
                        "Modelo": "Poisson",
                        "AIC": aic,
                        "AICc": calcular_aicc(aic, len(y), k),
                        "BIC": (-2 * modelo_p.llf + np.log(len(y)) * k),
                    }
                )

                modelos["Poisson"] = modelo_p

            else:

                falhas.append("Poisson: " + diag_p["mensagem"])

        except Exception as erro:

            falhas.append(f"Poisson: falha no ajuste ({erro})")

        # ----------------------------------------------------
        # BINOMIAL NEGATIVA
        # ----------------------------------------------------

        try:

            modelo_nb = sm.NegativeBinomial(y, X).fit(disp=False, maxiter=300)

            diag_nb = diagnostico_binomial_negativa(modelo_nb, y)

            diagnosticos["Binomial Negativa"] = diag_nb

            if diag_nb["valido"]:

                k = len(modelo_nb.params)

                aic = float(modelo_nb.aic)

                resultados.append(
                    {
                        "Modelo": "Binomial Negativa",
                        "AIC": aic,
                        "AICc": calcular_aicc(aic, len(y), k),
                        "BIC": float(modelo_nb.bic),
                    }
                )

                modelos["Binomial Negativa"] = modelo_nb

            else:

                falhas.append("Binomial Negativa: " + diag_nb["mensagem"])

        except Exception as erro:

            falhas.append(("Binomial Negativa: " f"falha no ajuste ({erro})"))

        tabela = organizar_comparacao(resultados)

        if tabela.empty:

            diagnosticos["erro"] = "Nenhum modelo de contagem atendeu aos critérios. " + " | ".join(
                falhas
            )

        diagnosticos["falhas_candidatos"] = falhas

        return (tabela, modelos, diagnosticos)

    def ajustar_logistico(dados_modelo, y_col, x_cols):
        """
        Regressão Logística Binomial para resposta 0/1.

        O modelo somente entra como válido se atender aos
        critérios obrigatórios do diagnóstico.
        """

        X = dados_modelo[x_cols].astype(float)

        X = sm.add_constant(X, has_constant="add")

        y = dados_modelo[y_col].astype(int)

        resultados = []
        modelos = {}
        diagnosticos = {}

        if y.nunique() != 2:

            return (
                pd.DataFrame(),
                {},
                {"erro": ("A resposta precisa possuir " "as duas categorias 0 e 1.")},
            )

        try:

            modelo = sm.GLM(
                y, X, family=(sm.families.Binomial(link=(sm.families.links.Logit())))
            ).fit()

            parametros_finitos = bool(np.isfinite(modelo.params).all())

            if not parametros_finitos:

                return (
                    pd.DataFrame(),
                    {},
                    {"erro": ("O modelo logístico apresentou " "estimativas não finitas.")},
                )

            # ------------------------------------------------
            # Convergência / separação grave
            # ------------------------------------------------
            # Os resíduos NÃO são usados para decidir quais variáveis
            # permanecem. Antes do diagnóstico residual, verificamos
            # somente problemas que podem invalidar estruturalmente
            # a estimação logística.
            convergiu = bool(getattr(modelo, "converged", True))

            coef_sem_const = modelo.params.drop(labels=["const"], errors="ignore")

            fitted_tmp = np.asarray(modelo.fittedvalues, dtype=float)

            coef_explosivo = bool(
                len(coef_sem_const) > 0
                and np.nanmax(np.abs(coef_sem_const.to_numpy(dtype=float))) > 25
            )

            probabilidades_extremas = bool(
                fitted_tmp.size > 0
                and (np.mean((fitted_tmp < 1e-8) | (fitted_tmp > 1 - 1e-8)) > 0.98)
            )

            separacao_grave = bool(coef_explosivo and probabilidades_extremas)

            if not convergiu or separacao_grave:
                motivo_estrutural = (
                    "o algoritmo não convergiu"
                    if not convergiu
                    else (
                        "há evidência de separação quase/perfeita "
                        "ou instabilidade extrema dos coeficientes"
                    )
                )

                return (
                    pd.DataFrame(),
                    {},
                    {
                        "erro": (
                            "O ajuste logístico não pôde ser aceito porque "
                            + motivo_estrutural
                            + "."
                        )
                    },
                )

            # ------------------------------------------------
            # Diagnóstico do ajuste
            # ------------------------------------------------
            # É calculado para ser exibido SOMENTE no modelo final.
            # Resíduos Pearson/deviance, Cook e Hosmer-Lemeshow não
            # eliminam automaticamente variáveis explicativas.
            diag_log = diagnostico_glm(modelo, y, "Binomial", X)

            diag_log["eventos"] = int(y.sum())

            diag_log["nao_eventos"] = int((1 - y).sum())

            diagnosticos["Logístico Binomial"] = diag_log

            # A partir daqui a estimação estrutural é válida.
            # O diagnóstico residual será apresentado somente na
            # Etapa 6 e não é usado para excluir este modelo.
            if True:

                k = len(modelo.params)

                aic = float(modelo.aic)

                resultados.append(
                    {
                        "Modelo": "Logístico Binomial",
                        "AIC": aic,
                        "AICc": calcular_aicc(aic, len(y), k),
                        "BIC": (-2 * modelo.llf + np.log(len(y)) * k),
                    }
                )

                modelos["Logístico Binomial"] = modelo

        except Exception as erro:

            diagnosticos["erro"] = "Não foi possível estimar a regressão logística: " + str(erro)

        return (organizar_comparacao(resultados), modelos, diagnosticos)

    def preparar_grafico_residuos(modelo, nome_modelo):
        """
        Retorna valores ajustados e um resíduo apropriado para
        inspeção gráfica do modelo final.
        """

        try:

            if nome_modelo == "Binomial Negativa":

                ajustado = np.asarray(modelo.predict(), dtype=float)

                residuo = np.asarray(modelo.resid_pearson, dtype=float)

                nome_residuo = "Resíduo de Pearson"

            else:

                ajustado = np.asarray(modelo.fittedvalues, dtype=float)

                try:

                    residuo = np.asarray(modelo.resid_deviance, dtype=float)

                    nome_residuo = "Resíduo de deviance"

                except Exception:

                    residuo = np.asarray(modelo.resid_pearson, dtype=float)

                    nome_residuo = "Resíduo de Pearson"

            dados = pd.DataFrame({"Valor ajustado": ajustado, nome_residuo: residuo})

            dados = dados.replace([np.inf, -np.inf], np.nan).dropna()

            # Para evitar gráfico excessivamente pesado.
            if len(dados) > 5000:

                dados = dados.sample(n=5000, random_state=20260816)

            return (dados, nome_residuo)

        except Exception:

            return (pd.DataFrame(), "Resíduo")

    def organizar_comparacao(resultados):

        if not resultados:
            return pd.DataFrame()

        tabela = pd.DataFrame(resultados)

        if tabela["AICc"].notna().any():

            tabela = tabela.sort_values(["AICc", "AIC"], na_position="last").reset_index(drop=True)

            minimo = tabela["AICc"].dropna().min()

            tabela["Delta_AICc"] = tabela["AICc"] - minimo

        else:

            tabela = tabela.sort_values("AIC").reset_index(drop=True)

            tabela["Delta_AICc"] = np.nan

        return tabela

    def avaliar_significancia_por_variavel(
        modelo,
        x_cols_atuais,
        selecionadas_numericas,
        selecionadas_categoricas,
        nomes_numericos,
        nomes_categoricos,
        alpha=0.05,
    ):
        """
        Avalia significância no nível da VARIÁVEL original.

        - Numéricas: usa o p-valor do coeficiente.
        - Categóricas: testa conjuntamente todas as dummies do bloco
          por teste de Wald. Assim, uma variável categórica com vários
          níveis conta como UMA variável explicativa, não como várias.

        O intercepto e o parâmetro alpha da Binomial Negativa não entram.
        """

        resultados = []

        params_index = list(modelo.params.index)

        pvalues = modelo.pvalues

        # ----------------------------------------------------
        # VARIÁVEIS NUMÉRICAS
        # ----------------------------------------------------

        for col in selecionadas_numericas:

            if col not in x_cols_atuais:
                continue

            if col not in params_index:
                continue

            try:
                pvalor = float(pvalues[col])
            except Exception:
                pvalor = np.nan

            resultados.append(
                {
                    "Variável": nomes_numericos.get(col, col),
                    "Colunas": [col],
                    "Tipo": "Numérica",
                    "p-valor": pvalor,
                    "Significativa": bool(pd.notna(pvalor) and pvalor < alpha),
                }
            )

        # ----------------------------------------------------
        # VARIÁVEIS CATEGÓRICAS
        # ----------------------------------------------------

        for col_cat in selecionadas_categoricas:

            prefixo = col_cat + "__"

            cols_bloco = [
                col for col in x_cols_atuais if col.startswith(prefixo) and col in params_index
            ]

            if not cols_bloco:
                continue

            nome_cat = nomes_categoricos.get(col_cat, col_cat)

            # Se restou apenas uma dummy, o teste conjunto
            # coincide com o p-valor desse coeficiente.
            if len(cols_bloco) == 1:

                try:
                    pvalor = float(pvalues[cols_bloco[0]])
                except Exception:
                    pvalor = np.nan

            else:

                try:

                    # Teste de Wald conjunto:
                    # H0: todos os coeficientes do fator = 0.
                    R = np.zeros((len(cols_bloco), len(params_index)), dtype=float)

                    for i, col in enumerate(cols_bloco):

                        j = params_index.index(col)

                        R[i, j] = 1.0

                    teste = modelo.wald_test(R, scalar=True)

                    pvalor = float(np.asarray(teste.pvalue).squeeze())

                except Exception:

                    # Fallback conservador:
                    # considera o maior p-valor entre as dummies.
                    try:

                        pvalor = float(pd.Series([pvalues[col] for col in cols_bloco]).max())

                    except Exception:

                        pvalor = np.nan

            resultados.append(
                {
                    "Variável": nome_cat,
                    "Colunas": cols_bloco,
                    "Tipo": "Categórica",
                    "p-valor": pvalor,
                    "Significativa": bool(pd.notna(pvalor) and pvalor < alpha),
                }
            )

        return resultados

    def reajustar_modelos_apos_selecao(dados_modelo, y_col, x_cols, tipo_resposta):
        """
        Reajusta todos os modelos compatíveis com a resposta
        usando somente o conjunto atualizado de explicativas.
        """

        if tipo_resposta == "continua":

            return ajustar_modelos_continuos(dados_modelo, y_col, x_cols)

        if tipo_resposta == "contagem":

            return ajustar_modelos_contagem(dados_modelo, y_col, x_cols)

        return ajustar_logistico(dados_modelo, y_col, x_cols)

    def refinar_por_significancia(
        dados_modelo,
        y_col,
        x_cols_iniciais,
        tipo_resposta,
        tabela_modelos,
        modelos,
        diagnosticos,
        selecionadas_numericas,
        selecionadas_categoricas,
        nomes_numericos,
        nomes_categoricos,
        limite_nao_significativas=0.40,
        alpha=0.05,
        max_iter=30,
    ):
        """
        Refinamento backward, removendo UMA variável original por vez.

        Fluxo:
        1. identifica a variável menos significativa (maior p-valor);
        2. remove somente essa variável;
        3. se for categórica, remove todo o bloco de dummies;
        4. recalcula VIF;
        5. reajusta todos os modelos candidatos compatíveis;
        6. seleciona novamente o melhor modelo válido por AICc;
        7. recalcula significância;
        8. repete até que no máximo 40% das variáveis originais
           sejam não significativas.

        Variáveis categóricas são avaliadas globalmente pelo teste
        de Wald e contam como UMA variável explicativa.
        """

        x_atual = list(x_cols_iniciais)

        historico = []

        if tabela_modelos.empty:

            return (x_atual, tabela_modelos, modelos, diagnosticos, historico, False)

        sucesso = True

        for etapa in range(1, max_iter + 1):

            if tabela_modelos.empty or not x_atual:

                sucesso = False
                break

            melhor_nome_etapa = tabela_modelos.iloc[0]["Modelo"]

            melhor_modelo_etapa = modelos[melhor_nome_etapa]

            avaliacao = avaliar_significancia_por_variavel(
                melhor_modelo_etapa,
                x_atual,
                selecionadas_numericas,
                selecionadas_categoricas,
                nomes_numericos,
                nomes_categoricos,
                alpha=alpha,
            )

            if not avaliacao:

                sucesso = False
                break

            total_variaveis = len(avaliacao)

            nao_sig = [item for item in avaliacao if not item["Significativa"]]

            qtd_nao_sig = len(nao_sig)

            proporcao_nao_sig = qtd_nao_sig / total_variaveis if total_variaveis > 0 else 0

            # ------------------------------------------------
            # CRITÉRIO ATINGIDO
            # ------------------------------------------------

            if proporcao_nao_sig <= limite_nao_significativas:

                historico.append(
                    {
                        "Etapa": etapa,
                        "Modelo": melhor_nome_etapa,
                        "Variáveis avaliadas": total_variaveis,
                        "Significativas": total_variaveis - qtd_nao_sig,
                        "Não significativas": qtd_nao_sig,
                        "% não significativas": proporcao_nao_sig * 100,
                        "Variável removida": "Nenhuma",
                        "p-valor da removida": np.nan,
                        "Ação": ("Critério atingido; manter modelo"),
                    }
                )

                break

            # ------------------------------------------------
            # ESCOLHER SOMENTE A MENOS SIGNIFICATIVA
            # ------------------------------------------------

            candidatos_remocao = [item for item in nao_sig if pd.notna(item["p-valor"])]

            if not candidatos_remocao:

                sucesso = False

                historico.append(
                    {
                        "Etapa": etapa,
                        "Modelo": melhor_nome_etapa,
                        "Variáveis avaliadas": total_variaveis,
                        "Significativas": total_variaveis - qtd_nao_sig,
                        "Não significativas": qtd_nao_sig,
                        "% não significativas": proporcao_nao_sig * 100,
                        "Variável removida": "Nenhuma",
                        "p-valor da removida": np.nan,
                        "Ação": ("Não foi possível identificar " "a variável menos significativa"),
                    }
                )

                break

            # Maior p-valor = menor evidência de associação.
            pior = max(candidatos_remocao, key=lambda item: item["p-valor"])

            nome_removida = pior["Variável"]

            p_removida = float(pior["p-valor"])

            cols_remover = set(pior["Colunas"])

            # Se for categórica, pior["Colunas"] contém TODAS
            # as dummies pertencentes ao fator.
            x_novo = [col for col in x_atual if col not in cols_remover]

            historico.append(
                {
                    "Etapa": etapa,
                    "Modelo": melhor_nome_etapa,
                    "Variáveis avaliadas": total_variaveis,
                    "Significativas": total_variaveis - qtd_nao_sig,
                    "Não significativas": qtd_nao_sig,
                    "% não significativas": proporcao_nao_sig * 100,
                    "Variável removida": nome_removida,
                    "p-valor da removida": p_removida,
                    "Ação": ("Remover somente a menos significativa " "e reajustar"),
                }
            )

            # Não estimar modelo sem explicativas.
            if not x_novo:

                sucesso = False

                historico.append(
                    {
                        "Etapa": etapa,
                        "Modelo": melhor_nome_etapa,
                        "Variáveis avaliadas": total_variaveis,
                        "Significativas": total_variaveis - qtd_nao_sig,
                        "Não significativas": qtd_nao_sig,
                        "% não significativas": proporcao_nao_sig * 100,
                        "Variável removida": nome_removida,
                        "p-valor da removida": p_removida,
                        "Ação": ("A remoção deixaria o modelo " "sem variáveis explicativas"),
                    }
                )

                break

            # ------------------------------------------------
            # RECALCULAR VIF DEPOIS DE CADA REMOÇÃO
            # ------------------------------------------------

            x_vif, _, _, _, vif_ok = aplicar_vif_iterativo(dados_modelo, x_novo, limite=10.0)

            if not vif_ok or not x_vif:

                sucesso = False

                historico.append(
                    {
                        "Etapa": etapa,
                        "Modelo": melhor_nome_etapa,
                        "Variáveis avaliadas": total_variaveis,
                        "Significativas": total_variaveis - qtd_nao_sig,
                        "Não significativas": qtd_nao_sig,
                        "% não significativas": proporcao_nao_sig * 100,
                        "Variável removida": nome_removida,
                        "p-valor da removida": p_removida,
                        "Ação": ("Após a remoção, não foi possível " "satisfazer VIF ≤ 10"),
                    }
                )

                break

            x_atual = list(x_vif)

            # ------------------------------------------------
            # REAJUSTAR TODAS AS FAMÍLIAS COMPATÍVEIS
            # ------------------------------------------------

            tabela_nova, modelos_novos, diagnosticos_novos = reajustar_modelos_apos_selecao(
                dados_modelo, y_col, x_atual, tipo_resposta
            )

            if tabela_nova.empty:

                sucesso = False

                historico.append(
                    {
                        "Etapa": etapa,
                        "Modelo": melhor_nome_etapa,
                        "Variáveis avaliadas": total_variaveis,
                        "Significativas": total_variaveis - qtd_nao_sig,
                        "Não significativas": qtd_nao_sig,
                        "% não significativas": proporcao_nao_sig * 100,
                        "Variável removida": nome_removida,
                        "p-valor da removida": p_removida,
                        "Ação": ("O modelo reduzido não pôde " "ser estimado ou validado"),
                    }
                )

                break

            # A seleção do melhor modelo é refeita porque
            # tabela_nova já vem ordenada pelo AICc.
            tabela_modelos = tabela_nova

            modelos = modelos_novos

            diagnosticos = diagnosticos_novos

        else:

            # Atingiu o número máximo de iterações.
            sucesso = False

            historico.append(
                {
                    "Etapa": max_iter,
                    "Modelo": (
                        tabela_modelos.iloc[0]["Modelo"] if not tabela_modelos.empty else "—"
                    ),
                    "Variáveis avaliadas": np.nan,
                    "Significativas": np.nan,
                    "Não significativas": np.nan,
                    "% não significativas": np.nan,
                    "Variável removida": "Nenhuma",
                    "p-valor da removida": np.nan,
                    "Ação": ("Limite máximo de iterações atingido"),
                }
            )

        return (x_atual, tabela_modelos, modelos, diagnosticos, historico, sucesso)

    # ========================================================
    # ÚNICA VARIÁVEL RESPOSTA — AVALIAÇÃO RUIM
    # ========================================================

    st.subheader("Configuração")

    st.info("**Variável resposta fixa:** Avaliação ruim " "(nota 1 ou 2 = 1; nota 3, 4 ou 5 = 0).")

    resposta_escolhida = "Avaliação ruim (nota 1 ou 2)"

    base_analise = construir_base_pedido(df_filtrado)

    nivel_modelo = "pedido"

    y_col = "avaliacao_ruim"

    tipo_resposta = "binaria"

    nome_y = "Probabilidade de avaliação ruim"

    pergunta_modelo = (
        "Quais características da compra, da logística, "
        "do pagamento, do produto e da localização estão "
        "associadas à chance de o cliente atribuir nota 1 ou 2?"
    )

    # --------------------------------------------------------
    # Variáveis numéricas opcionais
    # --------------------------------------------------------

    variaveis_numericas = {
        # PEDIDOS / variáveis logísticas derivadas diretamente das datas
        "Tempo de entrega (dias)": "dias_entrega",
        "Dias de atraso": "dias_atraso_positivo",
        "Pedido atrasado": "pedido_atrasado",
        "Prazo prometido (dias)": "prazo_entrega_dias",
        # GEOLOCALIZAÇÃO + CLIENTES + VENDEDORES
        "Distância logística (a cada 100 km)": "distancia_logistica_100",
        "Distância da capital (a cada 100 km)": "distancia_capital_100",
        # PAGAMENTOS
        "Valor total pago (a cada R$ 100)": "valor_pedido_100",
        "Número de parcelas": "payment_installments",
        # ITENS DO PEDIDO
        "Frete total (a cada R$ 10)": "frete_10",
        "Quantidade de itens": "quantidade_itens",
        # PRODUTOS
        "Peso total do pedido (kg)": "peso_total_kg",
        "Volume total do pedido (litros)": "volume_total_litros",
    }

    # --------------------------------------------------------
    # Variáveis categóricas opcionais
    # Todas vêm das bases utilizadas no projeto ou de
    # recodificações já existentes no banco analítico.
    # --------------------------------------------------------

    variaveis_categoricas = {
        # PRODUTOS + TRADUÇÃO
        "Categoria do produto": "categoria_produto_modelo",
        # PAGAMENTOS
        "Forma de pagamento": "forma_pagamento_modelo",
        # CLIENTES
        "Região do cliente": "regiao_modelo",
        "Estado do cliente": "estado_modelo",
    }

    # Conjunto inicial enxuto para apresentação.
    # O usuário ainda pode selecionar qualquer opção disponível.
    default_vars = [
        "Tempo de entrega (dias)",
        "Dias de atraso",
        "Prazo prometido (dias)",
        "Distância logística (a cada 100 km)",
        "Valor total pago (a cada R$ 100)",
        "Frete total (a cada R$ 10)",
        "Quantidade de itens",
        "Número de parcelas",
        "Categoria do produto",
        "Forma de pagamento",
        "Estado do cliente",
    ]

    st.info(f"**Pergunta do modelo:** {pergunta_modelo}")

    st.caption(
        "Sentimento do comentário e categoria da reclamação não entram "
        "como explicativas porque são produzidos a partir da própria "
        "avaliação/comentário e poderiam gerar vazamento de informação."
    )

    # ========================================================
    # OPÇÕES VÁLIDAS PARA O FILTRO ATUAL
    # ========================================================

    base_modelo = base_analise.replace([np.inf, -np.inf], np.nan).dropna(subset=[y_col]).copy()

    opcoes_validas = []

    for nome, coluna in variaveis_numericas.items():

        if coluna in base_modelo.columns and base_modelo[coluna].dropna().nunique() > 1:
            opcoes_validas.append(nome)

    for nome, coluna in variaveis_categoricas.items():

        if (
            coluna in base_modelo.columns
            and base_modelo[coluna].fillna("Não informado").nunique() > 1
        ):
            opcoes_validas.append(nome)

    default_vars = [nome for nome in default_vars if nome in opcoes_validas]

    explicativas = st.multiselect(
        "Variáveis explicativas",
        options=opcoes_validas,
        default=default_vars,
        key="reg_explicativas_final",
    )

    incluir_tendencia = False

    if nivel_modelo == "mensal":

        incluir_tendencia = st.checkbox(
            "Controlar tendência temporal", value=True, key="reg_tendencia_final"
        )

    st.caption(
        f"Modelo ajustado para: "
        f"**{regiao_texto}** | "
        f"Estados no filtro: "
        f"**{len(estados_selecionados)}** | "
        f"Categorias raras são agrupadas automaticamente | "
        f"VIF ≤ 10"
    )

    # ========================================================
    # PREPARAR O MODELO
    # ========================================================

    selecionadas_numericas = [
        variaveis_numericas[nome] for nome in explicativas if nome in variaveis_numericas
    ]

    selecionadas_categoricas = [
        variaveis_categoricas[nome] for nome in explicativas if nome in variaveis_categoricas
    ]

    # Região é determinada pelo estado.
    # Se ambos forem selecionados, mantemos Estado por ser mais detalhado.
    if "estado_modelo" in selecionadas_categoricas and "regiao_modelo" in selecionadas_categoricas:

        selecionadas_categoricas.remove("regiao_modelo")

        st.info(
            "**Região do cliente** foi retirada porque "
            "**Estado do cliente** já contém uma informação geográfica "
            "mais detalhada."
        )

    # "Pedido atrasado" é derivado de "Dias de atraso".
    # Quando ambos são selecionados, mantemos Dias de atraso,
    # que contém mais informação.
    if (
        "dias_atraso_positivo" in selecionadas_numericas
        and "pedido_atrasado" in selecionadas_numericas
    ):

        selecionadas_numericas.remove("pedido_atrasado")

        st.info(
            "**Pedido atrasado** foi retirado do modelo porque "
            "**Dias de atraso** já representa essa informação "
            "de forma mais detalhada."
        )

    if incluir_tendencia:

        selecionadas_numericas.append("tendencia")

        variaveis_numericas["Tendência temporal"] = "tendencia"

    if not selecionadas_numericas and not selecionadas_categoricas:

        st.warning("Selecione pelo menos uma variável explicativa.")

    else:

        nomes_numericos = {valor: nome for nome, valor in variaveis_numericas.items()}

        nomes_categoricos = {valor: nome for nome, valor in variaveis_categoricas.items()}

        dados_modelo, x_cols, nomes_amigaveis, referencias_categoricas = preparar_matriz_modelo(
            base_modelo,
            y_col,
            selecionadas_numericas,
            selecionadas_categoricas,
            nomes_numericos,
            nomes_categoricos,
            coluna_tempo=("mes_texto" if nivel_modelo == "mensal" else None),
        )

        if referencias_categoricas:

            with st.expander("Ver categorias de referência"):

                tabela_referencias = pd.DataFrame(
                    {
                        "Variável categórica": list(referencias_categoricas.keys()),
                        "Categoria de referência": list(referencias_categoricas.values()),
                    }
                )

                st.dataframe(tabela_referencias, use_container_width=True, hide_index=True)

        x_cols_finais, removidas = remover_colinearidade(dados_modelo, x_cols)

        if removidas:

            st.info(
                "Variáveis removidas por ausência de variação "
                "ou colinearidade perfeita: "
                + ", ".join(nomes_amigaveis.get(x, x) for x in removidas)
            )

        # ----------------------------------------------------
        # VIF — MULTICOLINEARIDADE
        # ----------------------------------------------------

        x_cols_vif, removidas_vif, tabela_vif_final, historico_vif, vif_valido = (
            aplicar_vif_iterativo(dados_modelo, x_cols_finais, limite=10.0)
        )

        x_cols_finais = x_cols_vif

        if removidas_vif:

            st.info(
                "Para controlar a multicolinearidade, "
                "o VIF removeu uma variável por vez: "
                + ", ".join(nomes_amigaveis.get(x, x) for x in removidas_vif)
                + "."
            )

        # ----------------------------------------------------
        # TAMANHO MÍNIMO DA AMOSTRA
        # ----------------------------------------------------

        pode_estimar = True

        if not vif_valido:

            pode_estimar = False

            st.warning(
                "Não foi possível obter um conjunto de "
                "variáveis explicativas com VIF ≤ 10. "
                "O modelo não será estimado neste filtro."
            )

        elif not x_cols_finais:

            pode_estimar = False

            st.warning(
                "Não restaram variáveis explicativas " "após o controle de multicolinearidade."
            )

        if pode_estimar and nivel_modelo == "mensal":

            minimo = max(12, len(x_cols_finais) + 5)

            if len(dados_modelo) < minimo:

                pode_estimar = False

                st.warning(
                    f"Não foi possível estimar "
                    f"com segurança: "
                    f"{len(dados_modelo)} meses "
                    f"válidos. O modelo exige "
                    f"pelo menos {minimo}."
                )

        elif pode_estimar:

            minimo = max(100, 10 * (len(x_cols_finais) + 1))

            if len(dados_modelo) < minimo:

                pode_estimar = False

                st.warning(
                    f"Não foi possível estimar "
                    f"com segurança: "
                    f"{len(dados_modelo)} "
                    f"pedidos completos. "
                    f"São necessários pelo "
                    f"menos {minimo}."
                )

        # ----------------------------------------------------
        # REGRESSÃO LOGÍSTICA — CONTROLE AUTOMÁTICO DE COMPLEXIDADE
        #
        # Critério prático: pelo menos 10 observações da classe
        # minoritária por parâmetro estimado (incluindo intercepto).
        #
        # Se o modelo estiver grande demais:
        # 1) remove primeiro o BLOCO categórico que mais consome
        #    parâmetros (todas as suas dummies de uma só vez);
        # 2) recalcula a razão eventos/parâmetro;
        # 3) se ainda necessário, remove preditores numéricos de
        #    menor prioridade, um por vez;
        # 4) só desiste se mesmo o modelo reduzido continuar inviável.
        # ----------------------------------------------------

        historico_complexidade = []

        if pode_estimar and tipo_resposta == "binaria":

            eventos = int(dados_modelo[y_col].sum())

            nao_eventos = len(dados_modelo) - eventos

            classe_minoritaria = min(eventos, nao_eventos)

            # Máximo de coeficientes explicativos permitido,
            # reservando 1 parâmetro para o intercepto.
            max_preditores_epv = max(1, int(classe_minoritaria // 10) - 1)

            # ------------------------------------------------
            # Identificar blocos categóricos presentes.
            # ------------------------------------------------

            blocos_categoricos = {}

            for nome_cat, coluna_cat in variaveis_categoricas.items():

                prefixo = coluna_cat + "__"

                cols_bloco = [col for col in x_cols_finais if col.startswith(prefixo)]

                if cols_bloco:

                    blocos_categoricos[nome_cat] = cols_bloco

            # ------------------------------------------------
            # 1. Remover blocos categóricos grandes, se preciso.
            # ------------------------------------------------

            while len(x_cols_finais) > max_preditores_epv and blocos_categoricos:

                nome_bloco = max(
                    blocos_categoricos,
                    key=lambda nome: len(
                        [col for col in blocos_categoricos[nome] if col in x_cols_finais]
                    ),
                )

                cols_remover = [
                    col for col in blocos_categoricos[nome_bloco] if col in x_cols_finais
                ]

                if not cols_remover:

                    blocos_categoricos.pop(nome_bloco, None)

                    continue

                antes = len(x_cols_finais)

                x_cols_finais = [col for col in x_cols_finais if col not in cols_remover]

                historico_complexidade.append(
                    {
                        "Etapa": "Redução por eventos/parâmetro",
                        "Removido": nome_bloco,
                        "Tipo": "Bloco categórico",
                        "Parâmetros removidos": len(cols_remover),
                        "Parâmetros antes": antes,
                        "Parâmetros depois": len(x_cols_finais),
                    }
                )

                blocos_categoricos.pop(nome_bloco, None)

            # ------------------------------------------------
            # 2. Se ainda estiver grande, reduzir numéricas.
            #
            # Ordem: primeiro variáveis complementares; por último
            # permanecem as variáveis mais diretamente ligadas
            # à pergunta de negócio.
            # ------------------------------------------------

            prioridades_remocao = {
                "pedido_atrasado": [
                    "payment_installments",
                    "volume_total_litros",
                    "distancia_capital_100",
                    "valor_pedido_100",
                    "quantidade_itens",
                    "peso_total_kg",
                    "frete_10",
                    "distancia_logistica_100",
                    "prazo_entrega_dias",
                ],
                "avaliacao_ruim": [
                    "volume_medio_item_litros",
                    "peso_medio_item_kg",
                    "frete_por_item_10",
                    "preco_medio_item_100",
                    "frete_percentual",
                    "vendedores_distintos",
                    "produtos_distintos",
                    "volume_total_litros",
                    "peso_total_kg",
                    "payment_installments",
                    "distancia_capital_100",
                    "valor_itens_100",
                    "valor_pedido_100",
                    "quantidade_itens",
                    "distancia_logistica_100",
                    "frete_10",
                    "prazo_entrega_dias",
                    "pedido_atrasado",
                    "dias_entrega",
                    "dias_atraso_positivo",
                ],
            }

            ordem_numericas = prioridades_remocao.get(y_col, [])

            for coluna_remover in ordem_numericas:

                if len(x_cols_finais) <= max_preditores_epv:
                    break

                if coluna_remover in x_cols_finais:

                    antes = len(x_cols_finais)

                    x_cols_finais.remove(coluna_remover)

                    historico_complexidade.append(
                        {
                            "Etapa": "Redução por eventos/parâmetro",
                            "Removido": nomes_amigaveis.get(coluna_remover, coluna_remover),
                            "Tipo": "Variável numérica",
                            "Parâmetros removidos": 1,
                            "Parâmetros antes": antes,
                            "Parâmetros depois": len(x_cols_finais),
                        }
                    )

            # ------------------------------------------------
            # 3. Verificação final da regra de 10 por parâmetro.
            # ------------------------------------------------

            parametros_totais = len(x_cols_finais) + 1

            epv_final = classe_minoritaria / parametros_totais if parametros_totais > 0 else np.nan

            if historico_complexidade:

                st.info(
                    "O modelo logístico foi simplificado "
                    "automaticamente para manter pelo menos "
                    "**10 observações da classe minoritária por parâmetro**."
                )

                with st.expander("Ver redução automática da complexidade"):

                    st.dataframe(
                        pd.DataFrame(historico_complexidade),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.caption(
                        f"Eventos: {eventos:,} | "
                        f"Não eventos: {nao_eventos:,} | "
                        f"Preditores finais: {len(x_cols_finais)} | "
                        f"EPV final: {epv_final:.1f}"
                    )

            if not x_cols_finais or epv_final < 10:

                pode_estimar = False

                st.warning(
                    "Mesmo após reduzir automaticamente "
                    "as categorias e variáveis menos prioritárias, "
                    "não foi possível obter um modelo logístico "
                    "com quantidade suficiente de eventos por parâmetro. "
                    f"Eventos: {eventos:,} | "
                    f"Não eventos: {nao_eventos:,} | "
                    f"EPV final: {epv_final:.1f}."
                )

            else:

                st.caption(
                    f"Regressão logística: "
                    f"{eventos:,} eventos | "
                    f"{nao_eventos:,} não eventos | "
                    f"{len(x_cols_finais)} preditores | "
                    f"EPV = {epv_final:.1f}."
                )

        if pode_estimar and not x_cols_finais:

            pode_estimar = False

            st.warning("Não restaram variáveis " "explicativas válidas.")

        # ====================================================
        # AJUSTE
        # ====================================================

        if pode_estimar:

            if tipo_resposta == "continua":

                tabela_modelos, modelos, diagnosticos = ajustar_modelos_continuos(
                    dados_modelo, y_col, x_cols_finais
                )

            elif tipo_resposta == "contagem":

                tabela_modelos, modelos, diagnosticos = ajustar_modelos_contagem(
                    dados_modelo, y_col, x_cols_finais
                )

            else:

                tabela_modelos, modelos, diagnosticos = ajustar_logistico(
                    dados_modelo, y_col, x_cols_finais
                )

                # --------------------------------------------
                # Fallback para separação/convergência
                #
                # Mesmo com EPV adequado, algumas combinações
                # de dummies podem causar separação quase perfeita
                # ou instabilidade numérica. Nesse caso o código
                # simplifica o modelo gradualmente e tenta de novo.
                # --------------------------------------------

                historico_fallback = []

                if tabela_modelos.empty:

                    x_tentativa = list(x_cols_finais)

                    max_tentativas = min(8, max(1, len(x_tentativa) - 1))

                    for _ in range(max_tentativas):

                        if len(x_tentativa) <= 1:
                            break

                        blocos_atuais = {}

                        for nome_cat, coluna_cat in variaveis_categoricas.items():

                            prefixo = coluna_cat + "__"

                            cols_bloco = [col for col in x_tentativa if col.startswith(prefixo)]

                            if cols_bloco:

                                blocos_atuais[nome_cat] = cols_bloco

                        if blocos_atuais:

                            nome_remover = max(
                                blocos_atuais, key=lambda nome: len(blocos_atuais[nome])
                            )

                            cols_remover = blocos_atuais[nome_remover]

                            x_tentativa = [col for col in x_tentativa if col not in cols_remover]

                            historico_fallback.append(
                                {
                                    "Removido": nome_remover,
                                    "Motivo": "Estabilidade/convergência",
                                    "Parâmetros removidos": len(cols_remover),
                                }
                            )

                        else:

                            candidato = None

                            for col in ordem_numericas:

                                if col in x_tentativa:

                                    candidato = col
                                    break

                            if candidato is None:

                                candidato = x_tentativa[-1]

                            x_tentativa.remove(candidato)

                            historico_fallback.append(
                                {
                                    "Removido": nomes_amigaveis.get(candidato, candidato),
                                    "Motivo": "Estabilidade/convergência",
                                    "Parâmetros removidos": 1,
                                }
                            )

                        tabela_teste, modelos_teste, diagnosticos_teste = ajustar_logistico(
                            dados_modelo, y_col, x_tentativa
                        )

                        if not tabela_teste.empty:

                            x_cols_finais = list(x_tentativa)

                            tabela_modelos = tabela_teste

                            modelos = modelos_teste

                            diagnosticos = diagnosticos_teste

                            # VIF já era adequado antes; como
                            # removemos preditores, mantemos apenas
                            # as linhas das variáveis que ficaram.
                            if tabela_vif_final is not None and not tabela_vif_final.empty:

                                tabela_vif_final = tabela_vif_final[
                                    tabela_vif_final["Variável"].isin(x_cols_finais)
                                ].copy()

                            break

                    if historico_fallback:

                        with st.expander("Ver ajustes automáticos para estabilidade"):

                            st.dataframe(
                                pd.DataFrame(historico_fallback),
                                use_container_width=True,
                                hide_index=True,
                            )

                            if not tabela_modelos.empty:

                                st.success("O modelo convergiu após " "a simplificação automática.")

                            else:

                                st.warning(
                                    "Mesmo após simplificação, "
                                    "o modelo logístico não convergiu "
                                    "de forma adequada."
                                )

            st.caption(
                "Como a resposta é binária, a família utilizada é " "Binomial com link logit."
            )

            if tabela_modelos.empty:

                mensagem_erro = diagnosticos.get(
                    "erro",
                    ("Nenhum modelo válido " "pôde ser estimado com " "os critérios definidos."),
                )

                st.warning(mensagem_erro)

            else:

                st.caption(
                    "A significância é avaliada a 5%. Se mais de 40% das "
                    "variáveis originais forem não significativas, a de maior "
                    "p-valor é retirada uma por vez e o modelo é reajustado."
                )

                # ============================================
                # REFINO AUTOMÁTICO POR SIGNIFICÂNCIA
                #
                # Regra:
                # - até 40% não significativas -> mantém;
                # - mais de 40% -> remove UMA variável por vez, começando pela menos significativa
                #   não significativas e reajusta;
                # - o processo repete até o modelo final ter
                #   no máximo 40% de não significativas.
                # ============================================

                (
                    x_cols_refinadas,
                    tabela_modelos_refinada,
                    modelos_refinados,
                    diagnosticos_refinados,
                    historico_significancia,
                    refino_ok,
                ) = refinar_por_significancia(
                    dados_modelo=dados_modelo,
                    y_col=y_col,
                    x_cols_iniciais=x_cols_finais,
                    tipo_resposta=tipo_resposta,
                    tabela_modelos=tabela_modelos,
                    modelos=modelos,
                    diagnosticos=diagnosticos,
                    selecionadas_numericas=selecionadas_numericas,
                    selecionadas_categoricas=selecionadas_categoricas,
                    nomes_numericos=nomes_numericos,
                    nomes_categoricos=nomes_categoricos,
                    limite_nao_significativas=0.40,
                    alpha=0.05,
                    max_iter=20,
                )

                if historico_significancia:

                    tabela_hist_sig = pd.DataFrame(historico_significancia)

                    with st.expander("Ver seleção automática por significância"):

                        st.dataframe(
                            tabela_hist_sig.round(2), use_container_width=True, hide_index=True
                        )

                        ultima = tabela_hist_sig.iloc[-1]

                        if ultima["% não significativas"] <= 40:

                            st.success(
                                "Modelo final com no máximo " "40% de variáveis não significativas."
                            )

                        else:

                            st.warning(
                                "O modelo exigiu redução backward: "
                                "a variável menos significativa foi retirada "
                                "uma por vez, com novo ajuste após cada etapa."
                            )

                if refino_ok:

                    x_cols_finais = list(x_cols_refinadas)

                    tabela_modelos = tabela_modelos_refinada

                    modelos = modelos_refinados

                    diagnosticos = diagnosticos_refinados

                    # Atualiza o VIF final para o conjunto refinado.
                    _, _, tabela_vif_final_refino, historico_vif_refino, vif_refino_ok = (
                        aplicar_vif_iterativo(dados_modelo, x_cols_finais, limite=10.0)
                    )

                    if (
                        vif_refino_ok
                        and tabela_vif_final_refino is not None
                        and not tabela_vif_final_refino.empty
                    ):

                        tabela_vif_final = tabela_vif_final_refino

                    if historico_vif_refino:

                        historico_vif = list(historico_vif) + list(historico_vif_refino)

                else:

                    st.error(
                        "O modelo não foi aceito como modelo final. "
                        "Após o refinamento, não foi possível obter "
                        "um ajuste válido com no máximo 40% de "
                        "variáveis explicativas não significativas."
                    )

                    tabela_modelos = pd.DataFrame()
                    modelos = {}
                    diagnosticos = {}

                if tabela_modelos.empty:

                    st.info(
                        "Altere as variáveis explicativas ou o filtro "
                        "de região/estado para tentar um novo ajuste."
                    )

                if not tabela_modelos.empty:

                    melhor_nome = tabela_modelos.iloc[0]["Modelo"]

                    melhor_modelo = modelos[melhor_nome]

                    diag = diagnosticos.get(melhor_nome, {})

                    melhor_aicc = tabela_modelos.iloc[0]["AICc"]

                    if pd.notna(melhor_aicc):

                        pseudo_r2_exibir = diag.get("pseudo_r2_mcfadden", np.nan)

                        if melhor_nome == "Logístico Binomial" and pd.notna(pseudo_r2_exibir):

                            st.success(
                                f"Modelo final: "
                                f"**{melhor_nome}** | "
                                f"AICc: "
                                f"**{melhor_aicc:.2f}** | "
                                f"Pseudo-R² de McFadden: "
                                f"**{pseudo_r2_exibir:.4f}**"
                            )

                        else:

                            st.success(
                                f"Modelo final: "
                                f"**{melhor_nome}** | "
                                f"AICc: "
                                f"**{melhor_aicc:.2f}**"
                            )

                    else:

                        st.success(f"Modelo final: " f"**{melhor_nome}**")

                    if melhor_nome == "Logístico Binomial" and pd.notna(
                        diag.get("pseudo_r2_mcfadden", np.nan)
                    ):

                        st.caption(
                            "O Pseudo-R² de McFadden compara o modelo final com "
                            "um modelo sem variáveis explicativas. Valores maiores "
                            "indicam maior melhora relativa; não representa a "
                            "porcentagem de variância explicada."
                        )

                    # ============================================
                    # VALIDAÇÃO
                    # ============================================

                    # ============================================
                    # AJUSTE DAS VARIÁVEIS CATEGÓRICAS
                    # ============================================

                    if selecionadas_categoricas:

                        tabela_resumo_categorias, tabela_detalhes_categorias = (
                            construir_tabelas_ajuste_categorias(
                                base=base_analise,
                                categoricas_selecionadas=(selecionadas_categoricas),
                                nomes_categoricos=(nomes_categoricos),
                                referencias_categoricas=(referencias_categoricas),
                                x_cols_finais=(x_cols_finais),
                            )
                        )

                        if not tabela_resumo_categorias.empty:

                            st.subheader("Ajuste das variáveis categóricas")

                            st.caption(
                                "A tabela mostra como cada variável categórica "
                                "entrou na regressão. Categoria do produto e "
                                "forma de pagamento podem ter níveis raros "
                                "agrupados. Estado e Região são preservados "
                                "integralmente: nenhuma UF ou região é reunida "
                                "com outra. A referência é a categoria usada "
                                "como base de comparação dos coeficientes."
                            )

                            st.dataframe(
                                tabela_resumo_categorias, use_container_width=True, hide_index=True
                            )

                            if not tabela_detalhes_categorias.empty:

                                with st.expander("Ver categorias antes e depois do ajuste"):

                                    st.dataframe(
                                        tabela_detalhes_categorias.sort_values(
                                            ["Variável", "Categoria após ajuste", "Quantidade"],
                                            ascending=[True, True, False],
                                        ).round({"Percentual (%)": 2}),
                                        use_container_width=True,
                                        hide_index=True,
                                    )

                                    st.caption(
                                        "**Mantida** = permaneceu com o próprio "
                                        "nome. **Agrupada** = categoria rara "
                                        "reunida em 'Outras/Outros'. "
                                        "**Preservada sem agrupamento** = Estado "
                                        "ou Região mantidos exatamente como na "
                                        "base. A referência é a categoria contra "
                                        "a qual os demais níveis são comparados."
                                    )

                            st.divider()

                    # ============================================
                    # COEFICIENTES
                    # ============================================

                    st.subheader("Efeitos estimados")

                    params = melhor_modelo.params

                    pvalues = melhor_modelo.pvalues

                    conf = melhor_modelo.conf_int()

                    resultados_coef = []

                    for param in params.index:

                        if param == "alpha":
                            continue

                        nome_param = (
                            "Intercepto" if param == "const" else nomes_amigaveis.get(param, param)
                        )

                        linha = {
                            "Variável": nome_param,
                            "Coeficiente": params[param],
                            "p-valor": pvalues[param],
                            "IC 95% inferior": conf.loc[param, 0],
                            "IC 95% superior": conf.loc[param, 1],
                        }

                        resultados_coef.append(linha)

                    tabela_coef = pd.DataFrame(resultados_coef)

                    tabela_coef["Significativo"] = np.where(
                        tabela_coef["p-valor"] < 0.05, "Sim", "Não"
                    )

                    modelos_link_log = {
                        "Gamma (link log)",
                        ("Gaussiano Inverso " "(link log)"),
                        "Poisson",
                        "Binomial Negativa",
                    }

                    if melhor_nome in modelos_link_log:

                        tabela_coef["Efeito (%)"] = (np.exp(tabela_coef["Coeficiente"]) - 1) * 100

                    elif melhor_nome == "Logístico Binomial":

                        tabela_coef["Odds Ratio"] = np.exp(tabela_coef["Coeficiente"])

                        tabela_coef["Variação nas chances (%)"] = (
                            np.exp(tabela_coef["Coeficiente"]) - 1
                        ) * 100

                    st.dataframe(tabela_coef.round(4), use_container_width=True)

                    # ============================================
                    # INTERPRETAÇÃO AUTOMÁTICA
                    # ============================================

                    with st.expander("Ver interpretação dos resultados", expanded=True):

                        st.markdown(
                            f"**Modelo:** " f"{melhor_nome}  \n" f"**Resposta:** " f"{nome_y}"
                        )

                        def unidade_explicativa(variavel):

                            if "(ref.:" in variavel:
                                return None

                            if variavel in {
                                "% sentimentos negativos",
                                "% sentimentos positivos",
                                "% reclamações classificadas",
                                "% reclamações de entrega",
                                "% pedidos atrasados",
                            }:
                                return "1 ponto percentual"

                            if variavel == "Nota média":
                                return "1 ponto"

                            if variavel == "Tendência temporal":
                                return "1 mês"

                            if "a cada 100 km" in variavel:
                                return "100 km"

                            if "a cada R$ 100" in variavel:
                                return "R&#36; 100,00"

                            if "a cada R$ 10" in variavel:
                                return "R&#36; 10,00"

                            if "Frete em relação ao valor" in variavel:
                                return "1 ponto percentual"

                            if variavel == "Produtos distintos no pedido":
                                return "1 produto distinto"

                            if variavel == "Vendedores distintos no pedido":
                                return "1 vendedor distinto"

                            if variavel == "Peso médio por item (kg)":
                                return "1 kg"

                            if variavel == "Volume médio por item (litros)":
                                return "1 litro"

                            if "(kg)" in variavel:
                                return "1 kg"

                            if "(litros)" in variavel:
                                return "1 litro"

                            if "(dias)" in variavel:
                                return "1 dia"

                            if variavel in {
                                "Número de parcelas",
                                "Pedidos do mês atual",
                                "Quantidade de itens",
                            }:
                                return "1 unidade"

                            return "1 unidade"

                        significativas = []
                        nao_significativas = []

                        # ------------------------------------------------
                        # INTERPRETAÇÃO INDIVIDUAL DE TODOS OS COEFICIENTES
                        # ------------------------------------------------

                        for _, linha_coef in tabela_coef.iterrows():

                            variavel = linha_coef["Variável"]

                            if variavel == "Intercepto":
                                continue

                            beta = linha_coef["Coeficiente"]

                            pvalor = linha_coef["p-valor"]

                            significativo = pd.notna(pvalor) and pvalor < 0.05

                            eh_categoria = "(ref.:" in variavel

                            unidade = unidade_explicativa(variavel)

                            # ============================================
                            # REGRESSÃO LOGÍSTICA
                            # ============================================

                            if melhor_nome == "Logístico Binomial":

                                odds_ratio = np.exp(beta)

                                efeito = (odds_ratio - 1) * 100

                                direcao = "aumento" if efeito >= 0 else "redução"

                                if eh_categoria:

                                    texto = (
                                        f"**{variavel}:** "
                                        f"em relação à categoria de referência, "
                                        f"apresenta **odds ratio = "
                                        f"{odds_ratio:.3f}**, correspondendo a "
                                        f"**{abs(efeito):.2f}% de {direcao} "
                                        f"nas chances** de "
                                        f"{nome_y.replace('Probabilidade de ', '').lower()}; "
                                        f"p = {pvalor:.4f}."
                                    )

                                else:

                                    texto = (
                                        f"**{variavel}:** "
                                        f"para cada aumento de "
                                        f"**{unidade}**, apresenta "
                                        f"**odds ratio = {odds_ratio:.3f}**, "
                                        f"equivalente a **{abs(efeito):.2f}% "
                                        f"de {direcao} nas chances** de "
                                        f"{nome_y.replace('Probabilidade de ', '').lower()}; "
                                        f"p = {pvalor:.4f}."
                                    )

                            # ============================================
                            # MODELOS COM LINK LOG
                            # ============================================

                            elif melhor_nome in modelos_link_log:

                                razao_medias = np.exp(beta)

                                efeito = (razao_medias - 1) * 100

                                direcao = "aumento" if efeito >= 0 else "redução"

                                alvo = (
                                    "na quantidade esperada"
                                    if tipo_resposta == "contagem"
                                    else "na média esperada"
                                )

                                if eh_categoria:

                                    texto = (
                                        f"**{variavel}:** "
                                        f"em relação à categoria de referência, "
                                        f"estima-se **razão = "
                                        f"{razao_medias:.3f}**, equivalente a "
                                        f"**{abs(efeito):.2f}% de {direcao} "
                                        f"{alvo}** de "
                                        f"{nome_y.lower()}; "
                                        f"p = {pvalor:.4f}."
                                    )

                                else:

                                    texto = (
                                        f"**{variavel}:** "
                                        f"para cada aumento de "
                                        f"**{unidade}**, estima-se "
                                        f"**razão = {razao_medias:.3f}**, "
                                        f"equivalente a **{abs(efeito):.2f}% "
                                        f"de {direcao} {alvo}** de "
                                        f"{nome_y.lower()}; "
                                        f"p = {pvalor:.4f}."
                                    )

                            # ============================================
                            # MODELO GAUSSIANO
                            # ============================================

                            else:

                                direcao = "aumento" if beta >= 0 else "redução"

                                if eh_categoria:

                                    texto = (
                                        f"**{variavel}:** "
                                        f"em relação à categoria de referência, "
                                        f"estima-se **{abs(beta):.4f} "
                                        f"unidade(s) de {direcao}** em "
                                        f"{nome_y.lower()}; "
                                        f"p = {pvalor:.4f}."
                                    )

                                else:

                                    texto = (
                                        f"**{variavel}:** "
                                        f"para cada aumento de "
                                        f"**{unidade}**, estima-se "
                                        f"**{abs(beta):.4f} unidade(s) "
                                        f"de {direcao}** em "
                                        f"{nome_y.lower()}; "
                                        f"p = {pvalor:.4f}."
                                    )

                            # ============================================
                            # SEPARAR EM SIGNIFICATIVAS E NÃO SIGNIFICATIVAS
                            # ============================================

                            if significativo:

                                significativas.append(texto)

                            else:

                                nao_significativas.append(
                                    (
                                        f"**{variavel}:** não apresentou "
                                        f"associação estatisticamente "
                                        f"significativa (p = {pvalor:.4f})."
                                    )
                                )

                        # ------------------------------------------------
                        # EXIBIÇÃO
                        # ------------------------------------------------

                        st.markdown("##### Variáveis significativas")

                        if significativas:

                            for texto_int in significativas:

                                st.markdown("- " + texto_int)

                        else:

                            st.info(
                                "Nenhuma variável ou categoria "
                                "apresentou significância estatística a 5%."
                            )

                        st.markdown("##### Variáveis não significativas")

                        if nao_significativas:

                            for texto_int in nao_significativas:

                                st.markdown("- " + texto_int)

                        else:

                            st.success(
                                "Todos os coeficientes apresentados "
                                "no modelo final foram significativos a 5%."
                            )

                        st.caption(
                            "As interpretações indicam "
                            "associações ajustadas e não "
                            "demonstram causalidade."
                        )

                    # ============================================
                    # OBSERVADO X PREVISTO
                    # ============================================

                    X_final = dados_modelo[x_cols_finais].astype(float)

                    X_final = sm.add_constant(X_final, has_constant="add")

                    previsto = melhor_modelo.predict(X_final)

                    if nivel_modelo == "mensal":

                        eixo_x = dados_modelo["mes_texto"].values

                        titulo_x = "Mês"

                    else:

                        eixo_x = np.arange(1, len(dados_modelo) + 1)

                        titulo_x = "Observação"

                    ajuste = pd.DataFrame(
                        {
                            titulo_x: eixo_x,
                            "Observado": dados_modelo[y_col].values,
                            "Previsto": np.asarray(previsto),
                        }
                    )

                    # Para bases de pedido muito grandes,
                    # amostra pontos apenas para visualização.
                    if len(ajuste) > 2000:

                        ajuste_grafico = ajuste.sample(2000, random_state=123).sort_index()

                    else:

                        ajuste_grafico = ajuste

                    fig = go.Figure()

                    fig.add_trace(
                        go.Scatter(
                            x=(ajuste_grafico[titulo_x]),
                            y=(ajuste_grafico["Observado"]),
                            mode="markers",
                            name="Observado",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=(ajuste_grafico[titulo_x]),
                            y=(ajuste_grafico["Previsto"]),
                            mode="markers",
                            name="Previsto",
                        )
                    )

                    fig.update_layout(
                        title=("Observado x previsto"), xaxis_title=(titulo_x), yaxis_title=(nome_y)
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # ============================================
                    # PRESSUPOSTOS
                    # ============================================

                    with st.expander("Ver pressupostos do modelo selecionado"):

                        st.markdown(f"**Modelo atual:** " f"{melhor_nome}")

                        # ----------------------------------------
                        # VIF
                        # ----------------------------------------

                        st.markdown("#### Multicolinearidade — VIF")

                        st.caption(
                            "O VIF é calculado depois do tratamento "
                            "das categóricas e da criação do banco final. "
                            "Critério adotado: VIF ≤ 10."
                        )

                        if tabela_vif_final is not None and not tabela_vif_final.empty:

                            tabela_vif_exibir = tabela_vif_final.copy()

                            if "Variável" in tabela_vif_exibir.columns:

                                tabela_vif_exibir["Variável"] = tabela_vif_exibir["Variável"].map(
                                    lambda x: nomes_amigaveis.get(x, x)
                                )

                            tabela_vif_exibir["Situação"] = np.where(
                                tabela_vif_exibir["VIF"] <= 10, "Atendido", "Não atendido"
                            )

                            st.dataframe(
                                tabela_vif_exibir.round(3),
                                use_container_width=True,
                                hide_index=True,
                            )

                        st.divider()

                        # ----------------------------------------
                        # VALIDAÇÃO DO MODELO FINAL
                        # ----------------------------------------

                        st.markdown("#### Validação do modelo")

                        st.caption(
                            "Depois do VIF, são apresentados os diagnósticos "
                            "do modelo final em linguagem simples. Os alertas "
                            "de resíduos, influência e calibração não removem "
                            "automaticamente variáveis explicativas."
                        )

                        st.subheader("Validação")

                        tabela_diag_final = diag.get("tabela_diagnostico", pd.DataFrame())

                        if tabela_diag_final is not None and not tabela_diag_final.empty:

                            # ------------------------------------------------
                            # Tabela de diagnóstico em linguagem simples
                            # ------------------------------------------------
                            # A tabela técnica continua sendo usada internamente.
                            # Aqui mostramos uma versão mais fácil de apresentar.
                            if melhor_nome == "Logístico Binomial":

                                explicacoes_simples = {
                                    "Convergência": (
                                        "O modelo conseguiu fazer os cálculos e encontrar "
                                        "os coeficientes normalmente."
                                    ),
                                    "Estrutura da resposta": (
                                        "Confere se existem os dois resultados possíveis: "
                                        "avaliação ruim (1) e não ruim (0)."
                                    ),
                                    "Resíduos finitos": (
                                        "Confere se os erros calculados pelo modelo possuem "
                                        "valores válidos, sem infinito ou erro numérico."
                                    ),
                                    "Resíduos Pearson extremos": (
                                        "Mostra a porcentagem de pedidos em que o resultado "
                                        "observado ficou muito diferente do previsto pelo modelo."
                                    ),
                                    "Padrão resíduos × ajustados": (
                                        "Verifica se os erros ainda apresentam um padrão em "
                                        "relação às probabilidades previstas. Um padrão forte "
                                        "é um alerta de que o modelo pode não captar toda a "
                                        "estrutura dos dados."
                                    ),
                                    "Observações influentes (Cook)": (
                                        "Procura pedidos que podem exercer influência maior "
                                        "sobre os coeficientes do modelo."
                                    ),
                                    "Eventos por parâmetro": (
                                        "Confere se há quantidade suficiente de avaliações "
                                        "ruins e não ruins para o número de parâmetros estimados."
                                    ),
                                    "Hosmer-Lemeshow": (
                                        "Compara as probabilidades previstas com o que realmente "
                                        "aconteceu. Serve como alerta sobre a calibração do modelo."
                                    ),
                                    "Brier score": (
                                        "Mede o erro das probabilidades previstas. Quanto menor "
                                        "o valor, melhores tendem a ser as previsões probabilísticas."
                                    ),
                                    "Pseudo-R² de McFadden": (
                                        "Mostra quanto o modelo com as variáveis explicativas "
                                        "melhora em relação a um modelo que não usa nenhuma "
                                        "explicativa, apenas o valor médio geral."
                                    ),
                                    "Resíduos quantílicos (Shapiro)": (
                                        "Verifica o comportamento dos resíduos quantílicos. "
                                        "Na regressão logística é apenas uma informação complementar."
                                    ),
                                }

                                nomes_simples = {
                                    "Convergência": "Cálculo do modelo",
                                    "Estrutura da resposta": "Resposta 0/1",
                                    "Resíduos finitos": "Erros calculáveis",
                                    "Resíduos Pearson extremos": "Casos muito diferentes do previsto",
                                    "Padrão resíduos × ajustados": "Padrão nos erros",
                                    "Observações influentes (Cook)": "Pedidos com maior influência",
                                    "Eventos por parâmetro": "Quantidade de dados",
                                    "Hosmer-Lemeshow": "Previsto × observado",
                                    "Brier score": "Erro das probabilidades",
                                    "Pseudo-R² de McFadden": "Poder explicativo do modelo",
                                    "Resíduos quantílicos (Shapiro)": "Comportamento dos resíduos",
                                }

                                def leitura_simples_diag(linha):
                                    teste = linha.get("Teste", "")
                                    resultado = str(linha.get("Resultado", ""))
                                    situacao = linha.get("Situação", "")

                                    if teste == "Convergência":
                                        return (
                                            "OK — o modelo foi estimado normalmente."
                                            if resultado == "Sim"
                                            else "Problema — o modelo não conseguiu ser estimado."
                                        )

                                    if teste == "Estrutura da resposta":
                                        return (
                                            "OK — existem avaliações ruins e não ruins."
                                            if situacao == "Atendido"
                                            else "Problema — falta uma das duas respostas (0 ou 1)."
                                        )

                                    if teste == "Resíduos finitos":
                                        return (
                                            "OK — os erros do modelo puderam ser calculados."
                                            if situacao == "Atendido"
                                            else "Atenção — existem erros que não puderam ser calculados."
                                        )

                                    if teste == "Resíduos Pearson extremos":
                                        return (
                                            f"{resultado} dos casos ficaram muito distantes do previsto. "
                                            + (
                                                "Está dentro do limite de referência usado no painel."
                                                if situacao == "Atendido"
                                                else "É um ponto de atenção, mas não exclui o modelo sozinho."
                                            )
                                        )

                                    if teste == "Padrão resíduos × ajustados":
                                        return f"Resultado: {resultado}. " + (
                                            "Não foi identificado um padrão relevante nos erros."
                                            if situacao == "Atendido"
                                            else "Há um padrão nos erros; interpretar como alerta diagnóstico."
                                        )

                                    if teste == "Observações influentes (Cook)":
                                        if resultado == "NA":
                                            return (
                                                "Não foi possível calcular esta medida neste ajuste; "
                                                "isso não invalida o modelo."
                                            )
                                        return (
                                            f"{resultado} dos casos ultrapassaram a referência de influência. "
                                            "Eles merecem investigação, não exclusão automática."
                                        )

                                    if teste == "Eventos por parâmetro":
                                        return f"{resultado}. " + (
                                            "Há dados suficientes para a quantidade de parâmetros do modelo."
                                            if situacao == "Atendido"
                                            else "A quantidade de dados pode ser pequena para o tamanho do modelo."
                                        )

                                    if teste == "Hosmer-Lemeshow":
                                        return f"{resultado}. " + (
                                            "Não foi detectada diferença importante entre previsto e observado."
                                            if situacao == "Atendido"
                                            else "Há diferença detectável entre previsto e observado; é um alerta de calibração."
                                        )

                                    if teste == "Brier score":
                                        return (
                                            f"Erro médio probabilístico = {resultado}. "
                                            "Quanto mais próximo de zero, melhor. Deve ser interpretado "
                                            "junto com outras medidas do modelo."
                                        )

                                    if teste == "Pseudo-R² de McFadden":
                                        try:
                                            valor_mcf = float(resultado)
                                        except Exception:
                                            valor_mcf = np.nan

                                        if pd.isna(valor_mcf):
                                            return (
                                                "Não foi possível calcular o Pseudo-R² de McFadden "
                                                "neste ajuste."
                                            )

                                        return (
                                            f"Pseudo-R² de McFadden = {valor_mcf:.4f}. "
                                            "Quanto maior esse valor, maior a melhora do modelo "
                                            "em relação ao modelo sem variáveis explicativas. "
                                            "Ele não deve ser interpretado como percentual de "
                                            "variância explicada, como no R² da regressão linear."
                                        )

                                    if teste == "Resíduos quantílicos (Shapiro)":
                                        return f"{resultado}. " + (
                                            "O diagnóstico complementar não indicou problema."
                                            if situacao == "Atendido"
                                            else "Há um alerta complementar, mas normalidade não é uma exigência da regressão logística."
                                        )

                                    return resultado

                                tabela_exibicao = tabela_diag_final.copy()

                                tabela_exibicao["Verificação"] = (
                                    tabela_exibicao["Teste"]
                                    .map(nomes_simples)
                                    .fillna(tabela_exibicao["Teste"])
                                )

                                tabela_exibicao["O que isso verifica?"] = (
                                    tabela_exibicao["Teste"]
                                    .map(explicacoes_simples)
                                    .fillna("Diagnóstico complementar do modelo.")
                                )

                                tabela_exibicao["Interpretação do resultado"] = (
                                    tabela_exibicao.apply(leitura_simples_diag, axis=1)
                                )

                                tabela_exibicao["Conclusão"] = (
                                    tabela_exibicao["Situação"]
                                    .map(
                                        {
                                            "Atendido": "OK",
                                            "Atenção": "Atenção",
                                            "Informativo": "Informação",
                                            "Não atendido": "Problema",
                                        }
                                    )
                                    .fillna(tabela_exibicao["Situação"])
                                )

                                tabela_exibicao = tabela_exibicao[
                                    [
                                        "Verificação",
                                        "O que isso verifica?",
                                        "Interpretação do resultado",
                                        "Conclusão",
                                    ]
                                ]

                                st.dataframe(
                                    tabela_exibicao, use_container_width=True, hide_index=True
                                )

                                st.caption(
                                    "Leitura rápida: **OK** = resultado adequado; "
                                    "**Atenção** = merece ser observado, mas não invalida "
                                    "automaticamente a regressão; **Informação** = medida "
                                    "complementar."
                                )

                            else:

                                st.dataframe(
                                    tabela_diag_final, use_container_width=True, hide_index=True
                                )

                        # Na regressão logística, o modelo já passou pelas
                        # verificações estruturais antes desta etapa.
                        # Aqui os resíduos e demais medidas são interpretados
                        # como diagnóstico do modelo final.
                        if melhor_nome == "Logístico Binomial":

                            tabela_alertas = (
                                tabela_diag_final.loc[
                                    tabela_diag_final["Situação"].isin(["Atenção", "Não atendido"])
                                ]
                                if (
                                    tabela_diag_final is not None
                                    and not tabela_diag_final.empty
                                    and "Situação" in tabela_diag_final.columns
                                )
                                else pd.DataFrame()
                            )

                            if tabela_alertas.empty:

                                st.success(
                                    "O modelo logístico final foi estimado com "
                                    "estabilidade e não apresentou alertas relevantes "
                                    "nos diagnósticos avaliados."
                                )

                            else:

                                st.warning(
                                    "O modelo logístico final foi estimado e mantido, "
                                    "mas há um ou mais alertas diagnósticos na tabela "
                                    "acima. Esses alertas devem ser considerados na "
                                    "interpretação, mas não provocam retirada automática "
                                    "de variáveis."
                                )

                        elif diag.get("valido", False):

                            st.success(
                                "O modelo final atendeu aos critérios "
                                "obrigatórios de diagnóstico definidos "
                                "para a sua distribuição."
                            )

                        else:

                            motivos_diag = diag.get("motivos", [])

                            if motivos_diag:

                                st.warning(
                                    "O modelo não foi considerado plenamente "
                                    "adequado porque: " + "; ".join(motivos_diag) + "."
                                )

                            else:

                                st.warning(
                                    diag.get(
                                        "mensagem",
                                        (
                                            "O modelo não atendeu a todos "
                                            "os critérios obrigatórios."
                                        ),
                                    )
                                )

                        st.caption(
                            "Nos MLGs, não se exige normalidade dos resíduos "
                            "comuns como no modelo Gaussiano. Os diagnósticos "
                            "usam resíduos de Pearson/deviance e, de forma "
                            "complementar, resíduos quantílicos."
                        )

                        dados_resid_plot, nome_resid_plot = preparar_grafico_residuos(
                            melhor_modelo, melhor_nome
                        )

                        if not dados_resid_plot.empty:

                            with st.expander("Ver gráfico de resíduos do modelo final"):

                                fig_resid = px.scatter(
                                    dados_resid_plot,
                                    x="Valor ajustado",
                                    y=nome_resid_plot,
                                    title=(f"{nome_resid_plot} " "versus valores ajustados"),
                                )

                                fig_resid.add_hline(y=0, line_dash="dash")

                                st.plotly_chart(fig_resid, use_container_width=True)

# ============================================================
# ABA 2 — ANÁLISES ESTATÍSTICAS | SÉRIE TEMPORAL
# ============================================================
with abas[2]:

    st.divider()

    st.header("Série Temporal: Vendas x Satisfação")

    serie = (
        df_filtrado
        .groupby("ano_mes")
        .agg(
            receita=("payment_value", "sum"),
            pedidos=("order_id", "nunique"),
            nota_media=("review_score", "mean"),
            taxa_atraso=("atrasou", lambda s: s.mean() * 100)
        )
        .reset_index()
        .sort_values("ano_mes")
    )

    serie["Receita_formatada"] = serie["receita"].apply(
        formatar_moeda
    )

    col1, col2 = st.columns(2)

    with col1:

        fig = px.line(
            serie,
            x="ano_mes",
            y="receita",
            markers=True,
            custom_data=["Receita_formatada"],
            title="Receita mensal",
            labels={
                "ano_mes": "Mês",
                "receita": "Receita"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "Mês: %{x}<br>"
                "Receita: %{customdata[0]}"
                "<extra></extra>"
            )
        )

        fig.update_yaxes(
            tickformat=".3s"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.line(
            serie,
            x="ano_mes",
            y="nota_media",
            markers=True,
            title="Nota média mensal",
            labels={
                "ano_mes": "Mês",
                "nota_media": "Nota média"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    col1, col2 = st.columns(2)

    with col1:

        fig = px.line(
            serie,
            x="ano_mes",
            y="pedidos",
            markers=True,
            title="Pedidos mensais",
            labels={
                "ano_mes": "Mês",
                "pedidos": "Pedidos"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.line(
            serie,
            x="ano_mes",
            y="taxa_atraso",
            markers=True,
            title="Taxa mensal de atraso",
            labels={
                "ano_mes": "Mês",
                "taxa_atraso": "Atraso (%)"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    correlacao = serie["receita"].corr(
        serie["nota_media"]
    )

    st.subheader("Relação entre vendas e satisfação")

    if pd.notna(correlacao):
        st.info(
            f"Correlação de Pearson entre receita mensal e nota média: "
            f"**{correlacao:.2f}**."
        )

        if correlacao > 0.5:
            st.write(
                "Neste recorte, meses com maior receita tendem a apresentar "
                "maior nota média. A correlação não implica causalidade."
            )
        elif correlacao < -0.5:
            st.write(
                "Neste recorte, meses com maior receita tendem a apresentar "
                "menor nota média. A correlação não implica causalidade."
            )
        else:
            st.write(
                "A associação linear entre receita mensal e nota média "
                "é fraca ou moderada neste recorte."
            )

    tabela_serie = serie.copy()
    tabela_serie["receita"] = tabela_serie[
        "receita"
    ].apply(formatar_moeda)

    st.dataframe(
        tabela_serie,
        use_container_width=True
    )

with abas[3]:

    st.header("Análise de Sentimentos")

    st.write("""
Os sentimentos desta seção foram previamente calculados pelo
modelo usado no projeto e armazenados em
`resultado_sentimentos.csv`.

**O modelo não é carregado nem executado pelo Streamlit.**
O dashboard apenas consulta as classificações prontas.
""")

    sentimentos_validos = (
        df_filtrado
        .dropna(
            subset=["sentimento_texto"]
        )
        .copy()
    )

    total_comentarios = len(
        sentimentos_validos
    )

    st.metric(
        "Comentários classificados",
        formatar_valor(total_comentarios)
    )

    if total_comentarios > 0:

        col1, col2 = st.columns(2)

        with col1:

            sentimentos = (
                sentimentos_validos["sentimento_texto"]
                .value_counts()
                .rename_axis("Sentimento")
                .reset_index(name="Quantidade")
            )

            sentimentos["Percentual"] = percentual(
                sentimentos["Quantidade"]
            )

            fig = grafico_barras_percentual(
                sentimentos,
                x="Sentimento",
                y="Quantidade",
                titulo="Distribuição dos sentimentos",
                nome_x="Sentimento"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            sentimento_nota = (
                sentimentos_validos
                .groupby("sentimento_texto", as_index=False)
                .agg(
                    nota_media=(
                        "review_score",
                        "mean"
                    )
                )
                .sort_values(
                    "nota_media",
                    ascending=False
                )
            )

            fig = px.bar(
                sentimento_nota,
                x="sentimento_texto",
                y="nota_media",
                text="nota_media",
                title="Sentimento x nota média",
                labels={
                    "sentimento_texto": "Sentimento",
                    "nota_media": "Nota média"
                }
            )

            fig.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:

            dados_entrega = sentimentos_validos.assign(
                Status=lambda x: x["atrasou"].map({
                    True: "Atrasada",
                    False: "No prazo"
                })
            )

            sentimento_entrega = (
                dados_entrega
                .groupby(
                    ["Status", "sentimento_texto"]
                )
                .size()
                .reset_index(
                    name="Quantidade"
                )
            )

            sentimento_entrega["Percentual"] = (
                sentimento_entrega
                .groupby("Status")["Quantidade"]
                .transform(
                    lambda s: s / s.sum() * 100
                )
            )

            fig = px.bar(
                sentimento_entrega,
                x="Status",
                y="Percentual",
                color="sentimento_texto",
                barmode="group",
                text="Percentual",
                title="Sentimento por status de entrega (%)",
                labels={
                    "Percentual": "Percentual (%)",
                    "sentimento_texto": "Sentimento"
                }
            )

            fig.update_traces(
                texttemplate="%{text:.1f}%"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            sentimento_estado = (
                sentimentos_validos
                .groupby(
                    ["customer_state", "sentimento_texto"]
                )
                .size()
                .reset_index(
                    name="Quantidade"
                )
            )

            sentimento_estado["Percentual"] = (
                sentimento_estado
                .groupby("customer_state")["Quantidade"]
                .transform(
                    lambda s: s / s.sum() * 100
                )
            )

            fig = px.bar(
                sentimento_estado,
                x="customer_state",
                y="Percentual",
                color="sentimento_texto",
                barmode="stack",
                title="Composição dos sentimentos por estado (%)",
                labels={
                    "customer_state": "Estado",
                    "Percentual": "Percentual (%)",
                    "sentimento_texto": "Sentimento"
                }
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.divider()
   
    # ========================================================
    # NUVENS DE PALAVRAS
    # ========================================================

    st.header("Nuvens de Palavras por Sentimento")

    st.write("""
    As nuvens apresentam as palavras mais frequentes encontradas
    nos comentários de cada classificação de sentimento.
    """)

    # Importações
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import re

    # --------------------------------------------------------
    # PALAVRAS A SEREM IGNORADAS
    # --------------------------------------------------------

    stopwords_pt = {
        "a", "o", "e", "é", "de", "do", "da", "dos", "das",
        "um", "uma", "uns", "umas", "em", "no", "na", "nos",
        "nas", "por", "para", "com", "sem", "que", "se",
        "não", "sim", "mais", "menos", "muito", "muita",
        "muitos", "muitas", "meu", "minha", "meus", "minhas",
        "seu", "sua", "seus", "suas", "ao", "aos", "às",
        "como", "mas", "ou", "já", "foi", "ser", "são",
        "está", "estão", "tem", "têm", "ter", "há", "isso",
        "esse", "essa", "esse", "essa", "ele", "ela",
        "eles", "elas", "eu", "tu", "você", "vocês",
        "me", "te", "lhe", "nos", "se", "pra", "pro",
        "bem", "também", "só", "até", "quando", "onde",
        "porque", "qual", "qualquer", "cada"
    }

    def limpar_texto(texto):

        texto = str(texto).lower()

        # Remove URLs
        texto = re.sub(
            r"http\S+|www\S+",
            "",
            texto
        )

        # Remove números
        texto = re.sub(
            r"\d+",
            "",
            texto
        )

        # Remove caracteres especiais
        texto = re.sub(
            r"[^a-záàâãéêíóôõúçü\s]",
            " ",
            texto
        )

        palavras = texto.split()

        palavras = [
            palavra
            for palavra in palavras
            if palavra not in stopwords_pt
            and len(palavra) > 2
        ]

        return " ".join(palavras)

    # --------------------------------------------------------
    # FUNÇÃO PARA GERAR NUVEM
    # --------------------------------------------------------

    def gerar_nuvem(sentimento):

        dados = df_filtrado[
            df_filtrado["sentimento_texto"] == sentimento
        ]

        comentarios = (
            dados["review_comment_message"]
            .dropna()
            .astype(str)
        )

        if comentarios.empty:
            return None

        texto = " ".join(
            comentarios.apply(limpar_texto)
        )

        if not texto.strip():
            return None

        nuvem = WordCloud(
            width=900,
            height=500,
            background_color="white",
            stopwords=stopwords_pt,
            min_font_size=10,
            max_words=100
        ).generate(texto)

        return nuvem

    # --------------------------------------------------------
    # GERAR AS 3 NUVENS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    sentimentos_nuvem = [
        ("Positivo", col1),
        ("Neutro", col2),
        ("Negativo", col3)
    ]

    for sentimento, coluna in sentimentos_nuvem:

        with coluna:

            st.subheader(
                f"☁️ {sentimento}"
            )

            nuvem = gerar_nuvem(
                sentimento
            )

            if nuvem is not None:

                fig, ax = plt.subplots(
                    figsize=(8, 5)
                )

                ax.imshow(
                    nuvem,
                    interpolation="bilinear"
                )

                ax.axis("off")

                st.pyplot(
                    fig,
                    use_container_width=True
                )

                plt.close(fig)

            else:

                st.info(
                    f"Não existem comentários "
                    f"{sentimento.lower()} no filtro atual."
                )

    st.divider()

    # ========================================================
    # BAG OF WORDS
    # ========================================================

    st.header(
        "📊 Bag of Words — Palavras Mais Frequentes"
    )

    st.write("""
    O gráfico abaixo apresenta as palavras mais frequentes
    encontradas nos comentários, considerando o filtro atual.
    """)

    comentarios_bow = (
        df_filtrado["review_comment_message"]
        .dropna()
        .astype(str)
        .apply(limpar_texto)
    )

    comentarios_bow = comentarios_bow[
        comentarios_bow.str.strip() != ""
    ]

    if not comentarios_bow.empty:

        from sklearn.feature_extraction.text import CountVectorizer

        vectorizer = CountVectorizer(
            max_features=20,
            ngram_range=(1, 1)
        )

        matriz = vectorizer.fit_transform(
            comentarios_bow
        )

        frequencias = (
            matriz.sum(axis=0)
            .A1
        )

        palavras = (
            vectorizer
            .get_feature_names_out()
        )

        bow_df = pd.DataFrame({
            "Palavra": palavras,
            "Frequência": frequencias
        })

        bow_df = (
            bow_df
            .sort_values(
                "Frequência",
                ascending=False
            )
            .reset_index(drop=True)
        )

        # Gráfico
        st.bar_chart(
            bow_df.set_index("Palavra")
        )

        # Tabela
        st.subheader(
            "Tabela de Frequência das Palavras"
        )

        st.dataframe(
            bow_df,
            use_container_width=True
        )

    else:

        st.info(
            "Não existem comentários disponíveis "
            "para gerar o Bag of Words no filtro atual."
        )

    st.divider()

    # ========================================================
    # COMENTÁRIOS NEGATIVOS
    # ========================================================

    st.subheader(
        "Comentários Negativos"
    )

    comentarios_negativos = (
        df_filtrado[
            df_filtrado["sentimento_texto"]
            == "Negativo"
        ][
            [
                "customer_state",
                "review_score",
                "review_comment_message"
            ]
        ]
        .dropna(
            subset=["review_comment_message"]
        )
    )

    st.dataframe(
        comentarios_negativos.head(100),
        use_container_width=True
    )

    st.divider()

    # ========================================================
    # COMENTÁRIOS POSITIVOS
    # ========================================================

    st.subheader(
        "Comentários Positivos"
    )

    comentarios_positivos = (
        df_filtrado[
            df_filtrado["sentimento_texto"]
            == "Positivo"
        ][
            [
                "customer_state",
                "review_score",
                "review_comment_message"
            ]
        ]
        .dropna(
            subset=["review_comment_message"]
        )
    )

    st.dataframe(
        comentarios_positivos.head(100),
        use_container_width=True
    )

# ============================================================
# ABA 4 — MAPA DE SENTIMENTOS
# ============================================================

with abas[4]:

    st.header(
        "Mapa de Sentimentos"
    )

    st.write("""
    O mapa mostra a localização aproximada dos clientes e
    destaca o sentimento predominante dos comentários em
    cada região.
    """)

    vendas_local = (
        df_filtrado
        .groupby(
            "customer_zip_code_prefix"
        )
        .agg(
            pedidos=(
                "order_id",
                "nunique"
            ),
            sentimento_predominante=(
                "sentimento_texto",
                sentimento_predominante_seguro
            ),
            nota_media=(
                "review_score",
                "mean"
            )
        )
        .reset_index()
    )

    mapa = vendas_local.merge(
        geo_resumo,
        left_on="customer_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left"
    )

    mapa = mapa.dropna(
        subset=[
            "lat",
            "lon"
        ]
    )

    cores_sentimentos = {
        "Positivo": "#1505F8",
        "Neutro": "#CFB85B",
        "Negativo": "#E74C3C",
        "Sem comentário": "#999999"
    }

    fig = px.scatter_mapbox(
        mapa,
        lat="lat",
        lon="lon",
        color="sentimento_predominante",
        color_discrete_map=cores_sentimentos,
        size="pedidos",
        hover_name="customer_zip_code_prefix",
        hover_data={
            "pedidos": True,
            "nota_media": ":.2f",
            "sentimento_predominante": True,
            "lat": False,
            "lon": False
        },
        zoom=3,
        height=600,
        title="Mapa de Sentimentos dos Clientes"
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 0
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    sentimento_estado = (
        df_filtrado
        .groupby("customer_state")
        .agg(
            pedidos=(
                "order_id",
                "nunique"
            ),
            nota_media=(
                "review_score",
                "mean"
            ),
            sentimento_predominante=(
                "sentimento_texto",
                sentimento_predominante_seguro
            )
        )
        .sort_values(
            "nota_media",
            ascending=False
        )
        .reset_index()
    )

    st.subheader(
        "Sentimento predominante por estado"
    )

    st.dataframe(
        sentimento_estado,
        use_container_width=True
    )

    st.subheader(
        "Quantidade de sentimentos por estado"
    )

    tabela_sentimentos = pd.crosstab(
        df_filtrado["customer_state"],
        df_filtrado["sentimento_texto"]
    )

    st.dataframe(
        tabela_sentimentos,
        use_container_width=True
    )


# ============================================================
# ABA 5 — RECOMENDAÇÕES
# ============================================================

with abas[5]:

    st.header(
        "Recomendações Consultivas"
    )

    estado_pior = (
        df_filtrado
        .groupby(
            "customer_state"
        )["review_score"]
        .mean()
        .sort_values()
        .head(1)
    )

    estado_melhor = (
        df_filtrado
        .groupby(
            "customer_state"
        )["review_score"]
        .mean()
        .sort_values(
            ascending=False
        )
        .head(1)
    )

    st.subheader(
        "Diagnóstico"
    )

    if not estado_pior.empty:

        st.write(
            f"O estado com pior avaliação média foi "
            f"**{estado_pior.index[0]}**, "
            f"com nota média de "
            f"**{estado_pior.iloc[0]:.2f}**."
        )

    if not estado_melhor.empty:

        st.write(
            f"O estado com melhor avaliação média foi "
            f"**{estado_melhor.index[0]}**, "
            f"com nota média de "
            f"**{estado_melhor.iloc[0]:.2f}**."
        )

    sentimento_geral = (
        df_filtrado[
            "sentimento_texto"
        ]
        .value_counts()
    )

    st.write(
        "Distribuição geral dos sentimentos "
        "nos comentários:"
    )

    st.dataframe(
        sentimento_geral,
        use_container_width=True
    )

    st.subheader(
        "Recomendações"
    )

    st.markdown("""
    1. **Priorizar a redução de atrasos nas entregas**,
       pois a experiência logística influencia diretamente
       a percepção do cliente e pode reduzir a nota média.

    2. **Monitorar os estados com menor avaliação média**,
       criando planos de ação específicos para regiões com
       maior insatisfação.

    3. **Analisar os comentários negativos com frequência**,
       pois eles ajudam a identificar problemas reais relatados
       pelos clientes, como atraso, defeito, erro no pedido
       ou má experiência de compra.

    4. **Comparar nota e sentimento do comentário**,
       verificando se avaliações baixas também apresentam
       textos negativos.

    5. **Acompanhar mensalmente vendas, notas e sentimentos**,
       para entender se o crescimento da receita está
       acompanhado de uma boa experiência do cliente.

    6. **Transformar avaliações negativas em ações de melhoria**,
       utilizando os comentários como fonte para corrigir
       problemas logísticos, operacionais e de atendimento.
    """)

    st.success("""
    Conclusão: o desempenho comercial da Olist não deve ser
    avaliado apenas pelas vendas.

    A análise mostra que entrega, nota e sentimento dos
    comentários precisam ser acompanhados juntos, pois a
    satisfação do cliente impacta diretamente a reputação
    e a qualidade da operação.
    """)
# ============================================================
# ABA 6 — DADOS
# ============================================================

with abas[6]:

    st.header(
        "Base de Dados Filtrada"
    )

    st.write(
        f"Total de linhas: {len(df_filtrado):,}"
    )

    st.dataframe(
        df_filtrado.head(1000),
        use_container_width=True
    )
    # ============================================================
# ABA 7 — ASSISTENTE IA
# ============================================================

with abas[7]:

    st.header("🤖 Assistente IA — Pergunte aos Dados")

    st.write(
        "Faça perguntas em linguagem natural sobre os dados "
        "filtrados no painel. Exemplos: *'qual estado tem mais "
        "atraso?'*, *'resuma os principais problemas relatados'*."
    )

    @st.cache_resource
    def get_client():
        chave = os.getenv("GROQ_API_KEY")
        if not chave:
            st.error(
                "GROQ_API_KEY não encontrada. Crie um arquivo .env na pasta ")
            st.stop()
        return Groq(api_key=chave)

    def montar_contexto_olist(df):
        total_pedidos = df["order_id"].nunique()
        faturamento = df["payment_value"].sum()
        nota_media = df["review_score"].mean()
        taxa_atraso = df["atrasou"].mean() * 100

        por_estado = (
            df.groupby("customer_state")
            .agg(
                pedidos=("order_id", "nunique"),
                nota_media=("review_score", "mean"),
                taxa_atraso=("atrasou", "mean")
            )
            .sort_values("pedidos", ascending=False)
            .head(10)
        )

        por_cidade = (
            df.groupby("customer_city")
            .agg(
                pedidos=("order_id", "nunique"),
                taxa_atraso=("atrasou", "mean")
            )
            .sort_values("pedidos", ascending=False)
            .head(10)
        ) if "customer_city" in df.columns else None

        sentimentos = df["sentimento_texto"].value_counts()

        reclamacoes = (
            df["categoria_reclamacao"]
            .value_counts()
            .head(10)
        )

        contexto = f"""
RESUMO GERAL DO PAINEL (dados já filtrados pelo usuário):
- Total de pedidos: {total_pedidos:,}
- Faturamento total: R$ {faturamento:,.2f}
- Nota média de avaliação: {nota_media:.2f} (escala 1-5)
- Taxa de atraso na entrega: {taxa_atraso:.1f}%

TOP 10 ESTADOS POR VOLUME DE PEDIDOS:
{por_estado.to_string()}

TOP 10 CIDADES POR VOLUME DE PEDIDOS (com taxa de atraso):
{por_cidade.to_string() if por_cidade is not None else "não disponível"}

DISTRIBUIÇÃO DE SENTIMENTOS NOS COMENTÁRIOS:
{sentimentos.to_string()}

TOP CATEGORIAS DE RECLAMAÇÃO:
{reclamacoes.to_string()}
"""
        return contexto

    # ------------------------------------------------------------
    # FERRAMENTA: consulta real no dataframe filtrado (não só resumo)
    # ------------------------------------------------------------

    COLUNAS_PERMITIDAS = [
        # Localização
        "customer_state", "customer_city", "customer_zip_code_prefix",
        # Pedido
        "order_id", "order_status", "order_purchase_timestamp",
        "order_delivered_customer_date", "order_estimated_delivery_date",
        # Entrega
        "atrasou", "dias_atraso", "dias_entrega",
        "distancia_capital_km", "distancia_origem_cliente_km",
        # Pagamento
        "payment_value", "payment_type", "payment_installments", "freight_value",
        # Avaliação / sentimento
        "review_score", "sentimento_texto",
        # Reclamações
        "categoria_reclamacao", "eh_reclamacao", "confianca_reclamacao",
        # Produto
        "product_category_name", "categoria_produto",
        # Tempo
        "mes", "mes_texto", "ano_mes"
    ]

    def consultar_dados(
        df,
        coluna_groupby=None,
        coluna_valor=None,
        agregacao="mean",
        coluna_filtro=None,
        valor_filtro=None,
        ordenar_desc=True,
        top_n=15
    ):
        """
        Executa uma consulta controlada (não é SQL/código livre) no
        dataframe filtrado do painel. O modelo escolhe os parâmetros,
        nunca escreve código diretamente — isso evita execução de
        código arbitrário vindo da IA.
        """
        dados = df.copy()

        # Filtro opcional (ex: só um estado, só pedidos atrasados)
        if coluna_filtro and coluna_filtro in dados.columns and valor_filtro is not None:
            dados = dados[
                dados[coluna_filtro].astype(str).str.lower()
                == str(valor_filtro).lower()
            ]

        if dados.empty:
            return "Nenhum dado encontrado com esse filtro."

        # Sem agrupamento: retorna estatísticas gerais da coluna pedida
        if not coluna_groupby:
            if coluna_valor and coluna_valor in dados.columns:
                serie = dados[coluna_valor]
                if pd.api.types.is_numeric_dtype(serie):
                    return serie.describe().to_string()
                return serie.value_counts().head(top_n).to_string()
            return f"Total de linhas encontradas: {len(dados)}"

        if coluna_groupby not in dados.columns:
            return f"Coluna '{coluna_groupby}' não existe nos dados."

        # Agrupamento + agregação
        if coluna_valor and coluna_valor in dados.columns:
            if agregacao == "count" or coluna_valor == "order_id":
                resultado = dados.groupby(coluna_groupby)[coluna_valor].nunique()
            else:
                resultado = dados.groupby(coluna_groupby)[coluna_valor].agg(agregacao)
        else:
            resultado = dados.groupby(coluna_groupby).size()

        resultado = resultado.sort_values(ascending=not ordenar_desc).head(top_n)
        return resultado.to_string()

    FERRAMENTAS = [
        {
            "type": "function",
            "function": {
                "name": "consultar_dados",
                "description": (
                    "Consulta os dados reais e filtrados do painel Olist "
                    "(não apenas o resumo). Use sempre que a pergunta pedir "
                    "algo mais específico do que o resumo geral fornece: "
                    "uma cidade, um estado específico, uma categoria de "
                    "produto, um tipo de pagamento, uma faixa de tempo, "
                    "uma agregação diferente, um top N diferente de 10, "
                    "cruzamento entre atraso e nota, etc. Pode ser chamada "
                    "várias vezes seguidas com parâmetros diferentes até "
                    "reunir informação suficiente para responder."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coluna_groupby": {
                            "type": "string",
                            "description": f"Coluna para agrupar. Uma de: {COLUNAS_PERMITIDAS}"
                        },
                        "coluna_valor": {
                            "type": "string",
                            "description": f"Coluna a analisar/agregar. Uma de: {COLUNAS_PERMITIDAS}"
                        },
                        "agregacao": {
                            "type": "string",
                            "enum": ["mean", "sum", "count", "median", "min", "max"],
                            "description": "Tipo de agregação a aplicar"
                        },
                        "coluna_filtro": {
                            "type": "string",
                            "description": f"Coluna para filtrar antes de agregar. Uma de: {COLUNAS_PERMITIDAS}"
                        },
                        "valor_filtro": {
                            "type": "string",
                            "description": "Valor exato a filtrar nessa coluna (ex: 'SP', 'Positivo')"
                        },
                        "ordenar_desc": {
                            "type": "string",
                            "description": "Se deve ordenar do maior para o menor. Responda 'true' ou 'false'."
                        },
                        "top_n": {
                            "type": "string",
                            "description": "Quantas linhas retornar (padrão 15). Responda apenas com o número, ex: '15'."
                        }
                    }
                }
            }
        }
    ]

    def perguntar_ia(pergunta, contexto, df):
        client = get_client()

        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é um analista de BI especializado em e-commerce. "
                    "Responda em português, de forma clara e objetiva. "
                    "Você recebe um RESUMO GERAL abaixo, mas também pode "
                    "chamar a ferramenta 'consultar_dados' quantas vezes "
                    "precisar para consultar os dados reais e filtrados "
                    "quando o resumo não for suficiente para responder "
                    "com precisão. Nunca invente números — se não conseguir "
                    "obter o dado, diga isso claramente.\n\n"
                    f"RESUMO GERAL:\n{contexto}"
                )
            },
            {"role": "user", "content": pergunta}
        ]

        # Loop de function calling: o modelo pode pedir consultas
        # várias vezes antes de dar a resposta final.
        for _ in range(6):
            resposta = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                max_tokens=800,
                messages=mensagens,
                tools=FERRAMENTAS,
                tool_choice="auto"
            )

            msg = resposta.choices[0].message

            if not msg.tool_calls:
                return msg.content

            mensagens.append(msg)

            for chamada in msg.tool_calls:
                import json
                args = json.loads(chamada.function.arguments)
                if "ordenar_desc" in args and isinstance(args["ordenar_desc"], str):
                    args["ordenar_desc"] = args["ordenar_desc"].strip().lower() in ("true", "1", "sim")
                if "top_n" in args and isinstance(args["top_n"], str) and args["top_n"].strip().isdigit():
                    args["top_n"] = int(args["top_n"])
                resultado = consultar_dados(
                    df,
                    coluna_groupby=args.get("coluna_groupby"),
                    coluna_valor=args.get("coluna_valor"),
                    agregacao=args.get("agregacao", "mean"),
                    coluna_filtro=args.get("coluna_filtro"),
                    valor_filtro=args.get("valor_filtro"),
                    ordenar_desc=args.get("ordenar_desc", True),
                    top_n=args.get("top_n", 15)
                )
                mensagens.append({
                    "role": "tool",
                    "tool_call_id": chamada.id,
                    "content": resultado
                })

        return "Não consegui concluir a consulta. Tenta reformular a pergunta."

    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = []

    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pergunta_usuario = st.chat_input(
        "Digite sua pergunta sobre os dados filtrados..."
    )

    if pergunta_usuario:
        st.session_state.historico_chat.append(
            {"role": "user", "content": pergunta_usuario}
        )
        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        with st.chat_message("assistant"):
            with st.spinner("Analisando os dados..."):
                contexto = montar_contexto_olist(df_filtrado)
                resposta = perguntar_ia(pergunta_usuario, contexto, df_filtrado)
                st.markdown(resposta)

        st.session_state.historico_chat.append(
            {"role": "assistant", "content": resposta}
        )

    if st.button("Limpar conversa"):
        st.session_state.historico_chat = []
        st.rerun()