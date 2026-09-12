"""Pruebas unitarias para las funciones de src/main.py.

Compatible con unittest y pytest.
"""

import unittest

try:
    from src.main import evaluar_fuerza, generar_contrasena
except ImportError:
    from main import evaluar_fuerza, generar_contrasena


class TestGeneradorContrasena(unittest.TestCase):
    """Casos de prueba para generar_contrasena."""

    def test_longitud_correcta(self):
        """Verifica que la contraseña generada tenga la longitud solicitada."""
        for longitud in [8, 12, 16, 25]:
            resultado = generar_contrasena(longitud=longitud)
            self.assertEqual(len(resultado), longitud)

    def test_longitud_invalida_lanza_error(self):
        """Verifica que longitudes menores a 4 lancen un ValueError."""
        with self.assertRaises(ValueError):
            generar_contrasena(longitud=3)

    def test_incluye_caracteres_requeridos(self):
        """Verifica que incluya dígitos y símbolos cuando están habilitados."""
        resultado = generar_contrasena(longitud=20, incluir_numeros=True, incluir_simbolos=True)
        tiene_digito = any(c.isdigit() for c in resultado)
        tiene_simbolo = any(c in "!@#$%&*+-_=?" for c in resultado)
        self.assertTrue(tiene_digito, "Debería contener al menos un dígito")
        self.assertTrue(tiene_simbolo, "Debería contener al menos un símbolo")


class TestEvaluadorFuerza(unittest.TestCase):
    """Casos de prueba para evaluar_fuerza."""

    def test_contrasena_corta_debil(self):
        """Contraseñas cortas y simples deben tener baja puntuación."""
        res = evaluar_fuerza("abc")
        self.assertIn(res["nivel"], ["Muy Debil", "Debil"])
        self.assertLessEqual(res["puntuacion"], 1)

    def test_contrasena_robusta(self):
        """Contraseñas largas con variedad deben tener alta puntuación."""
        res = evaluar_fuerza("P@ssw0rd2026!Segura")
        self.assertIn(res["nivel"], ["Muy Fuerte", "Excelente"])
        self.assertGreaterEqual(res["puntuacion"], 4)


if __name__ == "__main__":
    unittest.main()
