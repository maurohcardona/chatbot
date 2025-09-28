import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import numpy as np

class RealIAChatbot:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        
        # Modelo de IA más liviano para embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Modelo pequeño
        
    def semantic_sql_generation(self, question):
        """Genera SQL usando similitud semántica con IA"""
        # Obtener esquema de la base de datos
        table_info = self.get_table_info()
        
        # Convertir esquema a texto para embeddings
        schema_text = ""
        for table, columns in table_info.items():
            schema_text += f"Tabla {table} tiene columnas: {', '.join(columns)}. "
        
        # Crear embeddings con IA
        question_embedding = self.model.encode(question)
        schema_embedding = self.model.encode(schema_text)
        
        # Calcular similitud semántica
        similarity = util.pytorch_cos_sim(question_embedding, schema_embedding)[0][0]
        
        # Generar SQL basado en similitud y análisis de palabras
        if similarity > 0.3:  # Umbral de confianza
            return self.intelligent_sql_generation(question, table_info)
        else:
            return self.fallback_sql_generation(question)
    
    def intelligent_sql_generation(self, question, table_info):
        """Generación más inteligente de SQL usando análisis semántico"""
        # Análisis más avanzado con IA
        question_lower = question.lower()
        
        # Detectar intención con patrones semánticos
        if self.semantic_match(question, ["cuántos", "cantidad", "número de"]):
            table = list(table_info.keys())[0]
            return f"SELECT COUNT(*) as total FROM {table}"
        
        elif self.semantic_match(question, ["listar", "mostrar", "ver todos"]):
            table = list(table_info.keys())[0]
            return f"SELECT * FROM {table} LIMIT 10"
        
        elif self.semantic_match(question, ["promedio", "media de"]):
            table = list(table_info.keys())[0]
            numeric_cols = [col for col in table_info[table] if any(word in col.lower() for word in ['edad', 'salario', 'precio'])]
            if numeric_cols:
                return f"SELECT AVG({numeric_cols[0]}) as promedio FROM {table}"
        
        return f"SELECT * FROM {table} LIMIT 5"
    
    def semantic_match(self, question, keywords):
        """Comparación semántica en lugar de exacta"""
        question_embedding = self.model.encode(question.lower())
        for keyword in keywords:
            keyword_embedding = self.model.encode(keyword)
            similarity = util.pytorch_cos_sim(question_embedding, keyword_embedding)[0][0]
            if similarity > 0.5:  # Mayor tolerancia semántica
                return True
        return False