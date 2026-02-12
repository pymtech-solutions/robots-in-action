# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

from pygments.lexer import default

_logger = logging.getLogger(__name__)


class SchoolBox(models.Model):
    """ This model represents the material boxes that can be used in a specific class."""
    _name = 'school.box'
    _description = 'Boxes'

    name = fields.Char(string='Nombre', required=True)
    teacher_ids = (fields.Many2many(comodel_name='hr.employee', string='Profesores asignado',
                                    domain=[('is_teacher', '=', True)]))

    box_line_ids = fields.One2many(
        comodel_name='school.box.line',
        inverse_name='box_id',
        copy=True,
        string='Box lines',
    )

    products_ids = fields.Many2many(comodel_name='product.product', string='Productos en caja',
                                    compute='_compute_products_ids')

    material_movement_ids = fields.One2many(
        'school.material.movement',
        'box_id',
        string='Historial de movimientos'
    )

    total_material_movement = fields.Integer(
        compute='_compute_total_material_movement',
        string='Total de movimientos',
        store=True
    )

    alert_icon = fields.Html(compute='_compute_alert_icon', string="Alert", store=True)
    differences = fields.Boolean(string='Diferencias de materiales', compute='_compute_alert_icon', store=True)

    @api.depends('material_movement_ids')
    def _compute_total_material_movement(self):
        for record in self:
            record.total_material_movement = len(record.material_movement_ids)

    def action_initial_replenisment_all(self):
        unreplenished_boxes = self.env['school.box'].search([('material_movement_ids', '=', False)])
        for box in unreplenished_boxes:
            box.action_initial_replenishment()

    def action_initial_replenishment(self):
        if not self.material_movement_ids:
            return self.env['school.material.movement'].create([{
                'box_id': self.id,
                'notes': 'Reabastecimiento inicial de materiales.',
                'movement_type': 'increment',
                'product_id': line.product_id.id,
                'qty': line.expected_quantity
            } for line in self.box_line_ids])

    @api.depends('box_line_ids.real_quantity', 'box_line_ids.expected_quantity')
    def _compute_alert_icon(self):
        """ Calculate if there are any differences in materials """
        for record in self:
            has_difference = any(
                line.real_quantity < line.expected_quantity
                for line in record.box_line_ids
            )
            record.differences = has_difference
            record.alert_icon = '<span class="text-warning">Diferencia de cantidades⚠️</span>' if has_difference else ''

    @api.depends('box_line_ids')
    def _compute_products_ids(self):
        for record in self:
            record.products_ids = record.box_line_ids.mapped('product_id')

    def action_view_material_movements(self):
        """
        Acción para ver los movimientos de materiales de esta caja
        """
        self.ensure_one()
        action = {
            'name': f'Movimientos de Materiales - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'school.material.movement',
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


class SchoolBoxLine(models.Model):
    """ This model represents the materials inside of a school box"""
    _name = 'school.box.line'
    _description = 'Material line inside a box'

    # Box
    box_id = fields.Many2one(comodel_name='school.box', string='Boxes')
    box_material_movement_ids = fields.One2many(related='box_id.material_movement_ids',
                                                string='Historial de movimientos')

    # Product
    product_id = fields.Many2one(comodel_name='product.product', string='Products')
    image = fields.Binary(related='product_id.image_128', string='Imagen del producto')

    # Expected quantity of product a box should have
    expected_quantity = fields.Integer(string='Cantidad esperada')
    real_quantity = fields.Integer(string='Cantidad real', readonly=True, store=True,
                                   compute='_compute_real_quantity')

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
class AttendanceMaterialLine(models.Model):
    _name = 'school.attendance.material.line'
    _description = 'Attendance Material Line'

    attendance_id = fields.Many2one(
        comodel_name='school.attendance',
        string='Asistencia',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
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
