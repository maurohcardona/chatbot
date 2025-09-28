import sqlite3
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering
import re

class DBChatbot:
    def __init__(self, db_path, model_name="mrm8488/bert-small-finetuned-squad"):
        self.db_path = db_path
        self.qa_pipeline = pipeline(
            "question-answering",
            model=model_name,
            tokenizer=model_name
        )
        self.connection = sqlite3.connect(db_path)
        
    def get_table_info(self):
        """Obtiene información sobre las tablas en la base de datos"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_info = {}
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            table_info[table_name] = [col[1] for col in columns]
            
        return table_info
    
    def execute_query(self, query):
        """Ejecuta una consulta SQL y retorna los resultados"""
        try:
            df = pd.read_sql_query(query, self.connection)
            return df
        except Exception as e:
            return f"Error en la consulta: {str(e)}"
    
    def natural_language_to_sql(self, question, table_name):
        """Convierte preguntas naturales a consultas SQL simples"""
        question_lower = question.lower()
        table_info = self.get_table_info()
        
        if table_name not in table_info:
            return f"Tabla {table_name} no encontrada"
        
        columns = table_info[table_name]
        
        # Detectar tipo de consulta
        if "cuántos" in question_lower or "cantidad" in question_lower:
            return f"SELECT COUNT(*) as cantidad FROM {table_name}"
        elif "listar" in question_lower or "mostrar" in question_lower:
            return f"SELECT * FROM {table_name} LIMIT 10"
        elif "promedio" in question_lower and any(col for col in columns if 'precio' in col.lower() or 'valor' in col.lower()):
            numeric_col = next((col for col in columns if 'precio' in col.lower() or 'valor' in col.lower()), columns[0])
            return f"SELECT AVG({numeric_col}) as promedio FROM {table_name}"
        else:
            return f"SELECT * FROM {table_name} LIMIT 5"
    
    def ask_question(self, question, table_name="usuarios"):
        """Responde preguntas sobre la base de datos"""
        # Primero intentamos con SQL
        sql_query = self.natural_language_to_sql(question, table_name)
        result = self.execute_query(sql_query)
        
        if isinstance(result, pd.DataFrame) and not result.empty:
            # Convertir resultados a texto para el modelo de QA
            context = result.to_string()
            
            # Usar el modelo de QA para responder más específicamente
            qa_result = self.qa_pipeline(
                question=question,
                context=context
            )
            
            return {
                "respuesta": qa_result['answer'],
                "confianza": qa_result['score'],
                "consulta_sql": sql_query,
                "datos": result.head(3).to_dict('records')
            }
        else:
            return {"error": "No se pudieron obtener datos de la base de datos"}
    
    def close(self):
        self.connection.close()

# Ejemplo de uso
def main():
    # Crear base de datos de ejemplo
    conn = sqlite3.connect('ejemplo.db')
    cursor = conn.cursor()
    
    # Crear tabla de ejemplo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            edad INTEGER,
            ciudad TEXT,
            salario REAL
        )
    ''')
    
    # Insertar datos de ejemplo
    usuarios = [
        (1, 'Ana García', 28, 'Madrid', 35000),
        (2, 'Carlos López', 35, 'Barcelona', 42000),
        (3, 'María Rodríguez', 42, 'Sevilla', 38000),
        (4, 'Juan Martínez', 31, 'Valencia', 45000),
        (5, 'Laura Fernández', 29, 'Madrid', 37000)
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO usuarios VALUES (?, ?, ?, ?, ?)', usuarios)
    conn.commit()
    conn.close()
    
    # Usar el chatbot
    chatbot = DBChatbot('ejemplo.db')
    
    preguntas = [
        "¿Cuántos usuarios hay?",
        "¿Listar los usuarios de Madrid?",
        "¿Cuál es el salario promedio?"
    ]
    
    for pregunta in preguntas:
        print(f"\nPregunta: {pregunta}")
        respuesta = chatbot.ask_question(pregunta)
        print(f"Respuesta: {respuesta['respuesta']}")
        print(f"Confianza: {respuesta['confianza']:.2f}")
        print(f"Consulta SQL: {respuesta['consulta_sql']}")
    
    chatbot.close()

if __name__ == "__main__":
    main()