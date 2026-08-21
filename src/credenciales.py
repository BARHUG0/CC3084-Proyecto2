import getpass
import sys

import keyring
from keyring.errors import KeyringError

from src.config import CLAVE_TOKEN, SERVICIO_KEYRING

MENSAJE_SIN_BACKEND = (
    "No hay un almacen de credenciales disponible. En Windows y macOS keyring funciona "
    "sin configuracion adicional. En Linux se requiere instalar un Secret Service, "
    "por ejemplo gnome-keyring junto con dbus, o kwallet en entornos KDE."
)


def _verificar_backend():
    backend = keyring.get_keyring()
    if "fail.Keyring" in type(backend).__name__ or "fail" in type(backend).__module__:
        raise RuntimeError(MENSAJE_SIN_BACKEND)


def obtener_secreto(clave=CLAVE_TOKEN, solicitar=True):
    _verificar_backend()
    try:
        valor = keyring.get_password(SERVICIO_KEYRING, clave)
    except KeyringError as error:
        raise RuntimeError(MENSAJE_SIN_BACKEND) from error
    if valor:
        return valor
    if not solicitar:
        return None
    if not sys.stdin.isatty():
        raise RuntimeError(
            f"El secreto '{clave}' no esta almacenado y la sesion no es interactiva. "
            "Ejecute 'python -m src.credenciales guardar' desde una terminal."
        )
    valor = getpass.getpass(f"Ingrese el valor de '{clave}': ").strip()
    if not valor:
        raise ValueError("No se recibio ningun valor.")
    guardar_secreto(valor, clave)
    return valor


def guardar_secreto(valor, clave=CLAVE_TOKEN):
    _verificar_backend()
    try:
        keyring.set_password(SERVICIO_KEYRING, clave, valor)
    except KeyringError as error:
        raise RuntimeError(MENSAJE_SIN_BACKEND) from error


def borrar_secreto(clave=CLAVE_TOKEN):
    _verificar_backend()
    try:
        keyring.delete_password(SERVICIO_KEYRING, clave)
        return True
    except keyring.errors.PasswordDeleteError:
        return False
    except KeyringError as error:
        raise RuntimeError(MENSAJE_SIN_BACKEND) from error


def existe_secreto(clave=CLAVE_TOKEN):
    return obtener_secreto(clave, solicitar=False) is not None


def _main():
    accion = sys.argv[1] if len(sys.argv) > 1 else "estado"
    if accion == "guardar":
        valor = getpass.getpass(f"Ingrese el valor de '{CLAVE_TOKEN}': ").strip()
        if not valor:
            print("No se recibio ningun valor.")
            return
        guardar_secreto(valor)
        print(f"Secreto '{CLAVE_TOKEN}' almacenado en {type(keyring.get_keyring()).__name__}.")
    elif accion == "borrar":
        if borrar_secreto():
            print(f"Secreto '{CLAVE_TOKEN}' eliminado.")
        else:
            print(f"El secreto '{CLAVE_TOKEN}' no estaba almacenado.")
    else:
        estado = "almacenado" if existe_secreto() else "ausente"
        print(f"Backend: {type(keyring.get_keyring()).__name__}")
        print(f"Secreto '{CLAVE_TOKEN}': {estado}")


if __name__ == "__main__":
    _main()
