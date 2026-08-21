# Guia de Agentes IA — projeto_consultoria

## Visão Geral

**Projeto**: Consultoria de BI para dataset OLIST (e-commerce brasileiro)

**Stack**: Python (Streamlit + FastAPI + Jupyter + Quarto)

**Propósito**: Análise exploratória, regressão GLM/MLG, dashboards interativos e API de cálculos.

---

## 📁 Estrutura do Projeto

```
projeto_consultoria/
├── app.py                          # Streamlit dashboard (principal, com IA integrada)
├── appnovo (1).py                  # Alternativa melhorada do dashboard
├── app 2 (1) - corrigido v2 *.py   # Versões anteriores (usar como referência apenas)
├── fastAPI/
│   ├── main.py                     # API FastAPI simples (3 endpoints)
│   └── exe.bat                     # Script para rodar uvicorn
├── .env                            # Variáveis de ambiente (GROQ_API_KEY) **⚠️ SEGREDO**
├── _quarto.yml                     # Configuração de projeto Quarto
├── projeto_consultoria.qmd         # Relatório Quarto
├── analise.qmd                     # Análise complementar
├── analise_exploratoria.ipynb      # Notebook Jupyter
├── processamento_bert.py           # Processamento de sentimentos (BERT)
├── olist_*_dataset.csv             # Dados OLIST (8 arquivos)
└── produto_category_name_translation.csv
```

---

## 🔑 Variáveis de Ambiente

### `.env` — Carregamento Automático via VS Code

O VS Code está configurado com `python.terminal.useEnvFile: true`. Isso significa:

- ✅ Variáveis no `.env` **são automaticamente carregadas** ao abrir um terminal Python
- ✅ `os.getenv("GROQ_API_KEY")` funcionará sem chamar `load_dotenv()`
- ✅ Não há necessidade de `python-dotenv` se usar apenas terminals VS Code
- ⚠️ Alguns apps ainda usam `from dotenv import load_dotenv` (redundante, mas funciona)

**Variáveis esperadas:**
```env
GROQ_API_KEY=gsk_...  # Chave para LLM Groq (Llama 3.3 70B)
```

**Verificar variável no terminal:**
```powershell
echo $env:GROQ_API_KEY
# Ou no código:
import os; print(os.getenv("GROQ_API_KEY"))
```

---

## 🚀 Como Rodar Cada Componente

### 1. **Streamlit Dashboard** (principal)

```bash
# Terminal Python VS Code (já tem .env carregado)
streamlit run app.py
# ou a versão alternativa melhorada:
streamlit run appnovo\ \(1\).py
```

**URL**: http://localhost:8501

**Abas principais**:
- Resumo de vendas/reclamações
- Análises estatísticas (MLG/Regressão)
- Previsão de receita
- Diagnóstico de modelos
- Assistente IA (powered by Groq)

**Recursos especiais**:
- Filtro por região/estado/período
- Regressão GLM automática (Gaussiana, Poisson, Binomial Negativa, Logística)
- AI Chat usando `consultar_dados()` como tool (acesso controlado aos dados)

### 2. **FastAPI**

```bash
cd fastAPI
python -m uvicorn main:app --reload
# Ou:
python exe.bat
```

**URL**: http://localhost:8000  
**Docs**: http://localhost:8000/docs

**Endpoints**:
- `GET /` → Status
- `GET /media?n1=10&n2=20` → Calcula média
- `POST /avaliar` → Classifica aluno por nota

### 3. **Jupyter Notebook**

```bash
jupyter notebook analise_exploratoria.ipynb
```

### 4. **Relatório Quarto**

```bash
quarto render projeto_consultoria.qmd
```

---

## 🔧 Padrões e Convenções

### Carregamento de Dados

```python
from pathlib import Path
PASTA = Path(__file__).parent

# CSV são carregados do diretório raiz:
df = pd.read_csv(PASTA / "olist_orders_dataset.csv")
```

### IA Assistant (Groq)

```python
@st.cache_resource
def get_client():
    chave = os.getenv("GROQ_API_KEY")  # Usa .env automaticamente
    if not chave:
        st.error("GROQ_API_KEY não encontrada")
        st.stop()
    return Groq(api_key=chave)

# A IA não executa código arbitrário — usa função `consultar_dados()`
# com parâmetros seguros (groupby, agregação, filtro, top_n)
```

### Modelagem (GLM/Regressão)

```python
# Pressupostos são testados automaticamente:
# - Gaussiana: Shapiro-Wilk
# - Poisson/NegBin: Dispersão
# - Logística: Hosmer-Lemeshow

# Colinearidade testada com VIF (limite: 10.0)
# AICc usado para comparação de modelos (melhor = menor AICc)
```

### Formatação de Dados

```python
def formatar_moeda(valor):
    """Exibe valor em Real (R$)"""
    pass

def percentual(serie):
    """Retorna % de cada categoria"""
    pass
```

---

## ⚠️ Pontos de Atenção

### 1. **Múltiplas Versões do App**

- `app.py` e `appnovo (1).py` são **funcionalmente similares**
- Versões `app 2 (1) - corrigido v2 *.py` são **legado** — usar como referência
- Quando editar, considerar sincronizar entre `app.py` e `appnovo (1).py` se ambas estiverem em uso

### 2. **API Key é Sensível**

- ⚠️ `.env` contém `GROQ_API_KEY` — **NUNCA commit no git**
- Arquivo `.gitignore` ignora `.quarto/` mas **deveria incluir `.env`**
- Verificar: `echo .env >> .gitignore`

### 3. **Dados Grandes**

- OLIST dataset tem múltiplos CSVs (~8MB combinados)
- Streamlit cacheia com `@st.cache_data` e `@st.cache_resource`
- Não recarregar dados a cada interação

### 4. **Colunhas Derivadas**

Apps criam colunas calculadas:
- `sentimento_texto` (análise BERT de reviews)
- `categoria_reclamacao` (classificação de tipo)
- `mes`, `ano_mes` (agregação temporal)

Verificar que estas colunas existem antes de usar em filtros/gráficos.

---

## 🛠️ Tarefas Comuns para Agentes

| Tarefa | Comando | Notas |
|--------|---------|-------|
| Rodar app Streamlit | `streamlit run app.py` | Usa `.env` automaticamente |
| Testar API | `python -m uvicorn fastAPI/main:app --reload` | Acesse `/docs` |
| Instalar deps | Buscar `import X` não encontrado → instalar com pip | Não há `requirements.txt` |
| Editar gráficos | Usar `plotly` (já importado) | Streamlit pode renderizar direto |
| Adicionar teste | Criar `test_*.py`, rodar com `pytest` | Não há teste estruturado atualmente |
| Debugar modelo | Usar `diagnostico_glm(modelo, y, familia)` | Retorna tabela de diagnóstico |

---

## 📋 Checklist para Novas Features

- [ ] Variáveis usadas existem no dataset?
- [ ] `GROQ_API_KEY` está em `.env` (não no código)?
- [ ] Dados são cacheados com `@st.cache_data` ou `@st.cache_resource`?
- [ ] Função nova usa padrão seguro (não `eval`/`exec`)?
- [ ] Sincronizar mudanças entre `app.py` e `appnovo (1).py`?
- [ ] Documentar novos parâmetros em docstrings?

---

## 🔗 Referências

- **Streamlit**: https://docs.streamlit.io
- **FastAPI**: https://fastapi.tiangolo.com
- **Groq API**: https://console.groq.com
- **statsmodels GLM**: https://www.statsmodels.org/stable/glm.html
- **OLIST Dataset**: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

---

**Última atualização**: 2026-08-16
