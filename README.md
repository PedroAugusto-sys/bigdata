# 🎓 Sistema de Análise Educacional

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.2-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25.0-red.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-5.0+-brightgreen.svg)

Solução completa para monitoramento e análise de dados educacionais com backend em FastAPI e frontend em Streamlit.

## 📋 Sumário

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Backend](#-backend)
  - [Endpoints](#endpoints)
  - [Configuração](#configuração)
- [Frontend](#-frontend)
  - [Funcionalidades](#funcionalidades)
  - [Dashboard](#dashboard)
- [ETL](#-etl)
- [Instalação](#-instalação)
- [Contribuição](#-contribuição)

## 🌐 Visão Geral

Sistema completo para análise de desempenho educacional com:

- **Backend**: API REST com FastAPI + MongoDB
- **Frontend**: Dashboard interativo com Streamlit
- **ETL**: Processamento de dados com Pandas

## 🏗 Arquitetura

```mermaid
graph TD
    A[Frontend - Streamlit] -->|GET Requests| B[Backend - FastAPI]
    B -->|Operações de Consulta| C[(MongoDB Atlas)]
    D[ETL/Ingestão] -->|Carregamento Inicial| C
    E[CSV Files] --> D
```

## ⚙️ Backend

### Estrutura de Arquivos
```
backend/
├── main.py          # API principal
├── database.py      # Conexão com MongoDB
├── ingest.py        # Ingestão de dados
├── etl_pandas.py    # Transformação de dados
└── requirements.txt # Dependências
```

### Endpoints Principais

| Endpoint | Método | Descrição | Parâmetros |
|----------|--------|-----------|------------|
| `/performance` | GET | Dados de desempenho | `min_exam`, `subject` |
| `/attendance` | GET | Registros de frequência | `date_start`, `date_end`, `status` |
| `/homework` | GET | Status de tarefas | `subject`, `status`, `grade` |
| `/students` | GET | Dados de alunos | `grade_level`, `emergency_contact` |
| `/communications` | GET | Comunicações | `message_type`, `last_days` |
| `/dashboard/summary` | GET | Dados consolidados | - |

### Configuração

1. Criar arquivo `.env`:
```ini
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/tech_trends
```

2. Instalar dependências:
```bash
pip install -r requirements.txt
```

3. Iniciar servidor:
```bash
uvicorn main:app --reload
```

## 🖥 Frontend

### Funcionalidades Principais

- 📊 Visualização de desempenho acadêmico
- 📅 Controle de frequência
- ✅ Acompanhamento de tarefas
- 📨 Monitoramento de comunicações

### Dashboard

![Dashboard Preview]([https://i.imgur.com/JQ8w5Rn.png](https://imgur.com/a/DxqKbyB))

**Seções principais:**
1. Visão geral com métricas
2. Análise de frequência
3. Desempenho por disciplina
4. Status de tarefas
5. Comunicações recentes

Para executar:
```bash
streamlit run dashboard.py
```

## 🔄 ETL

Processo de transformação de dados:

```python
# Extração
data = pd.DataFrame(list(db.performance.find()))

# Transformação
data['Final_Score'] = 0.7*data['Exam_Score'] + 0.3*data['Homework_Score']

# Load
data.to_csv("processed_data.csv")
```

Executar:
```bash
python etl_pandas.py
```

## 🚀 Instalação

1. Clonar repositório:
```bash
git clone https://github.com/seu-usuario/analise-educacional.git
```

2. Configurar ambiente:
```bash
cd analise-educacional
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

3. Instalar dependências:
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

4. Iniciar serviços:
```bash
# Backend
uvicorn backend.main:app --reload

# Frontend (outro terminal)
streamlit run frontend/dashboard.py
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes
```
