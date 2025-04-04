from http.client import HTTPException
from fastapi import FastAPI, Query
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional


load_dotenv()

app = FastAPI(
    title="API de Análise Educacional",
    description="API para acesso aos dados do MongoDB (Performance, Frequência, Tarefas, etc.)",
    version="2.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão com o MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["tech_trends"]

# --- Endpoints Originais (Mantidos) ---
@app.get("/performance")
def get_performance(
    min_exam: Optional[int] = None, 
    subject: Optional[str] = None,
    limit: int = 100
):
    """Retorna dados de desempenho com filtros (original)"""
    query = {}
    if min_exam:
        query["Exam_Score"] = {"$gte": min_exam}
    if subject:
        query["Subject"] = subject
    
    projection = {"_id": 0, "Student_ID": 1, "Subject": 1, "Exam_Score": 1}
    return list(db.performance.find(query, projection).limit(limit))

# --- Novos Endpoints para as Coleções Adicionais ---

# 1. Endpoint para Frequência (attendance)
@app.get("/attendance")
def get_attendance(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(Present|Absent)$")
):
    """Retorna dados de frequência com filtros por data/status"""
    query = {}
    if date_start and date_end:
        query["Date"] = {"$gte": date_start, "$lte": date_end}
    if status:
        query["Attendance_Status"] = status
    
    return list(db.attendance.find(query, {"_id": 0}).limit(500))

# 2. Endpoint para Tarefas (homework)
@app.get("/homework")
def get_homework(
    subject: Optional[str] = None,
    status: Optional[str] = None,
    grade: Optional[str] = None
):
    """Filtra tarefas por disciplina/status/nota"""
    query = {}
    if subject:
        query["Subject"] = subject
    if status:
        query["Status"] = status
    if grade:
        query["Grade_Feedback"] = {"$regex": f"^{grade}"}
    
    projection = {"_id": 0, "Due_Date": 1, "Subject": 1, "Status": 1}
    return list(db.homework.find(query, projection).limit(200))

# 3. Endpoint para Dados de Alunos (students)
@app.get("/students")
def get_students(
    grade_level: Optional[str] = None,
    emergency_contact: bool = False
):
    """Lista alunos com filtro por nível escolar"""
    query = {}
    if grade_level:
        query["Grade_Level"] = grade_level
    
    projection = {"_id": 0, "Student_ID": 1, "Full_Name": 1}
    if emergency_contact:
        projection["Emergency_Contact"] = 1
    
    return list(db.students.find(query, projection))

# 4. Endpoint para Comunicação (teacher_parent_communication)
@app.get("/communications")
def get_communications(
    message_type: Optional[str] = None,
    last_days: Optional[int] = 30
):
    """Filtra comunicações por tipo e recência"""
    query = {}
    if message_type:
        query["Message_Type"] = message_type
    
    if last_days:
        cutoff_date = datetime.now() - timedelta(days=last_days)
        query["Date"] = {"$gte": cutoff_date.isoformat()}
    
    return list(db.teacher_parent_communication.find(query, {"_id": 0}).limit(100))



@app.get("/performance/homework-completion")
def get_homework_completion(
    min_percentage: Optional[int] = Query(None, ge=0, le=100, description="Filtro por % mínimo de conclusão (0-100)"),
    subject: Optional[str] = None,
    limit: int = 100
):
    """
    Retorna a porcentagem de conclusão de tarefas (armazenada na coleção performance)
    Filtros:
    - min_percentage: % mínimo de conclusão (ex: 80 para buscar >=80%)
    - subject: Filtrar por disciplina específica
    """
    query = {}
    
    if min_percentage is not None:
        query["Homework_Completion_%"] = {
            "$regex": f"^{min_percentage}|^[1-9][0-9]%|^100%"
        }
    
    if subject:
        query["Subject"] = subject
    
    projection = {
        "_id": 0,
        "Student_ID": 1,
        "Subject": 1,
        "Homework_Completion_%": 1,
        "Teacher_Comments": 1
    }
    
    try:
        results = list(db.performance.find(query, projection).limit(limit))
        
        # Converte "%" para número (opcional)
        for item in results:
            item["Homework_Completion"] = int(item["Homework_Completion_%"].replace('%', ''))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/combined-analysis")
async def get_combined_analysis(
    subject: Optional[str] = None,
    min_completion: Optional[int] = 0
):
    """Endpoint que combina dados de performance e homework completion"""
    try:
        # Pipeline de agregação
        pipeline = [
            # Estágio 1: Filtro por disciplina (se fornecido)
            {"$match": {"Subject": subject}} if subject else {"$match": {}},
            
            # Estágio 2: Join com a coleção de homework completion
            {"$lookup": {
                "from": "homework_completion",
                "localField": "Student_ID",
                "foreignField": "Student_ID",
                "as": "homework_data"
            }},
            
            # Estágio 3: Desnormaliza o array resultante do lookup
            {"$unwind": "$homework_data"},
            
            # Estágio 4: Filtro por porcentagem mínima
            {"$match": {"homework_data.Completion_Percentage": {"$gte": min_completion}}},
            
            # Estágio 5: Projeção final
            {"$project": {
                "_id": 0,
                "Student_ID": 1,
                "Subject": 1,
                "Exam_Score": 1,
                "Homework_Completion": "$homework_data.Completion_Percentage",
                "Last_Update": "$homework_data.Date"
            }}
        ]
        
        # Executa a agregação
        results = list(db.performance.aggregate(pipeline))
        
        if not results:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado com os filtros fornecidos")
            
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# Novo endpoint no FastAPI
@app.get("/performance/combined")
def get_combined_data(
    subject: Optional[str] = None,
    min_completion: int = 0
):
    # Pipeline de agregação
    pipeline = [
        {"$match": {"Subject": subject}} if subject else {"$match": {}},
        {"$lookup": {
            "from": "homework_completion",
            "localField": "Student_ID",
            "foreignField": "Student_ID",
            "as": "hw_data"
        }},
        {"$unwind": "$hw_data"},
        {"$project": {
            "Student_ID": 1,
            "Subject": 1,
            "Exam_Score": 1,
            "Homework_Completion": "$hw_data.Completion_Percentage"
        }},
        {"$match": {"Homework_Completion": {"$gte": min_completion}}}
    ]
    
    results = list(db.performance.aggregate(pipeline))
    return results

# --- Endpoint Combinado para Dashboard ---
@app.get("/dashboard/summary")
def get_dashboard_summary():
    """Agrega dados para o dashboard principal"""
    pipeline = [
        {"$facet": {
            "attendance_stats": [
                {"$group": {
                    "_id": "$Attendance_Status",
                    "count": {"$sum": 1}
                }}
            ],
            "homework_status": [
                {"$group": {
                    "_id": "$Status",
                    "count": {"$sum": 1}
                }}
            ],
            "recent_comms": [
                {"$sort": {"Date": -1}},
                {"$limit": 5},
                {"$project": {"_id": 0, "Student_ID": 1, "Date": 1}}
            ]
        }}
    ]
    
    return db.attendance.aggregate(pipeline).next()