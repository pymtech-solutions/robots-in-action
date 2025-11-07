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
        string='Box lines'
    )

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
            'name': 'Reponer Producto',
            'res_model': 'oe.refill.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_box_id': self.id  # pasa el ID de la caja al wizard
            }
        }


class OeBoxesLine(models.Model):
    """ This model represents oe.boxes.line"""
    _name = 'oe.boxes.line'
    _description = 'OeBoxes.line'

    # Box
    oe_box_id = fields.Many2one(
        'oe.boxes',
        string='Boxes'
    )

    # Product
    product_id = fields.Many2one(
        'product.product',
        string='Products'
    )
    image = fields.Binary(
        related='product_id.image_128',
        string='Imagen del producto',
    )

    # Expected quantity of product a box should have
    expected_quantity = fields.Integer(string='Cantidad esperada')
    real_quantity = fields.Integer(string='Cantidad real')

    # Campo para mostrar diferencias
    quantity_difference = fields.Integer(
        compute='_compute_quantity_difference',
        string='Diferencia',
        store=True
    )

    @api.depends('expected_quantity', 'real_quantity')
    def _compute_quantity_difference(self):
        for record in self:
            record.quantity_difference = record.real_quantity - record.expected_quantity


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
        'product.product',
        string='Producto',
        required=True
    )

    # Cantidades
    quantity_before = fields.Integer(string='Cantidad antes')
    quantity_after = fields.Integer(string='Cantidad después')
    quantity_lost = fields.Integer(string='Cantidad perdida')
    quantity_refilled = fields.Integer(string='Cantidad añadida')

    # Información adicional
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)
    notes = fields.Text(string='Observaciones')

    # Tipo de movimiento
    movement_type = fields.Selection([
        ('loss', 'Pérdida'),
        ('damage', 'Daño'),
        ('adjustment', 'Reposición'),
    ], string='Tipo de movimiento', default='loss')

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
        # store=True
    )

    notified = fields.Boolean(string='Notificado', default=False)

    @api.model_create_multi
    def create(self, vals):
        """
        Create modificado para comprobar cuantos materiales perdidos y dañados se tienen que informar
        """
        record = super().create(vals)
        if record.movement_type in ('loss', 'damage'):
            self._check_and_send_alert()

        return record

    def _check_and_send_alert(self):
        """
        Verifica si han habido suficientes piezas dañadas/perdidas para avisar
        """
        domain_losses = [
            ('movement_type', '=', 'loss'),
            ('notified', '=', False)
        ]
        domain_damages = [
            ('movement_type', '=', 'damage'),
            ('notified', '=', False)
        ]
        losses = self.search(domain_losses)
        damages = self.search(domain_damages)

        total_losses = sum(losses.mapped('quantity_lost'))
        total_damages = sum(damages.mapped('quantity_lost'))

        if total_losses >= 10 or total_damages >= 1:
            body = "<h3>Alerta de inventario</h3>"

            if total_losses >= 10:
                subject = '⚠ Alerta de productos perdidos'
                body += "<h4>📦 Productos perdidos</h4><ul>"
                for move in losses:
                    profesores = ", ".join(move.teacher_ids.mapped('name'))
                    body += f"<li>{move.product_id.name} - Marca temporal: {move.date} - Profesores: {profesores} - Colegio: {move.school_id.name} - Caja: {move.box_id.name} - Cantidad: {move.quantity_lost}</li>"
                body += "</ul>"
                self._send_alert_email(body, subject)
                losses.write({'notified': True})

            if total_damages >= 1:
                subject = '⚠ Alerta de productos dañados'
                body += "<h4>💥 Productos dañados</h4><ul>"
                for move in damages:
                    profesores = ", ".join(move.teacher_ids.mapped('name'))
                    body += f"<li>{move.product_id.name} - Marca temporal: {move.date} - Profesores: {profesores} - Colegio: {move.school_id.name} - Caja: {move.box_id.name} - Cantidad: {move.quantity_lost}</li>"
                body += "</ul>"
                self._send_alert_email(body, subject)
                damages.write({'notified': True})

    def _send_alert_email(self, body_html, subject):
        """Envía el correo de alerta con el body y el título recibidos"""
        self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body_html,
            'email_to': 'miguel@loxika.com',
        }).send()


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

    # Cantidades actuales (después de la clase)
    current_quantity = fields.Integer(string='Cantidad actual', compute='_compute_current_quantity')

    # Cantidades perdidas/dañadas
    lost_quantity = fields.Integer(string='Cantidad perdida')
    damaged_quantity = fields.Integer(string='Cantidad dañada')

    # Observaciones específicas
    notes = fields.Text(string='Observaciones')

    # Campo computado para mostrar diferencia total
    total_difference = fields.Integer(
        compute='_compute_total_difference',
        string='Diferencia total',
        store=True
    )

    @api.depends('original_expected_quantity', 'original_real_quantity', 'lost_quantity', 'damaged_quantity')
    def _compute_current_quantity(self):
        for record in self:
            record.current_quantity = record.original_real_quantity - record.lost_quantity - record.damaged_quantity

    @api.depends('original_real_quantity', 'current_quantity', 'lost_quantity', 'damaged_quantity')
    def _compute_total_difference(self):
        for record in self:
            record.total_difference = record.original_real_quantity - record.current_quantity


class OeRefillWizard(models.TransientModel):
    _name = 'oe.refill.wizard'
    _description = 'Wizard para reponer productos'

    product_id = fields.Many2one('product.product', string='Producto', required=True,
                                 domain=lambda self: self._get_product_domain())
    quantity = fields.Integer(string='Cantitad', required=True)
    box_id = fields.Many2one(
        comodel_name='oe.boxes',
        string='Caja',
        required=True
    )
    notes = fields.Text(string="Notas")

    def _get_product_domain(self):
        """
        Consigue todos los productos de la caja
        """
        box_id = self.env.context.get('default_box_id')
        if not box_id:
            return []

        box = self.env['oe.boxes'].browse(box_id)
        product_ids = box.mapped('oe_box_line_ids.product_id.id')
        return [('id', 'in', product_ids)]

    def action_confirm(self):
        """
        Accion para confirmar la reposición y guardar el producto
        """
        self.ensure_one()
        if not self.box_id:
            return

        self._update_box_line()
        self._create_movement_line()

        return {'type': 'ir.actions.act_window_close'}

    def _update_box_line(self):
        """
        Acción para actualizar la caja
        """
        line = self.env['oe.boxes.line'].search([
            ('oe_box_id', '=', self.box_id.id),
            ('product_id', '=', self.product_id.id)
        ], limit=1)

        if line:
            line.real_quantity += self.quantity

        return

    def _create_movement_line(self):
        """
        Crea el respectivo Historial de movimiento para la reposición
        """
        self.env['oe.material.movement'].create({
            'box_id': self.box_id.id,
            'product_id': self.product_id.id,
            'quantity_refilled': self.quantity,
            'movement_type': 'adjustment',
            'notes': self.notes,
        })
