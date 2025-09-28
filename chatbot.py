import sqlite3
import streamlit as st

# Conectar base de datos
conexion = sqlite3.connect("empresa.db")
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

# Agregar datos de ejemplo si la tabla está vacía
cursor.execute("SELECT COUNT(*) FROM empleados")
if cursor.fetchone()[0] == 0:
    empleados = [
        ("Ana", "Ingeniera", 75000),
        ("Juan", "Técnico", 45000),
        ("María", "Analista", 60000),
        ("Pedro", "Gerente", 90000)
    ]
    cursor.executemany("INSERT INTO empleados (nombre, puesto, salario) VALUES (?, ?, ?)", empleados)
    conexion.commit()

st.title("Chatbot con IA y SQLite")

pregunta = st.text_input("Escribí tu consulta:")

if pregunta:
    # Por ahora simulamos la IA con reglas simples
    if "mayor salario" in pregunta.lower():
        cursor.execute("SELECT nombre, puesto, salario FROM empleados ORDER BY salario DESC LIMIT 1")
    elif "todos" in pregunta.lower():
        cursor.execute("SELECT nombre, puesto, salario FROM empleados")
    else:
        cursor.execute("SELECT nombre, puesto, salario FROM empleados")
    
    resultados = cursor.fetchall()
    for fila in resultados:
        st.write(fila)
