"""
Servicio de autenticación.

Antes, la lógica de "¿la contraseña actual es correcta?", "¿la nueva
contraseña tiene al menos 6 caracteres?", "¿coinciden nueva y confirmación?"
vivía directamente dentro del código de la ventana del menú (main.py).

Este servicio concentra esas reglas de negocio, separadas tanto de la UI
(no sabe nada de Tkinter) como del acceso a datos (no escribe SQL, usa
el repositorio de usuarios).
"""
from data.usuarios_repository import UsuariosRepository

PASSWORD_MIN_LENGTH = 6


class AuthService:
    def __init__(self, usuarios_repo: UsuariosRepository):
        self.usuarios_repo = usuarios_repo

    def iniciar_sesion(self, usuario: str, password: str):
        """Devuelve el rol ('ADMIN' / 'OPERADOR') si las credenciales son válidas, o None."""
        return self.usuarios_repo.obtener_rol(usuario, password)

    def cambiar_password(self, usuario_objetivo: str, password_actual: str,
                          nueva_password: str, confirmacion: str):
        """
        Aplica todas las reglas de negocio antes de actualizar una contraseña.
        Devuelve una tupla (exito: bool, mensaje: str).
        """
        if not password_actual or not nueva_password or not confirmacion:
            return False, "Complete todos los campos."

        if len(nueva_password) < PASSWORD_MIN_LENGTH:
            return False, f"La nueva contraseña es muy corta. Use al menos {PASSWORD_MIN_LENGTH} caracteres."

        rol_validado = self.usuarios_repo.obtener_rol(usuario_objetivo, password_actual)
        if not rol_validado:
            return False, f"La contraseña actual de {usuario_objetivo.upper()} es incorrecta."

        if nueva_password != confirmacion:
            return False, "La nueva contraseña y la confirmación no coinciden."

        actualizado = self.usuarios_repo.actualizar_password(usuario_objetivo, nueva_password)
        if not actualizado:
            return False, "No se pudo actualizar la contraseña."

        return True, f"Contraseña de {usuario_objetivo.upper()} actualizada correctamente."
