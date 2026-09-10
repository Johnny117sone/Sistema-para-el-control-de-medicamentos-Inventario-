"""
Repositorio de medicamentos.
Contiene las operaciones de catálogo maestro que antes vivían en la clase
InventarioDB. Las ventanas de reportes/devoluciones/órdenes siguen abriendo
conexión directa a la BD para sus consultas específicas (ver nota en README);
aquí solo están las operaciones de escritura centrales del catálogo.
"""
from datetime import datetime
from data.db import get_connection, DB_NAME


class MedicamentosRepository:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name

    def eliminar_logico(self, sku: str) -> bool:
        """Marca un medicamento como INACTIVO en lugar de borrarlo físicamente."""
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE medicamentos SET estatus = 'INACTIVO' WHERE sku = ?", (sku,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar medicamento lógicamente: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def registrar_salida_optimizada(self, municipio: str, sku: str, periodo: str) -> bool:
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        anio_actual = str(datetime.now().year)

        try:
            cursor.execute("""UPDATE medicamentos
                              SET stock_actual = stock_actual - 1,
                                  salidas_municipio = salidas_municipio + 1
                              WHERE sku = ?""", (sku,))

            cursor.execute("""
                INSERT INTO historial_retornos (municipio, sku, tipo_movimiento, cantidad, fecha, periodo, anio)
                VALUES (?, ?, 'SALIDA MUNICIPIO', 1, ?, ?, ?)
                ON CONFLICT(municipio, sku, periodo, anio, tipo_movimiento) DO UPDATE SET
                cantidad = cantidad + 1,
                fecha = excluded.fecha
            """, (municipio, sku, fecha_ahora, periodo, anio_actual))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error en salida optimizada: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def registrar_o_actualizar(self, datos, es_edicion: bool = False):
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if es_edicion:
            sql = '''UPDATE medicamentos SET
                     nombre = ?, gramaje = ?, presentacion = ?, laboratorio = ?,
                     grupo = ?, tipo = ?, stock_actual = ?, stock_min = ?, stock_max = ?
                     WHERE sku = ?'''
            d_edit = (datos[1], datos[2], datos[3], datos[4], datos[5], datos[6], datos[7], datos[8], datos[9], datos[0])
            cursor.execute(sql, d_edit)
        else:
            sql = '''INSERT INTO medicamentos
                     (sku, nombre, gramaje, presentacion, laboratorio, grupo, tipo,
                      stock_actual, stock_min, stock_max, entradas_registro, fecha_registro, estatus)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVO')
                     ON CONFLICT(sku) DO UPDATE SET
                     stock_actual = stock_actual + excluded.stock_actual,
                     entradas_registro = entradas_registro + excluded.entradas_registro,
                     nombre = excluded.nombre, stock_min = excluded.stock_min, stock_max = excluded.stock_max,
                     estatus = 'ACTIVO' '''
            valores = datos + (datos[7], fecha)
            cursor.execute(sql, valores)

        conn.commit()
        conn.close()
