from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones'

# Diccionario de consultas
consultas = {
    "Estadisticas de jugadores": """
        SELECT * FROM (
            SELECT * FROM vista_jugadores_estadisticas
        ) AS sub
        LIMIT {limit} OFFSET {offset}
    """,

    "Top 10 jugadores con más de 25 puntos": """
        SELECT * FROM (
            SELECT j.nombre AS Jugador, e.nombre AS Equipo, p.fecha AS Fecha_Partido,
                   es.puntos AS Puntos, es.rebotes, es.asistencias
            FROM estadisticas es
            JOIN jugadores j ON es.id_jugador = j.id_jugador
            JOIN equipos e ON j.equipo_id = e.id_equipo
            JOIN partidos p ON es.id_partido = p.id_partido
            WHERE es.puntos >= 25
            ORDER BY es.puntos DESC
        ) AS sub
        LIMIT {limit} OFFSET {offset}
    """,

    "Promedio de puntos como local por equipo": """
        SELECT * FROM (
            SELECT eq.nombre AS Equipo_Local, AVG(p.puntos_local) AS Promedio_Puntos_Local
            FROM partidos p
            JOIN equipos eq ON p.equipo_local_id = eq.id_equipo
            GROUP BY eq.nombre
            ORDER BY Promedio_Puntos_Local DESC
        ) AS sub
        LIMIT {limit} OFFSET {offset}
    """,

    "Jugadores Escoltas o Aleros ordenados por altura": """
        SELECT * FROM (
            SELECT nombre, posicion, altura
            FROM jugadores
            WHERE posicion IN ('Escolta', 'Alero')
            ORDER BY altura DESC
        ) AS sub
        LIMIT {limit} OFFSET {offset}
    """,

    "Jugadores sin estadísticas registradas": """
        SELECT * FROM (
            SELECT j.nombre, e.nombre AS Equipo
            FROM jugadores j
            LEFT JOIN estadisticas es ON j.id_jugador = es.id_jugador
            JOIN equipos e ON j.equipo_id = e.id_equipo
            WHERE es.id_estadistica IS NULL
        ) AS sub
        LIMIT {limit} OFFSET {offset}
    """,

    "Características Físicas de jugadores":"""
        SELECT * FROM (
            SELECT nombre, posicion, altura, peso
            FROM jugadores
            ORDER BY nombre
        )AS sub
        LIMIT {limit} OFFSET {offset}
    """
}


def get_db_connection():
    return pymysql.connect(
        host='ballast.proxy.rlwy.net',
        port=29681,
        user='root',
        password='UShYqZPcenAHzdvHcpcMoBOuuHPztGHF',
        database='railway',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = generate_password_hash(request.form['contraseña'])

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO usuarios (nombre, correo, contraseña) VALUES (%s, %s, %s)",
                           (nombre, correo, contraseña))
            connection.commit()
        connection.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user['contraseña'], contraseña):
            session['user_id'] = user['id']
            session['user_name'] = user['nombre']
            return redirect(url_for('index'))
        else:
            return "❌ Credenciales inválidas"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    consulta_seleccionada = request.args.get('consulta', 'Estadisticas de jugadores')
    pagina = int(request.args.get('pagina', 1))
    por_pagina = 10
    offset = (pagina - 1) * por_pagina

    sql = consultas[consulta_seleccionada].format(limit=por_pagina, offset=offset)

    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute(sql)
        resultados = cursor.fetchall()
    connection.close()

    return render_template('index.html',
                           user_name=session.get('user_name'),
                           consulta_seleccionada=consulta_seleccionada,
                           consultas=list(consultas.keys()),
                           resultados=resultados,
                           pagina=pagina)

# --- Ejecutar la aplicación ---
if __name__ == "__main__":
    app.run(debug=True)