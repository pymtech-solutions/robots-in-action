# -*- coding: utf-8 -*-
from odoo import api, fields, models


# Nuevo modelo para gestionar movimientos de materiales
class OeMaterialMovement(models.Model):
    _name = 'oe.material.movement'
    _description = 'Material Movement'
    _order = 'date desc, id desc'

    # Relaciones principales
    box_id = fields.Many2one(
        'oe.boxes',
        string='Caja',
        required=True
    )

    attendance_id = fields.Many2one(
        'oe.attendance',
        string='Asistencia',
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto',
        required=True,
        ondelete='cascade'
    )

    qty = fields.Integer(string='Cambio')
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)
    notes = fields.Text(string='Observaciones')

    # Tipo de movimiento
    movement_type = fields.Selection([
        ('loss', 'Pérdida'),
        ('increment', 'Reposición'),
    ], string='Tipo de movimiento', default='loss', required=True)

    # Campos relacionados para facilidad
    course_line_id = fields.Many2one(
        related='attendance_id.course_line_id',
        string='Línea de curso',
        store=True
    )

    teacher_ids = fields.Many2many(
        comodel_name='hr.employee',
        related='course_line_id.teacher_ids',
        string='Profesores',
        # store=True
    )

    school_id = fields.Many2one(
        comodel_name='res.partner',
        related='attendance_id.school_id',
        string='Escuela',
    )