# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AttendanceRefillBoxMaterial(models.TransientModel):
    _name = 'attendance.adjust.box.material'
    _description = 'Wizard para reponer productos'

    attendance_id = fields.Many2one(comodel_name='oe.attendance', string='Asistencia')
    attendance_box_ids = fields.Many2many(related='attendance_id.box_ids', string='Cajas de asistencia')
    box_id = fields.Many2one(comodel_name='oe.boxes', string='Caja')
    box_product_ids = fields.Many2many(related='box_id.products_ids', string='Productos de la caja')
    product_id = fields.Many2one(comodel_name='product.product', string='Producto', required=True)

    qty = fields.Integer(string='Cantitad', required=True)
    movement_type = fields.Selection([
        ('loss', 'Pérdida'),
        ('increment', 'Reposición'),
    ], string='Tipo de movimiento', default='loss', required=True)

    notes = fields.Text(string="Notas")

    @api.onchange('box_id')
    def _onchange_box_id(self):
        self.product_id = False
        if self.box_id:
            product_ids = self.box_id.products_ids
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}
        return {'domain': {'product_id': []}}

    def action_confirm(self):
        self.ensure_one()
        if not self.box_id:
            return

        if self.qty <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')

        self._create_movement_line()

        return {'type': 'ir.actions.act_window_close'}

    def _create_movement_line(self):
        """
        Create a new material movement line
        """
        self.env['oe.material.movement'].create({
            'box_id': self.box_id.id,
            'product_id': self.product_id.id,
            'qty': self.qty if self.movement_type == 'increment' else -self.qty,
            'movement_type': self.movement_type,
            'notes': self.notes,
        })
