"""
Repositorio de usuarios.
Único lugar del proyecto que ejecuta SQL sobre la tabla `usuarios`.
No contiene reglas de negocio (esas viven en services/auth_service.py) ni UI.

Las contraseñas se guardan y verifican usando data/security.py (hash con
salt), nunca en texto plano.
"""
from data.db import get_connection, DB_NAME
from data.security import hash_password, verify_password


class UsuariosRepository:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name

    def obtener_rol(self, usuario: str, password: str):
        """Devuelve el rol si las credenciales son correctas, o None."""
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password, rol FROM usuarios WHERE username = ?",
            (usuario,),
        )
        resultado = cursor.fetchone()
        conn.close()

        if not resultado:
            return None

        password_guardada, rol = resultado
        if verify_password(password, password_guardada):
            return rol
        return None

    def actualizar_password(self, usuario: str, nueva_password: str) -> bool:
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET password = ? WHERE username = ?",
                (hash_password(nueva_password), usuario),
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
