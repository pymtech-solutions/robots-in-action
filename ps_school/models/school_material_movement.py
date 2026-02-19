# -*- coding: utf-8 -*-
from odoo import api, fields, models


# Nuevo modelo para gestionar movimientos de materiales
class SchoolMaterialMovement(models.Model):
    _name = 'school.material.movement'
    _description = 'Movimiento de materiales'
    _order = 'date desc, id desc'

    box_id = fields.Many2one(
        comodel_name='school.box',
        string='Caja',
        required=True,
        ondelete='cascade',
    )

    attendance_id = fields.Many2one(comodel_name='school.attendance', string='Asistencia')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto',
        required=True,
        ondelete='cascade'
    )

    qty = fields.Integer(string='Cantidad')
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)
    notes = fields.Text(string='Observaciones')

    movement_type = fields.Selection([
        ('loss', 'Pérdida'),
        ('increment', 'Reposición'),
    ], string='Tipo de movimiento', default='loss', required=True)

    course_line_id = fields.Many2one(
        related='attendance_id.course_line_id',
        string='Línea de curso',
        store=True
    )
    teacher_ids = fields.Many2many(
        comodel_name='hr.employee',
        related='course_line_id.teacher_ids',
        string='Profesores',
    )
    school_id = fields.Many2one(
        comodel_name='res.partner',
        related='attendance_id.school_id',
        string='Escuela',
    )