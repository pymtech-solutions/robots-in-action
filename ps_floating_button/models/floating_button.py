# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FloatingButton(models.Model):
    """ This model represents floating.button."""
    _name = 'floating.button'
    _description = 'FloatingButton'

    button_url = fields.Char(string='URL')
    button_x = fields.Integer(string='X')
    button_y = fields.Integer(string='Y')

    @api.model
    def get_button_url(self):
        """ Get floating button url. """
        return self.env['ir.config_parameter'].sudo().get_param(
            'ps_floating_button.button_url',
            default=False
        )

    @api.model
    def get_button_coordinates(self):
        """ Get floating button coordinates. """
        x = self.env['ir.config_parameter'].sudo().get_param('ps_floating_button.button_x', default=1)
        y = self.env['ir.config_parameter'].sudo().get_param('ps_floating_button.button_y', default=1)
        return {'x': x, 'y': y}

