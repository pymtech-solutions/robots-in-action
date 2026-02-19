# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SchoolProgram(models.Model):
    _name = 'school.program'
    _description = 'Programa'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del programa', required=True)
    course_id = fields.Many2many(comodel_name='school.course', string='Curso')
    subject_ids = fields.Many2many(comodel_name='school.subject', string='Materias')
