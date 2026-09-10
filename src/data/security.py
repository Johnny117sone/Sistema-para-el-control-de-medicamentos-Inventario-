"""
Utilidades de hashing de contraseñas.

Usa PBKDF2-HMAC-SHA256 (vía hashlib, librería estándar de Python, sin
dependencias externas como bcrypt). Cada contraseña se guarda con un
salt aleatorio distinto, en el formato:

    pbkdf2_sha256$<iteraciones>$<salt_hex>$<hash_hex>

Esto reemplaza el almacenamiento anterior en texto plano.
"""
import hashlib
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000  # recomendación vigente de OWASP para PBKDF2-SHA256


def hash_password(plain_password: str) -> str:
    """Genera un hash seguro con salt aleatorio para guardar en la BD."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${hashed.hex()}"


def verify_password(plain_password: str, stored_value: str) -> bool:
    """
    Compara una contraseña en texto plano contra el valor guardado en la BD.

    Compatible hacia atrás: si `stored_value` no tiene el formato de hash
    (bases de datos antiguas con contraseñas en texto plano), compara
    directamente como texto plano.
    """
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_value.split("$")
        if algorithm != ALGORITHM:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, int(iterations)
        )
        return expected.hex() == hash_hex
    except (ValueError, AttributeError):
        # El valor guardado no tiene formato de hash -> BD antigua en texto plano.
        return plain_password == stored_value
