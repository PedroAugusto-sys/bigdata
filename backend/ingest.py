import os
import sys
import io
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import BulkWriteError, ConnectionFailure, OperationFailure

# Configuração para evitar erros de encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurações do MongoDB
uri = "mongodb+srv://gabrielsales012345:<db_password>@gabrielsales.vlmptyd.mongodb.net/?retryWrites=true&w=majority&appName=GabrielSales"
DB_NAME = "tech_trends"

# Caminho relativo (a partir da raiz do projeto)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")  # Pasta 'data' na mesma pasta do script

def test_connection():
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("✅ Conexão com o MongoDB Atlas bem-sucedida!")
        return client
    except OperationFailure as e:
        print(f"❌ Erro de autenticação: {e.details['errmsg']}")
        return None
    except ConnectionFailure as e:
        print(f"❌ Falha na conexão: {str(e)}")
        return None

def ingest_csv_to_mongodb(client):
    try:
        # Verifica se a pasta existe
        if not os.path.exists(DATA_DIR):
            raise FileNotFoundError(f"Pasta 'data' não encontrada em: {os.path.abspath(DATA_DIR)}")
        
        print(f"📂 Pasta de dados: {os.path.abspath(DATA_DIR)}")
        print(f"📝 Arquivos encontrados: {os.listdir(DATA_DIR)}")
        
        db = client[DB_NAME]
        
        for filename in sorted(os.listdir(DATA_DIR)):  # Ordena os arquivos
            if filename.endswith(".csv"):
                csv_path = os.path.join(DATA_DIR, filename)
                collection_name = os.path.splitext(filename)[0]
                
                try:
                    print(f"\n🔍 Processando: {filename}")
                    df = pd.read_csv(csv_path)
                    print(f"📊 Registros no arquivo: {len(df)}")
                    
                    # Pré-processamento
                    df = df.dropna().reset_index(drop=True)
                    df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
                    
                    # Conversão e inserção
                    data = df.to_dict("records")
                    result = db[collection_name].insert_many(data)
                    print(f"✅ Inseridos em '{collection_name}': {len(result.inserted_ids)} registros")
                    
                except pd.errors.EmptyDataError:
                    print(f"⚠️ Arquivo vazio: {filename}")
                except Exception as e:
                    print(f"⚠️ Erro no arquivo {filename}: {str(e)}")
                    
    except Exception as e:
        print(f"🔥 Erro crítico: {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" INGESTÃO DE DADOS - MONGODB ".center(50, "~"))
    print("="*50 + "\n")
    
    mongo_client = test_connection()
    
    if mongo_client:
        try:
            ingest_csv_to_mongodb(mongo_client)
        except KeyboardInterrupt:
            print("\n⛔ Processo interrompido pelo usuário")
        finally:
            mongo_client.close()
            print("\n🔌 Conexão encerrada")
            print("="*50)