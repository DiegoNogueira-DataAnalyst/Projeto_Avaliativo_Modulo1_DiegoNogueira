"""Casos de fronteira dos formatos brasileiros."""

import importlib.util
from pathlib import Path
from decimal import Decimal
import unittest

raiz = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("transformar", raiz / "2_transformar.py")
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


class ConversoesTest(unittest.TestCase):
    def test_milhar_e_centavos(self):
        self.assertEqual(modulo.converter_decimal(" 1.272,97 "), Decimal("1272.97"))

    def test_ausente_nao_vira_zero(self):
        self.assertIsNone(modulo.converter_decimal(""))
        self.assertIsNone(modulo.converter_data(" "))

    def test_data_bissexta(self):
        self.assertEqual(str(modulo.converter_data("29/02/2024")), "2024-02-29")
        with self.assertRaises(ValueError):
            modulo.converter_data("29/02/2025")

    def test_decimal_invalido(self):
        for texto in ("abc", "NaN", "Infinity", "1,234"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                modulo.converter_decimal(texto)


if __name__ == "__main__":
    unittest.main()
