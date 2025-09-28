import sqlite3
import streamlit as st
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

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
# Cargar modelo de Hugging Face
# -----------------------------
@st.cache_resource  # evita recargar el modelo en cada interacción
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
    prompt = f"Convierte esta pregunta en español a SQL para SQLite: {pregunta}"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=128)
    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql

# -----------------------------
# Interfaz Streamlit
# -----------------------------
st.title("🤖 Chatbot con IA + SQLite")

pregunta = st.text_input("Escribí tu consulta:")

if pregunta:
    sql = generar_sql(pregunta)
    st.write(f"🔎 SQL generado: `{sql}`")

    try:
        cursor.execute(sql)
        resultados = cursor.fetchall()
        if resultados:
            st.write("📊 Resultados:")
            for fila in resultados:
                st.write(fila)
        else:
            st.write("⚠️ No se encontraron resultados.")
    except Exception as e:
        st.error(f"Error al ejecutar la consulta: {e}")
