import sqlite3
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from googletrans import Translator  # Para traducir español -> inglés

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
# Traductor español -> inglés
# -----------------------------
translator = Translator()

# -----------------------------
# Cargar modelo Hugging Face Text-to-SQL
# -----------------------------
@st.cache_resource
def cargar_modelo():
    modelo = "tscholak/bert2sql-small"
    tokenizer = AutoTokenizer.from_pretrained(modelo)
    model = AutoModelForSeq2SeqLM.from_pretrained(modelo)
    return tokenizer, model

tokenizer, model = cargar_modelo()

# -----------------------------
# Función para generar SQL
# -----------------------------
def generar_sql(pregunta_en_ingles):
    prompt = f"""
Generate a valid SQLite query for the following question: {pregunta_en_ingles}
The table available is: empleados(id, nombre, puesto, salario)
Return only the SQL query.
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
    # Traducir pregunta al inglés
    pregunta_en_ingles = translator.translate(pregunta, src='es', dest='en').text

    # Generar SQL con IA
    sql = generar_sql(pregunta_en_ingles)
    st.write(f"🔎 SQL generado: `{sql}`")

    # Ejecutar SQL si es válido
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
