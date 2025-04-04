# etl_pandas.py - VERSÃO DEFINITIVA (GARANTIDO FUNCIONAR)
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import re
import os
import sys

def criar_caminho_confiavel():
    """Define um caminho de saída que sempre funcionará"""
    # Tenta primeiro na pasta do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "ETL_OUTPUT")
    
    # Se falhar, tenta na área de trabalho
    if not os.access(script_dir, os.W_OK):
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "ETL_OUTPUT")
    
    # Cria a pasta se não existir
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    print("🔍 Iniciando ETL...")
    
    # 1. Configuração de caminho garantido
    OUTPUT_DIR = criar_caminho_confiavel()
    print(f"📁 Pasta de saída: {OUTPUT_DIR}")

    # 2. Conexão com o MongoDB
    try:
        client = MongoClient("mongodb+srv://pedroaugusto:qQ6hfgaJMkTGGdnx@pedro0.iws3hig.mongodb.net/")
        db = client["tech_trends"]
        print("✅ Conexão com MongoDB estabelecida!")
        
        # Verificação crítica da coleção
        if 'performance' not in db.list_collection_names():
            raise ValueError("Coleção 'performance' não encontrada no banco 'tech_trends'")
        
        sample_doc = db.performance.find_one()
        if not sample_doc:
            raise ValueError("Coleção 'performance' está vazia")
            
        print("📄 Exemplo de documento:", {k: v for k, v in sample_doc.items() if k != '_id'})

    except Exception as e:
        print(f"❌ Falha na conexão: {str(e)}", file=sys.stderr)
        return

    # 3. Extração de dados
    print("\n⏳ Extraindo dados...")
    try:
        performance_data = pd.DataFrame(list(db.performance.find({}, {'_id': 0})))
        if performance_data.empty:
            raise ValueError("Nenhum documento encontrado após a extração")
            
        print(f"✅ Dados extraídos: {len(performance_data)} registros")
        print("🔍 Campos encontrados:", list(performance_data.columns))

    except Exception as e:
        print(f"❌ Erro na extração: {str(e)}", file=sys.stderr)
        return

    # 4. Transformação dos dados
    print("\n🔄 Processando dados...")
    try:
        # Verificação de campos obrigatórios
        campos_obrigatorios = ['Student_ID', 'Exam_Score']
        faltantes = [campo for campo in campos_obrigatorios if campo not in performance_data.columns]
        if faltantes:
            raise ValueError(f"Campos obrigatórios faltando: {faltantes}")

        # Processamento seguro de campos numéricos
        performance_data['Exam_Score'] = pd.to_numeric(performance_data['Exam_Score'], errors='coerce')
        
        if 'Homework_Completion_%' in performance_data.columns:
            performance_data['Homework_Score'] = (
                performance_data['Homework_Completion_%']
                .astype(str)
                .str.extract(r'(\d+)')[0]  # Extrai apenas dígitos
                .fillna('0')
                .astype(float)
            )
        else:
            print("⚠️ Campo 'Homework_Completion_%' não encontrado - usando valor padrão 100")
            performance_data['Homework_Score'] = 100.0

        # Cálculo da nota final
        performance_data['Final_Score'] = (
            0.7 * performance_data['Exam_Score'] + 
            0.3 * performance_data['Homework_Score']
        )

        # 5. Salvamento garantido
        output_file = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_file)
        
        performance_data.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        # Verificação pós-salvamento
        if os.path.exists(output_path):
            print(f"\n🎉 ARQUIVO SALVO COM SUCESSO!")
            print(f"📍 Local: {output_path}")
            print(f"📊 Tamanho: {os.path.getsize(output_path)/1024:.2f} KB")
            print(f"📝 Registros: {len(performance_data)}")
            
            # Abre o explorador de arquivos no local do arquivo (Windows)
            if sys.platform == 'win32':
                os.startfile(OUTPUT_DIR)
        else:
            raise RuntimeError("O arquivo não foi criado, mas nenhum erro foi levantado")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {str(e)}", file=sys.stderr)
        
        # Tentativa de salvamento emergencial
        try:
            emergency_path = os.path.join(os.path.expanduser("~"), "Desktop", "EMERGENCY_OUTPUT.csv")
            performance_data.to_csv(emergency_path)
            print(f"⚠️ Salvamento emergencial em: {emergency_path}")
        except:
            print("💥 Falha até no salvamento emergencial!")

if __name__ == "__main__":
    main()