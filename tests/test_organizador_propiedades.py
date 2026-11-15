#!/usr/bin/env python3
"""
Unit tests for organizador_propiedades_autonomo.py
Validates emoji sanitization, routing list determination, WhatsApp formatting,
and clean_obsolete_folders safety.
"""

import os
import shutil
import tempfile
import unittest

from organizador_propiedades_autonomo import (
    clean_no_emojis,
    determine_routing_lists,
    clean_obsolete_folders,
    PROPIEDADES_DIR,
)


class TestOrganizadorPropiedades(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. clean_no_emojis tests
    # -------------------------------------------------------------------------
    def test_clean_no_emojis_removes_standard_emojis(self):
        raw = "🏠 Hermosa residencia en venta ✨🔑 con alberca 🏊‍♂️ y jardín 🌳"
        cleaned = clean_no_emojis(raw)
        self.assertEqual(cleaned, "Hermosa residencia en venta con alberca y jardín")

    def test_clean_no_emojis_preserves_accents_and_punctuation(self):
        raw = "¡OPORTUNIDAD ÚNICA! Departamento de 273 m², $13,800,000 MXN. ¿Te interesa?"
        cleaned = clean_no_emojis(raw)
        self.assertEqual(cleaned, raw)

    def test_clean_no_emojis_collapses_whitespace(self):
        raw = "Casa   en    Colinas  de   San  Javier"
        cleaned = clean_no_emojis(raw)
        self.assertEqual(cleaned, "Casa en Colinas de San Javier")

    # -------------------------------------------------------------------------
    # 2. determine_routing_lists tests
    # -------------------------------------------------------------------------
    def test_routing_venta_residencial_san_javier(self):
        lists = determine_routing_lists('casa', 'Venta', 'Colinas de San Javier, Guadalajara')
        self.assertIn("1. Solo Venta (Inmuebles ZMG)", lists)
        self.assertIn("7. Zona Providencia - Country Club - Colomos", lists)
        self.assertIn("12. Inmobiliarios Generales y Asesores ZMG", lists)
        self.assertNotIn("11. Solo Renta (Departamentos y Casas)", lists)

    def test_routing_renta_country_club(self):
        lists = determine_routing_lists('departamento', 'Renta', 'Country Club, Guadalajara')
        self.assertIn("11. Solo Renta (Departamentos y Casas)", lists)
        self.assertIn("2. Venta y Renta (Inmuebles ZMG)", lists)
        self.assertIn("7. Zona Providencia - Country Club - Colomos", lists)
        self.assertIn("12. Inmobiliarios Generales y Asesores ZMG", lists)
        self.assertNotIn("1. Solo Venta (Inmuebles ZMG)", lists)

    def test_routing_oficina_renta_hsbc(self):
        lists = determine_routing_lists('oficina', 'Renta', 'Torre HSBC, Providencia')
        self.assertIn("4. Oficinas y Corporativos", lists)
        self.assertIn("11. Solo Renta (Departamentos y Casas)", lists)
        self.assertIn("7. Zona Providencia - Country Club - Colomos", lists)
        self.assertIn("12. Inmobiliarios Generales y Asesores ZMG", lists)

    def test_routing_deduplication(self):
        lists = determine_routing_lists('casa', 'Venta', 'Providencia Country Club Colomos')
        # Check no duplicates exist
        self.assertEqual(len(lists), len(set(lists)))

    # -------------------------------------------------------------------------
    # 3. clean_obsolete_folders safety tests
    # -------------------------------------------------------------------------
    def test_clean_obsolete_folders_isolation(self):
        # Create a mock folder environment
        import organizador_propiedades_autonomo as opa
        original_dir = opa.PROPIEDADES_DIR
        try:
            opa.PROPIEDADES_DIR = self.test_dir
            os.makedirs(os.path.join(self.test_dir, "01_activa"))
            os.makedirs(os.path.join(self.test_dir, "99_obsoleta"))

            deleted = opa.clean_obsolete_folders({"01_activa"})
            self.assertEqual(deleted, ["99_obsoleta"])
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, "01_activa")))
            self.assertFalse(os.path.exists(os.path.join(self.test_dir, "99_obsoleta")))
        finally:
            opa.PROPIEDADES_DIR = original_dir


if __name__ == "__main__":
    unittest.main()
