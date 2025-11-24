# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FloatingButton(models.Model):
    """ This model represents floating.button."""
    _name = 'floating.button'
    _description = 'FloatingButton'

    button_url = fields.Char(string='URL')
