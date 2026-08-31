from datetime import date

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHrExpenseSheetAdditionalFields(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Trabajador Prueba"})
        cls.other_employee = cls.env["hr.employee"].create({"name": "Otro Trabajador"})

    def _create_sheet(self, **values):
        sheet_values = {
            "name": "Reporte de prueba",
            "employee_id": self.employee.id,
            "zg_report_date": date(2026, 8, 29),
        }
        sheet_values.update(values)
        return self.env["hr.expense.sheet"].create(sheet_values)

    def test_default_values(self):
        sheet = self.env["hr.expense.sheet"].create(
            {
                "name": "Reporte con valores predeterminados",
                "employee_id": self.employee.id,
            }
        )

        self.assertEqual(sheet.zg_report_date, fields.Date.context_today(sheet))
        self.assertEqual(sheet.zg_kms_traveled, 0.0)
        self.assertFalse(sheet.zg_has_lunch)
        self.assertFalse(sheet.zg_lunch_place)

    def test_employee_cannot_have_two_reports_on_same_date(self):
        self._create_sheet()

        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._create_sheet(name="Segundo reporte")

    def test_different_employees_can_report_same_date(self):
        self._create_sheet()

        second_sheet = self._create_sheet(
            name="Reporte de otro trabajador",
            employee_id=self.other_employee.id,
        )

        self.assertTrue(second_sheet)

    def test_same_employee_can_report_different_dates(self):
        self._create_sheet()

        second_sheet = self._create_sheet(
            name="Reporte de otro día",
            zg_report_date=date(2026, 8, 30),
        )

        self.assertTrue(second_sheet)

    def test_kms_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._create_sheet(zg_kms_traveled=-0.01)

    def test_lunch_requires_a_place(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._create_sheet(zg_has_lunch=True)

        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._create_sheet(zg_has_lunch=True, zg_lunch_place="   ")

    def test_lunch_with_place_is_valid(self):
        sheet = self._create_sheet(
            zg_has_lunch=True,
            zg_lunch_place="Casino central",
        )

        self.assertEqual(sheet.zg_lunch_place, "Casino central")

    def test_disabling_lunch_clears_the_place(self):
        sheet = self._create_sheet(
            zg_has_lunch=True,
            zg_lunch_place="Casino central",
        )

        sheet.zg_has_lunch = False

        self.assertFalse(sheet.zg_lunch_place)
