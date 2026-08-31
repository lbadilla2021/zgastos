from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    zg_report_date = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
        index=True,
        tracking=True,
        copy=False,
        help="Fecha de la jornada asociada al reporte.",
    )
    zg_kms_traveled = fields.Float(
        string="Kms Recorridos",
        digits=(16, 2),
        default=0.0,
        tracking=True,
        copy=False,
        help="Cantidad de kilómetros recorridos durante la jornada.",
    )
    zg_has_lunch = fields.Boolean(
        string="Almuerzo",
        default=False,
        tracking=True,
        copy=False,
        help="Indica si el trabajador tuvo almuerzo durante la jornada.",
    )
    zg_lunch_place = fields.Char(
        string="Lugar Almuerzo",
        tracking=True,
        copy=False,
        help="Lugar donde almorzó el trabajador.",
    )

    _sql_constraints = [
        (
            "zg_employee_report_date_unique",
            "UNIQUE(employee_id, zg_report_date)",
            "El trabajador ya tiene un reporte para esta fecha.",
        ),
        (
            "zg_kms_traveled_nonnegative",
            "CHECK(zg_kms_traveled >= 0)",
            "Los kilómetros recorridos no pueden ser negativos.",
        ),
        (
            "zg_lunch_data_consistency",
            """
                CHECK(
                    (zg_has_lunch AND NULLIF(BTRIM(zg_lunch_place), '') IS NOT NULL)
                    OR (NOT zg_has_lunch AND zg_lunch_place IS NULL)
                )
            """,
            "Debe ingresar el lugar del almuerzo cuando Almuerzo está activado.",
        ),
    ]

    @api.constrains("zg_has_lunch", "zg_lunch_place")
    def _check_lunch_place(self):
        for sheet in self:
            if sheet.zg_has_lunch and not (sheet.zg_lunch_place or "").strip():
                raise ValidationError(
                    _("Debe ingresar el lugar del almuerzo cuando Almuerzo está activado.")
                )
            if not sheet.zg_has_lunch and sheet.zg_lunch_place:
                raise ValidationError(
                    _("El lugar del almuerzo solo puede informarse cuando Almuerzo está activado.")
                )

    @api.onchange("zg_has_lunch")
    def _onchange_zg_has_lunch(self):
        if not self.zg_has_lunch:
            self.zg_lunch_place = False

    @api.model_create_multi
    def create(self, vals_list):
        normalized_vals_list = []
        for vals in vals_list:
            normalized_vals = dict(vals)
            if not normalized_vals.get("zg_has_lunch", False):
                normalized_vals["zg_lunch_place"] = False
            normalized_vals_list.append(normalized_vals)
        return super().create(normalized_vals_list)

    def write(self, vals):
        normalized_vals = dict(vals)
        if "zg_has_lunch" in normalized_vals and not normalized_vals["zg_has_lunch"]:
            normalized_vals["zg_lunch_place"] = False
        return super().write(normalized_vals)

