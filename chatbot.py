import sqlite3
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# -----------------------------
# Conexión a SQLite
# -----------------------------
conexion = sqlite3.connect("./empresa.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS empleados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    puesto TEXT,
    salario REAL
)
""")
conexion.commit()

# -----------------------------
# Cargar modelo Hugging Face
# -----------------------------
@st.cache_resource
def cargar_modelo():
    modelo = "google/flan-t5-small"
    tokenizer = AutoTokenizer.from_pretrained(modelo)
    model = AutoModelForSeq2SeqLM.from_pretrained(modelo)
    return tokenizer, model

tokenizer, model = cargar_modelo()

# -----------------------------
# Función para generar SQL
# -----------------------------
def generar_sql(pregunta):
    prompt = f"""
Eres un asistente que convierte preguntas en español a consultas SQL para SQLite.
Base de datos: empleados(id, nombre, puesto, salario)
Instrucciones: Devuelve SOLO la consulta SQL, sin explicaciones.
La consulta puede ser SELECT, INSERT o UPDATE según corresponda a la pregunta.

Pregunta: {pregunta}
"""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=128)
    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql

# -----------------------------
# Función para validar SQL
# -----------------------------
def validar_sql(sql):
    # Evitar ejecutar comandos peligrosos
    sql = sql.strip().lower()
    if sql.startswith(("select", "insert", "update")):
        return True
    return False

# -----------------------------
# Interfaz Streamlit
# -----------------------------
st.title("🤖 Chatbot con IA + SQLite")

pregunta = st.text_input("Escribí tu consulta (SELECT, INSERT, UPDATE):")

if pregunta:
    sql = generar_sql(pregunta)
    st.write(f"🔎 SQL generado: `{sql}`")

    if validar_sql(sql):
        try:
            cursor.execute(sql)
            conexion.commit()
            resultados = cursor.fetchall()
            if resultados:
                st.write("📊 Resultados:")
                for fila in resultados:
                    st.write(fila)
            else:
                st.write("✅ Consulta ejecutada correctamente.")
        except Exception as e:
            st.error(f"Error al ejecutar la consulta: {e}")
    else:
        st.error("❌ SQL no permitido o inválido")
