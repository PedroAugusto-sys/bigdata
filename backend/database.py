from pymongo import MongoClient

# Conexão com o MongoDB Atlas (substitua pela sua URL)
client = MongoClient("mongodb+srv://<usuario>:<senha>@cluster0.mongodb.net/tech_trends?retryWrites=true&w=majority")
db = client["tech_trends"]
collection = db["jobs"]  # Coleção para vagas de tecnologia