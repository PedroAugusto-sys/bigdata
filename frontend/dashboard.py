import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


# Funções auxiliares para formatação de datas
def formatar_data_brasil(data):
    """Formata datetime para string DD/MM/AAAA"""
    return data.strftime("%d/%m/%Y")

def parse_data_brasil(data_str):
    """Converte string DD/MM/AAAA para datetime"""
    try:
        return datetime.strptime(data_str, "%d/%m/%Y")
    except ValueError:
        return None

# Configuração inicial
st.set_page_config(
    page_title="Dashboard Educacional 2.0",
    layout="wide",
    page_icon="📚"
)

# Título principal
st.title("📚 Dashboard Educacional Completo")

# Sidebar com filtros globais
with st.sidebar:
    st.header("⚙️ Filtros Globais")
    
    # Data padrão: últimos 30 dias
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=31)
    
    # Widget com formato brasileiro
    col1, col2 = st.columns(2)
    with col1:
        data_inicio_str = st.text_input(
            "Data inicial (DD/MM/AAAA)",
            value=formatar_data_brasil(data_inicio),
            max_chars=10,
            key="data_inicio"
        )
    with col2:
        data_fim_str = st.text_input(
            "Data final (DD/MM/AAAA)",
            value=formatar_data_brasil(data_fim),
            max_chars=10,
            key="data_fim"
        )
    
    # Validação e conversão
    datas_validas = True
    data_inicio = parse_data_brasil(data_inicio_str)
    data_fim = parse_data_brasil(data_fim_str)
    
    if not data_inicio or not data_fim:
        st.error("Formato inválido! Use DD/MM/AAAA")
        datas_validas = False
    elif data_inicio > data_fim:
        st.error("Data inicial maior que final!")
        datas_validas = False
    
    st.markdown("---")
    
    # Filtro de disciplinas
    try:
        subjects = requests.get("http://localhost:8000/performance", timeout=5).json()
        unique_subjects = list(set([item.get("Subject") for item in subjects if isinstance(item, dict) and "Subject" in item]))
        selected_subjects = st.multiselect(
            "Disciplinas",
            options=unique_subjects,
            default=unique_subjects[:2] if unique_subjects else []
        )
    except Exception as e:
        st.error(f"Erro ao carregar disciplinas: {str(e)}")
        selected_subjects = []
    
    st.markdown("---")
    st.markdown(f"🔄 Atualizado em: {formatar_data_brasil(datetime.now())} {datetime.now().strftime('%H:%M')}")

# Função para buscar dados da API
@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def fetch_api_data(endpoint, params=None):
    try:
        response = requests.get(
            f"http://localhost:8000{endpoint}", 
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro na requisição para {endpoint}: {str(e)}")
        return None

# -------------------------
# Seção 1: Visão Geral
# -------------------------
st.header("📊 Visão Geral")

# Dados resumidos
summary_data = fetch_api_data("/dashboard/summary")

if summary_data:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        present = next((x.get("count", 0) for x in summary_data.get("attendance_stats", []) if x.get("_id") == "Present"), 0)
        st.metric("Presenças", f"{present:,}")
    
    with col2:
        completed = next((x.get("count", 0) for x in summary_data.get("homework_status", []) if x.get("_id") == "✅"), 0)
        st.metric("Tarefas Concluídas", f"{completed:,}")
    
    with col3:
        st.metric("Comunicações Recentes", len(summary_data.get("recent_comms", [])))

# -------------------------
# Seção 2: Frequência
# -------------------------
st.header("📅 Análise de Frequência")

if datas_validas:
    attendance_params = {
        "date_start": data_inicio.strftime("%Y-%m-%d"),
        "date_end": data_fim.strftime("%Y-%m-%d")
    }
    attendance_data = fetch_api_data("/attendance", attendance_params)
    
    if attendance_data:
        df_attendance = pd.DataFrame(attendance_data)
        
        if not df_attendance.empty:
            # Gráfico de frequência por disciplina
            fig_attendance = px.bar(
                df_attendance.groupby(["Subject", "Attendance_Status"]).size().unstack(fill_value=0),
                barmode="group",
                title="Frequência por Disciplina",
                labels={"value": "Quantidade"}
            )
            st.plotly_chart(fig_attendance, use_container_width=True)
            
            # Heatmap de frequência
            df_attendance["Date"] = pd.to_datetime(df_attendance["Date"])
            df_attendance["Day"] = df_attendance["Date"].dt.day_name()
            
            fig_heatmap = px.density_heatmap(
                df_attendance,
                x="Day",
                y="Subject",
                z="Attendance_Status",
                histfunc="count",
                title="Distribuição de Frequência por Dia",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.warning(f"Nenhum registro de frequência encontrado entre {data_inicio_str} e {data_fim_str}")
else:
    st.warning("Selecione um intervalo de datas válido para visualizar a frequência")

# -------------------------
# Seção 3: Desempenho Acadêmico
# -------------------------
st.header("📊 Desempenho Acadêmico")

# Container principal com abas
tab1, tab2 = st.tabs(["📝 Notas por Disciplina", "📈 Relação Notas-Tarefas"])

with tab1:
    st.subheader("Distribuição de Notas")
    performance_data = fetch_api_data("/performance", {"subject": selected_subjects[0] if selected_subjects else None})
    
    if performance_data:
        df_performance = pd.DataFrame(performance_data)
        
        if "Exam_Score" in df_performance.columns:
            fig = px.box(
                df_performance,
                x="Subject",
                y="Exam_Score",
                title="Distribuição de Notas por Disciplina",
                color="Subject",
                labels={"Exam_Score": "Nota do Exame"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas resumidas
            st.subheader("Estatísticas por Disciplina")
            stats_df = df_performance.groupby("Subject")["Exam_Score"].agg(['mean', 'median', 'std', 'count'])
            stats_df.columns = ['Média', 'Mediana', 'Desvio Padrão', 'Alunos']
            st.dataframe(stats_df.style.format("{:.1f}"), use_container_width=True)
        else:
            st.warning("Dados de notas não disponíveis")

with tab2:
    st.subheader("Relação Entre Notas e Tarefas")
    
    # Verificação se há disciplinas selecionadas
    if not selected_subjects:
        st.warning("Selecione pelo menos uma disciplina nos filtros globais")
        st.stop()
    
    # Busca dados de homework completion
    hw_data = fetch_api_data("/performance/homework-completion", {
        "subject": selected_subjects[0],
        "min_percentage": 0
    })
    
    # Busca dados de performance
    perf_data = fetch_api_data("/performance", {
        "subject": selected_subjects[0]
    })
    
    if hw_data and perf_data:
        df_hw = pd.DataFrame(hw_data)
        df_perf = pd.DataFrame(perf_data)
        
        # Combina os dados manualmente
        df_combined = pd.merge(
            df_perf[['Student_ID', 'Subject', 'Exam_Score']],
            df_hw[['Student_ID', 'Subject', 'Homework_Completion']],
            on=['Student_ID', 'Subject'],
            how='inner'
        )
        
        if not df_combined.empty:
            # Gráfico de dispersão
            fig = px.scatter(
                df_combined,
                x="Homework_Completion",
                y="Exam_Score",
                color="Student_ID",
                trendline="ols",
                title=f"Relação Notas x Tarefas - {selected_subjects[0]}",
                labels={
                    "Homework_Completion": "% Conclusão de Tarefas",
                    "Exam_Score": "Nota do Exame"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Cálculo da correlação
            correlation = df_combined["Exam_Score"].corr(df_combined["Homework_Completion"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Correlação", f"{correlation:.2f}", 
                         delta="Forte" if abs(correlation) > 0.5 else "Moderada" if abs(correlation) > 0.3 else "Fraca")
            
            with col2:
                st.metric("Alunos na análise", len(df_combined))
            
            # Tabela com dados combinados
            st.subheader("Dados Completos")
            st.dataframe(
                df_combined,
                column_config={
                    "Homework_Completion": st.column_config.ProgressColumn(
                        "% Concluído",
                        format="%d%%",
                        min_value=0,
                        max_value=100
                    )
                },
                hide_index=True
            )
        else:
            st.warning("Nenhum aluno com dados completos de notas e tarefas")
    else:
        if not hw_data:
            st.error("Falha ao carregar dados de conclusão de tarefas")
        if not perf_data:
            st.error("Falha ao carregar dados de desempenho")

# -------------------------
# Seção 3.5: Conclusão de Tarefas (Nova!)
# -------------------------
st.header("✅ Conclusão de Tarefas")

# Filtros específicos para esta seção
with st.expander("🔍 Filtros Avançados", expanded=False):
    min_completion = st.slider(
        "Mínimo de conclusão (%)", 
        min_value=0, 
        max_value=100, 
        value=70,
        key="min_completion"
    )
    subject_filter = st.selectbox(
        "Filtrar por disciplina",
        options=unique_subjects if 'unique_subjects' in locals() else [],
        index=0,
        key="hw_subject_filter"
    )

# Busca dados do novo endpoint
hw_completion_data = fetch_api_data(
    "/performance/homework-completion",
    params={
        "min_percentage": min_completion,
        "subject": subject_filter if subject_filter != "Todas" else None
    }
)

if hw_completion_data:
    df_hw_completion = pd.DataFrame(hw_completion_data)
    
    # Gráfico de distribuição
    fig_dist = px.histogram(
        df_hw_completion,
        x="Homework_Completion",
        nbins=20,
        title=f"Distribuição de Conclusão (≥{min_completion}%)",
        labels={"Homework_Completion": "% de Conclusão"}
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Top alunos
    st.subheader("🏆 Melhores Alunos")
    top_students = df_hw_completion.sort_values("Homework_Completion", ascending=False).head(5)
    st.dataframe(
        top_students[["Student_ID", "Subject", "Homework_Completion", "Teacher_Comments"]],
        column_config={
            "Homework_Completion": st.column_config.ProgressColumn(
                "% Concluído",
                format="%d%%",
                min_value=0,
                max_value=100
            ),
            "Teacher_Comments": "Comentários"
        },
        hide_index=True
    )
    
    # Análise por disciplina
    if len(df_hw_completion['Subject'].unique()) > 1:
        fig_subject = px.box(
            df_hw_completion,
            x="Subject",
            y="Homework_Completion",
            title="Conclusão por Disciplina"
        )
        st.plotly_chart(fig_subject, use_container_width=True)
else:
    st.warning("Nenhum dado encontrado com os filtros selecionados")




# -------------------------
# Seção 4: Tarefas
# -------------------------
st.header("📚 Status das Tarefas")

homework_data = fetch_api_data("/homework", {"subject": selected_subjects[0] if selected_subjects else None})

if homework_data:
    df_homework = pd.DataFrame(homework_data)
    
    # Gráfico de status das tarefas
    fig_homework_status = px.pie(
        df_homework,
        names="Status",
        title="Proporção de Status das Tarefas",
        hole=0.4
    )
    st.plotly_chart(fig_homework_status, use_container_width=True)
    
    # Tabela de tarefas recentes
    st.subheader("Últimas Tarefas")
    st.dataframe(
        df_homework.sort_values("Due_Date", ascending=False).head(5),
        hide_index=True,
        column_config={
            "Due_Date": st.column_config.DateColumn("Data de Entrega"),
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )

# -------------------------
# Seção 5: Comunicação
# -------------------------
st.header("📨 Comunicação Pais-Professores")

comms_data = fetch_api_data("/communications", {"last_days": 30})

if comms_data:
    df_comms = pd.DataFrame(comms_data)
    
    # Gráfico de tipos de mensagem
    fig_comms = px.bar(
        df_comms["Message_Type"].value_counts(),
        orientation="h",
        title="Tipos de Comunicação",
        labels={"value": "Quantidade", "index": "Tipo"}
    )
    st.plotly_chart(fig_comms, use_container_width=True)
    
    # Últimas comunicações
    st.subheader("Registros Recentes")
    for _, row in df_comms.head(3).iterrows():
        with st.expander(f"{row.get('Date', 'N/D')} - {row.get('Message_Type', 'N/D')}"):
            st.write(row.get("Message_Content", "Sem conteúdo disponível"))

# -------------------------
# Rodapé
# -------------------------
st.markdown("---")
st.caption("Dashboard desenvolvido para análise educacional - Dados atualizados em tempo real")