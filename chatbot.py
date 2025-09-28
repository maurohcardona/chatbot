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
    modelo = "Salesforce/codet5-small"
    tokenizer = AutoTokenizer.from_pretrained(modelo)
    model = AutoModelForSeq2SeqLM.from_pretrained(modelo)
    return tokenizer, model

tokenizer, model = cargar_modelo()

# -----------------------------
# Función para generar SQL desde español
# -----------------------------
def generar_sql(pregunta):
    prompt = f"""
La pregunta está en español. Genera una consulta SQL válida para SQLite 
basada en esta pregunta. La tabla disponible es empleados(id, nombre, puesto, salario).
Pregunta: {pregunta}
Devuelve SOLO la consulta SQL.
"""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=128)
    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql

# -----------------------------
# Validación básica de SQL
# -----------------------------
def validar_sql(sql):
    sql = sql.strip().lower()
    if sql.startswith(("select", "insert", "update")):
        return True
    return False

# -----------------------------
# Interfaz Streamlit
# -----------------------------
st.title("🤖 Chatbot con IA + SQLite (preguntas en español)")

pregunta = st.text_input("Escribí tu consulta:")

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
