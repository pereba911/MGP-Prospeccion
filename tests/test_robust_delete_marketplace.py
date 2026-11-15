#!/usr/bin/env python3
"""
Unit tests for robust_delete_marketplace.py
Validates prefix extraction, deletion decision logic, false-positive prevention,
and directory scanning safety.
"""

import os
import shutil
import tempfile
import unittest

from robust_delete_marketplace import (
    extract_property_number,
    evaluate_deletion_candidate,
    get_active_numbers,
)


class TestRobustDeleteMarketplace(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. get_active_numbers tests
    # -------------------------------------------------------------------------
    def test_get_active_numbers_standard_folders(self):
        os.makedirs(os.path.join(self.test_dir, "01_colinas_san_javier_casa_venta"))
        os.makedirs(os.path.join(self.test_dir, "02_country_club_depto_venta"))
        os.makedirs(os.path.join(self.test_dir, "08_americana_estudio_amueblado_renta"))
        os.makedirs(os.path.join(self.test_dir, "non_numeric_folder"))

        active = get_active_numbers(self.test_dir)
        self.assertEqual(active, {"1", "2", "8"})

    def test_get_active_numbers_ignores_files(self):
        os.makedirs(os.path.join(self.test_dir, "03_elysian_country"))
        with open(os.path.join(self.test_dir, "04_not_a_folder.txt"), "w") as f:
            f.write("test")

        active = get_active_numbers(self.test_dir)
        self.assertEqual(active, {"3"})

    def test_get_active_numbers_nonexistent_directory(self):
        active = get_active_numbers("/path/that/does/not/exist_12345")
        self.assertEqual(active, set())

    # -------------------------------------------------------------------------
    # 2. extract_property_number tests (valid prefixes)
    # -------------------------------------------------------------------------
    def test_extract_valid_underscore_prefix(self):
        self.assertEqual(extract_property_number("01_Colinas de San Javier"), "1")
        self.assertEqual(extract_property_number("02_Country Club Depto Venta"), "2")
        self.assertEqual(extract_property_number("8_Americana Estudio"), "8")
        self.assertEqual(extract_property_number("12_Nave Industrial Zapopan"), "12")

    def test_extract_valid_dash_and_dot_prefix(self):
        self.assertEqual(extract_property_number("03 - Elysian Country Amueblado"), "3")
        self.assertEqual(extract_property_number("04. Country Club 200m2"), "4")
        self.assertEqual(extract_property_number("05 Torre Opera Depto"), "5")

    # -------------------------------------------------------------------------
    # 3. extract_property_number tests (CRITICAL FALSE-POSITIVE DEFENSE)
    # -------------------------------------------------------------------------
    def test_rejects_price_starts(self):
        self.assertIsNone(extract_property_number("$13,800,000 Residencia en Colinas"))
        self.assertIsNone(extract_property_number("$44,900 MXN Renta Departamento"))
        self.assertIsNone(extract_property_number("MX$10,500,000 Depto en Venta"))
        self.assertIsNone(extract_property_number("USD 850,000 Terreno"))

    def test_rejects_surface_units(self):
        self.assertIsNone(extract_property_number("200m2 Departamento Country Club"))
        self.assertIsNone(extract_property_number("200 m2 Departamento"))
        self.assertIsNone(extract_property_number("104.9 m2 habitables"))

    def test_rejects_bedroom_and_bathroom_counts(self):
        self.assertIsNone(extract_property_number("3 recámaras en Country Club"))
        self.assertIsNone(extract_property_number("3 recamaras con bano privado"))
        self.assertIsNone(extract_property_number("4 baños completos"))
        self.assertIsNone(extract_property_number("2 cajones de estacionamiento"))
        self.assertIsNone(extract_property_number("1 recamara amueblada"))

    def test_rejects_generic_or_empty_titles(self):
        self.assertIsNone(extract_property_number("Residencia de lujo en venta"))
        self.assertIsNone(extract_property_number("Departamento amueblado"))
        self.assertIsNone(extract_property_number(""))
        self.assertIsNone(extract_property_number("   "))
        self.assertIsNone(extract_property_number(None))

    # -------------------------------------------------------------------------
    # 4. evaluate_deletion_candidate tests
    # -------------------------------------------------------------------------
    def test_evaluate_retains_active_property(self):
        active_numbers = {"1", "2", "3", "4", "5", "6", "7", "8"}
        should_del, reason, prop_num = evaluate_deletion_candidate(
            "01_Colinas de San Javier Casa Venta", active_numbers
        )
        self.assertFalse(should_del)
        self.assertEqual(prop_num, "1")
        self.assertIn("activa", reason.lower())

    def test_evaluate_marks_obsolete_property_for_deletion(self):
        active_numbers = {"1", "2", "3", "4", "5", "6", "7", "8"}
        should_del, reason, prop_num = evaluate_deletion_candidate(
            "09_Zapopan Depto Venta Antiguo", active_numbers
        )
        self.assertTrue(should_del)
        self.assertEqual(prop_num, "9")
        self.assertIn("obsoleta", reason.lower())

    def test_evaluate_fail_safe_retains_ambiguous_or_unprefixed_listing(self):
        active_numbers = {"1", "2", "3"}
        # Even if a listing has no prefix, it must NOT be deleted accidentally
        should_del, reason, prop_num = evaluate_deletion_candidate(
            "Residencia Colinas de San Javier", active_numbers
        )
        self.assertFalse(should_del)
        self.assertIsNone(prop_num)
        self.assertIn("seguridad", reason.lower())

    def test_evaluate_fail_safe_retains_price_listing(self):
        active_numbers = {"1", "2", "3"}
        should_del, reason, prop_num = evaluate_deletion_candidate(
            "$13,800,000 Residencia Colinas", active_numbers
        )
        self.assertFalse(should_del)
        self.assertIsNone(prop_num)

    def test_evaluate_fail_safe_retains_bedroom_count_listing(self):
        active_numbers = {"1", "2"}
        # "3 recámaras" must NOT trigger deletion of property #3
        should_del, reason, prop_num = evaluate_deletion_candidate(
            "3 recámaras en Country Club", active_numbers
        )
        self.assertFalse(should_del)
        self.assertIsNone(prop_num)


if __name__ == "__main__":
    unittest.main()
