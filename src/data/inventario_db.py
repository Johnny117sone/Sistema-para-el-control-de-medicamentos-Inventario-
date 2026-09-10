"""
Fachada de acceso a datos.

Las ventanas de la UI (ui/*.py) siguen usando `InventarioDB` con la misma
interfaz de siempre (self.db.validar_acceso(...), self.db.db_name, etc.)
para no tener que reescribir cada ventana de golpe. Por dentro, ya no hay
SQL aquí: cada método delega al repositorio correspondiente.

Nota para siguientes iteraciones: varias ventanas (reportes, órdenes de
salida, devoluciones) todavía abren su propia conexión sqlite3 directa
para consultas específicas de reportes. Migrarlas a repositorios propios
(ej. HistorialRepository) es el siguiente paso natural de este refactor.
"""
from data.db import init_schema, DB_NAME
from data.usuarios_repository import UsuariosRepository
from data.medicamentos_repository import MedicamentosRepository
from data.municipios_repository import MunicipiosRepository


class InventarioDB:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.usuarios = UsuariosRepository(db_name)
        self.medicamentos = MedicamentosRepository(db_name)
        self.municipios = MunicipiosRepository(db_name)
        self.init_db()

    def init_db(self):
        init_schema(self.db_name)

    # --- Métodos de compatibilidad (misma firma que la versión anterior) ---
    def validar_acceso(self, usuario, password):
        return self.usuarios.obtener_rol(usuario, password)

    def eliminar_medicamento(self, sku):
        return self.medicamentos.eliminar_logico(sku)

    def registrar_salida_optimizada(self, municipio, sku, periodo):
        return self.medicamentos.registrar_salida_optimizada(municipio, sku, periodo)

    def registrar_o_actualizar(self, datos, es_edicion=False):
        return self.medicamentos.registrar_o_actualizar(datos, es_edicion)

    def obtener_municipios(self):
        return self.municipios.listar_activos()
