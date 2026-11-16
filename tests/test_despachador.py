#!/usr/bin/env python3
"""Tests unitarios para despachador_publicaciones.py."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import despachador_publicaciones as dp


class TestDespachadorPublicaciones(unittest.TestCase):

    def test_generar_plan_lunes(self):
        plan = dp.generar_plan_del_dia(dia_idx=0)
        self.assertEqual(plan["dia"], "Lunes")
        self.assertEqual(plan["tipo"], "Venta")
        self.assertEqual(len(plan["jobs"]), 2)
        prop_ids = [j["property_id"] for j in plan["jobs"]]
        self.assertIn("01_colinas_san_javier_casa_venta", prop_ids)
        self.assertIn("02_country_club_depto_venta", prop_ids)
        for job in plan["jobs"]:
            self.assertEqual(job["type"], "publish")
            self.assertEqual(job["lists"], ["Solo Venta"])
            self.assertGreater(len(job["photos"]), 0)
            self.assertIn("https://wa.me/523340088294", job["comment"])

    def test_generar_plan_martes(self):
        plan = dp.generar_plan_del_dia(dia_idx=1)
        self.assertEqual(plan["dia"], "Martes")
        self.assertEqual(plan["tipo"], "Renta")
        self.assertEqual(len(plan["jobs"]), 6)
        for job in plan["jobs"]:
            self.assertEqual(job["lists"], ["Lista Venta y Renta"])

    def test_generar_plan_domingo_descanso(self):
        plan = dp.generar_plan_del_dia(dia_idx=6)
        self.assertEqual(plan["dia"], "Domingo")
        self.assertEqual(plan["tipo"], "Descanso")
        self.assertEqual(len(plan["jobs"]), 0)

    def test_generar_plan_propiedad_override(self):
        plan = dp.generar_plan_del_dia(dia_idx=0, propiedad_override="05_torre_opera_depto_renta")
        self.assertEqual(len(plan["jobs"]), 1)
        self.assertEqual(plan["jobs"][0]["property_id"], "05_torre_opera_depto_renta")

    def test_idempotencia_omitir_si_completado_hoy(self):
        plan = dp.generar_plan_del_dia(dia_idx=0)
        # Mock status file
        prev_data = {
            "state": "DONE",
            "fecha": plan["fecha"],
            "jobs_completados": [j["id"] for j in plan["jobs"]],
        }
        test_status = Path("/tmp/test_despachador_status.json")
        test_status.write_text(json.dumps(prev_data), encoding="utf-8")

        orig_status = dp.STATUS_FILE
        try:
            dp.STATUS_FILE = test_status
            ya_hecho, motivo = dp.verificar_idempotencia_hoy(plan)
            self.assertTrue(ya_hecho)
            self.assertIn("ya fueron procesados", motivo)
        finally:
            dp.STATUS_FILE = orig_status
            if test_status.exists():
                test_status.unlink()

    def test_dry_run_retorna_ok_sin_despachar(self):
        plan = dp.generar_plan_del_dia(dia_idx=0)
        res = dp.despachar(plan, dry_run=True)
        self.assertEqual(res["state"], "DRY_RUN_OK")
        self.assertEqual(res["dia"], "Lunes")


if __name__ == "__main__":
    unittest.main()
