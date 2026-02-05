# -*- coding: utf-8 -*-
from odoo import api, fields, models


class User(models.Model):
    _inherit = 'res.users'

    school_ids = fields.Many2many(related='employee_ids.school_ids', string='Colegios')
