# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

from pygments.lexer import default

_logger = logging.getLogger(__name__)


class OeBoxes(models.Model):
    """ This model represents oe.boxes."""
    _name = 'oe.boxes'
    _description = 'OeBoxes'

    name = fields.Char(string='Nombre', required=True)

    oe_box_line_ids = fields.One2many(
        'oe.boxes.line',
        'oe_box_id',
        copy=True,
        string='Box lines',
    )

    products_ids = fields.Many2many(comodel_name='product.product', string='Productos en caja',
                                    compute='_compute_products_ids')

    # Historial de movimientos de materiales
    material_movement_ids = fields.One2many(
        'oe.material.movement',
        'box_id',
        string='Historial de movimientos'
    )

    diferences = fields.Boolean(
        compute='_compute_diferences',
        string="Diferencias")

    alert_icon = fields.Html(compute='_compute_alert_icon', string="Alert")

    @api.depends('diferences')
    def _compute_alert_icon(self):
        for record in self:
            if record.diferences:
                record.alert_icon = '<span class="text-warning">Diferencia de cantidades⚠️</span>'
            else:
                record.alert_icon = ''

    @api.depends('oe_box_line_ids')
    def _compute_diferences(self):
        for record in self:
            record.diferences = False
            for line in record.oe_box_line_ids:
                if line.real_quantity != line.expected_quantity:
                    record.diferences = True

    @api.depends('oe_box_line_ids')
    def _compute_products_ids(self):
        for record in self:
            record.products_ids = record.oe_box_line_ids.mapped('product_id')

    def action_view_material_movements(self):
        """
        Acción para ver los movimientos de materiales de esta caja
        """
        self.ensure_one()
        action = {
            'name': f'Movimientos de Materiales - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'oe.material.movement',
            'view_mode': 'list,form',
            'domain': [('box_id', '=', self.id)],
            'context': {
                'default_box_id': self.id,
            },
        }
        return action

    def action_reponer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Modificar Materiales',
            'res_model': 'adjust.box.material',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_box_id': self.id
            }
        }


class OeBoxesLine(models.Model):
    """ This model represents oe.boxes.line"""
    _name = 'oe.boxes.line'
    _description = 'OeBoxes.line'

    # Box
    oe_box_id = fields.Many2one(comodel_name='oe.boxes', string='Boxes')
    box_material_movement_ids = fields.One2many(related='oe_box_id.material_movement_ids',
                                                string='Historial de movimientos')

    # Product
    product_id = fields.Many2one(comodel_name='product.product', string='Products')
    image = fields.Binary(related='product_id.image_128', string='Imagen del producto')

    # Expected quantity of product a box should have
    expected_quantity = fields.Integer(string='Cantidad esperada')
    real_quantity = fields.Integer(string='Cantidad real', readonly=True, store=True, compute='_compute_real_quantity')

    # Campo para mostrar diferencias
    quantity_difference = fields.Integer(
        compute='_compute_quantity_difference',
        string='Diferencia',
        store=True
    )

    @api.depends('box_material_movement_ids')
    def _compute_real_quantity(self):
        for record in self:
            movements = record.box_material_movement_ids.filtered(lambda x: x.product_id == record.product_id)
            record.real_quantity = sum(movements.mapped('qty'))

    @api.depends('expected_quantity', 'real_quantity')
    def _compute_quantity_difference(self):
        for record in self:
            record.quantity_difference = record.real_quantity - record.expected_quantity


# Nuevo modelo para líneas de materiales específicas de asistencia
class OeAttendanceMaterialLine(models.Model):
    _name = 'oe.attendance.material.line'
    _description = 'Attendance Material Line'

    attendance_id = fields.Many2one(
        'oe.attendance',
        string='Asistencia',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True
    )

    # Cantidades originales (snapshot al crear la asistencia)
    original_expected_quantity = fields.Integer(string='Cantidad esperada original')
    original_real_quantity = fields.Integer(string='Cantidad real original')

    # Cantidades perdidas/dañadas
    lost_quantity = fields.Integer(string='Cantidad perdida')
    damaged_quantity = fields.Integer(string='Cantidad dañada')

    # Observaciones específicas
    notes = fields.Text(string='Observaciones')
