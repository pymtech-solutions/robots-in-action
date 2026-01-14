# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OeProgram(models.Model):
    _name = 'oe.program'
    _description = 'Program'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del programa',
        required=True,
    )

    course_id = fields.Many2many(
        'oe.school.course',
        string='Curso',
    )
