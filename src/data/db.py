"""
Capa de conexión a la base de datos.
Centraliza el nombre de archivo de la BD y la creación del esquema (tablas).
Los repositorios (usuarios, medicamentos, municipios) usan este módulo
para abrir conexiones, en lugar de que cada ventana de la UI conecte por su cuenta.
"""
import sqlite3

from data.security import hash_password

DB_NAME = "sistema_salud.db"


def get_connection(db_name: str = DB_NAME) -> sqlite3.Connection:
    """Abre una nueva conexión a la base de datos."""
    return sqlite3.connect(db_name)


def init_schema(db_name: str = DB_NAME) -> None:
    """Crea las tablas si no existen y aplica migraciones simples."""
    conn = get_connection(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicamentos (
            sku TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            gramaje TEXT,
            presentacion TEXT,
            laboratorio TEXT,
            grupo TEXT,
            tipo TEXT,
            stock_actual INTEGER DEFAULT 0,
            stock_min INTEGER DEFAULT 5,
            stock_max INTEGER DEFAULT 100,
            entradas_registro INTEGER DEFAULT 0,
            entradas_devolucion INTEGER DEFAULT 0,
            salidas_municipio INTEGER DEFAULT 0,
            salidas_merma INTEGER DEFAULT 0,
            fecha_registro TIMESTAMP,
            estatus TEXT DEFAULT 'ACTIVO'
        )
    ''')

    # Migración: agrega 'estatus' si la tabla ya existía sin esa columna.
    try:
        cursor.execute("ALTER TABLE medicamentos ADD COLUMN estatus TEXT DEFAULT 'ACTIVO'")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_retornos (
            municipio TEXT,
            sku TEXT,
            tipo_movimiento TEXT,
            cantidad INTEGER DEFAULT 0,
            fecha TIMESTAMP,
            periodo TEXT,
            anio TEXT,
            UNIQUE(municipio, sku, periodo, anio, tipo_movimiento)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS municipios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            estado_republica TEXT NOT NULL,
            estatus TEXT DEFAULT 'ACTIVO',
            UNIQUE(nombre, estado_republica)
        )
    ''')

    # Usuarios por defecto (solo si la tabla está vacía). Las contraseñas
    # se guardan ya con hash, nunca en texto plano.
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                       ("admin", hash_password("1234"), "OPERADOR"))
        cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                       ("master", hash_password("admin99"), "ADMIN"))

    conn.commit()
    conn.close()
