"""Módulo principal: Generador y Evaluador de Contraseñas Seguras.

Proyecto modular para Diplomado - Módulo 1.
"""

import random
import string
import sys

# Asegurar compatibilidad con terminales de Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def generar_contrasena(
    longitud: int = 12,
    incluir_mayusculas: bool = True,
    incluir_numeros: bool = True,
    incluir_simbolos: bool = True,
) -> str:
    """Genera una contraseña aleatoria basada en los parámetros especificados."""
    if longitud < 4:
        raise ValueError("La longitud mínima de la contraseña es de 4 caracteres.")

    caracteres_base = string.ascii_lowercase
    caracteres_obligatorios = [random.choice(caracteres_base)]

    if incluir_mayusculas:
        caracteres_base += string.ascii_uppercase
        caracteres_obligatorios.append(random.choice(string.ascii_uppercase))

    if incluir_numeros:
        caracteres_base += string.digits
        caracteres_obligatorios.append(random.choice(string.digits))

    if incluir_simbolos:
        simbolos = "!@#$%&*+-_=?"
        caracteres_base += simbolos
        caracteres_obligatorios.append(random.choice(simbolos))

    # Completar la longitud restante
    caracteres_restantes = [
        random.choice(caracteres_base)
        for _ in range(longitud - len(caracteres_obligatorios))
    ]

    todos_los_caracteres = caracteres_obligatorios + caracteres_restantes
    random.shuffle(todos_los_caracteres)

    return "".join(todos_los_caracteres)


def evaluar_fuerza(contrasena: str) -> dict:
    """Evalúa la robustez de una contraseña devolviendo nivel y puntuación."""
    longitud = len(contrasena)
    tiene_minusculas = any(c.islower() for c in contrasena)
    tiene_mayusculas = any(c.isupper() for c in contrasena)
    tiene_digitos = any(c.isdigit() for c in contrasena)
    tiene_simbolos = any(c in "!@#$%&*+-_=?" for c in contrasena)

    puntuacion = 0
    if longitud >= 8:
        puntuacion += 1
    if longitud >= 12:
        puntuacion += 1
    if tiene_minusculas and tiene_mayusculas:
        puntuacion += 1
    if tiene_digitos:
        puntuacion += 1
    if tiene_simbolos:
        puntuacion += 1

    niveles = {
        0: "Muy Debil",
        1: "Debil",
        2: "Media",
        3: "Fuerte",
        4: "Muy Fuerte",
        5: "Excelente",
    }

    return {
        "longitud": longitud,
        "puntuacion": puntuacion,
        "nivel": niveles.get(puntuacion, "Media"),
    }


def menu():
    """Interfaz de consola interactiva."""
    print("=" * 50)
    print(">> GESTOR Y GENERADOR DE CONTRASEÑAS SEGURAS <<")
    print("=" * 50)

    while True:
        print("\nOpciones:")
        print("1. Generar contraseña aleatoria")
        print("2. Evaluar fortaleza de una contraseña")
        print("3. Salir")

        opcion = input("\nElige una opción (1-3): ").strip()

        if opcion == "1":
            try:
                longitud_str = input("Longitud deseada (por defecto 12): ").strip()
                longitud = int(longitud_str) if longitud_str else 12
                pwd = generar_contrasena(longitud=longitud)
                fuerza = evaluar_fuerza(pwd)
                print("\n" + "-" * 40)
                print(f"[+] Contraseña: {pwd}")
                print(f"[*] Nivel de seguridad: {fuerza['nivel']} (Puntos: {fuerza['puntuacion']}/5)")
                print("-" * 40)
            except ValueError as e:
                print(f"[!] Error: {e}")

        elif opcion == "2":
            pwd = input("Ingresa la contraseña a evaluar: ").strip()
            if not pwd:
                print("[!] La contraseña no puede estar vacía.")
                continue
            fuerza = evaluar_fuerza(pwd)
            print("\n" + "-" * 40)
            print(f"Longitud: {fuerza['longitud']} caracteres")
            print(f"Fortaleza: {fuerza['nivel']} ({fuerza['puntuacion']}/5)")
            print("-" * 40)

        elif opcion == "3":
            print("\n>> ¡Hasta luego! <<\n")
            break
        else:
            print("[!] Opción inválida. Intenta nuevamente.")


if __name__ == "__main__":
    menu()

# prueba de branch protection
