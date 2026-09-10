"""Repositorio de municipios."""
from data.db import get_connection, DB_NAME


class MunicipiosRepository:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name

    def listar_activos(self):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre || ' - ' || estado_republica
                FROM municipios
                WHERE estatus = 'ACTIVO'
                ORDER BY nombre ASC
            """)
            lista = [fila[0] for fila in cursor.fetchall()]
            conn.close()
            return lista
        except Exception:
            return []
