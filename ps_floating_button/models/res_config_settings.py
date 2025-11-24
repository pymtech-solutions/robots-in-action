# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    button_url = fields.Char(string='URL del botón', default='https://www.example.com', required=True,
                             config_parameter='ps_floating_button.button_url',
                             help='URL a la que el botón redirige cuando se hace clic')
