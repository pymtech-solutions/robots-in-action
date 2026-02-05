# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class School(models.Model):
    _inherit = "res.partner"

    is_school = fields.Boolean(string='Es colegio')

    course_line_ids = fields.One2many(
        comodel_name='school.course.line',
        inverse_name='school_id',
        string="Líneas de Curso",
    )
    student_qty = fields.Integer(string='Alumnos totales', compute='_compute_student_qty', store=True)
    active_student_qty = fields.Integer(string='Alumnos de alta', compute='_compute_student_qty', store=True)
    inactive_student_qty = fields.Integer(string='Alumnos de baja', compute='_compute_student_qty', store=True)

    @api.depends('course_line_ids.student_ids', 'course_line_ids.student_ids.enrollment_state')
    def _compute_student_qty(self):
        for school in self:
            school.student_qty = len(school.course_line_ids.mapped('student_ids'))
            school.active_student_qty = len(
                school.course_line_ids.mapped('student_ids').filtered(lambda s: s.enrollment_state == 'active'))
            school.inactive_student_qty = len(
                school.course_line_ids.mapped('student_ids').filtered(lambda s: s.enrollment_state == 'inactive'))

    def action_create_school_invoice(self):
        for record in self:
            # Get the product
            product = self.env.ref('ps_school.active_student_product')
            invoice = record.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': record.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'quantity': record.active_student_qty,
                    'tax_ids': [(6, 0, product.taxes_id.ids)],
                    'price_unit': product.list_price
                })],
            })

            return {
                'type': 'ir.actions.act_window',
                'name': 'Factura',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
                'target': 'current',
            }
