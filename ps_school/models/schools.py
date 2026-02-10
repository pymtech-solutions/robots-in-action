# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class School(models.Model):
    _inherit = "res.partner"

    course_line_ids = fields.One2many(
        comodel_name='school.course.line',
        inverse_name='school_id',
        string="Líneas de Curso",
    )
    student_qty = fields.Integer(string='Alumnos totales', compute='_compute_student_qty', store=True)
    active_student_qty = fields.Integer(string='Alumnos de alta', compute='_compute_student_qty', store=True)
    inactive_student_qty = fields.Integer(string='Alumnos de baja', compute='_compute_student_qty', store=True)
    invoice_type = fields.Selection([('0', 'A la escuela'), ('1', 'A los alumnos')], string='Tipo de facturación',
                                    default='0')
    school_invoice_date = fields.Date(string='Ultima facturación de la escuela', readonly=True)

    def action_change_old_to_new(self):
        all_contacts = self.env['res.partner'].search([])
        for contact in all_contacts:
            if contact.is_school:
                contact.school_role = 'school'
            elif contact.employee_ids and contact.employee_ids[0].is_teacher:
                contact.school_role = 'teacher'
            elif contact.is_student:
                contact.is_student = 'student'
            elif contact.is_parent:
                contact.school_role = 'parent'

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

            if record.active_student_qty == 0 or not record.course_line_ids:
                raise UserError('No hay alumnos para facturar')

            if record.invoice_type == '0':
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

                record.school_invoice_date = fields.Date.today()

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Factura',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': invoice.id,
                    'target': 'current',
                }
            elif record.invoice_type == '1':
                students = record.course_line_ids.mapped('student_ids')

                invoices = []
                for student in students:
                    invoice_parent = student.guardian_ids.filtered(lambda g: g.invoice)[0].partner_id.id,

                    if not invoice_parent:
                        raise UserError(f'El alumno {student.name} no tiene un padre al que facturar. {student.id}')
                    elif student.enrollment_state == 'active':
                        invoices.append({
                            'move_type': 'out_invoice',
                            'partner_id': invoice_parent,
                            'invoice_date': fields.Date.today(),
                            'invoice_line_ids': [(0, 0, {
                                'product_id': product.id,
                                'name': f"{product.name} - {student.name}",
                                'quantity': 1,
                                'tax_ids': [(6, 0, product.taxes_id.ids)],
                                'price_unit': product.list_price
                            })],
                        })

                record.env['account.move'].create(invoices)

                record.school_invoice_date = fields.Date.today()

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Facturas',
                    'res_model': 'account.move',
                    'view_mode': 'list,form',
                    'views': [(self.env.ref('account.view_out_invoice_tree').id, 'list')],
                    'domain': [('move_type', '=', 'out_invoice')],
                    'target': 'current',
                }
