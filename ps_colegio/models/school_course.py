# -*- coding: utf-8 -*-
from odoo import api, fields, models
from random import randint


class SchoolCourse(models.Model):
    _name = 'school.course'
    _description = 'Course'
    _order = 'name'

    name = fields.Char(string='Nombre del curso', required=True, index=True)
    program_ids = fields.Many2many(comodel_name='school.program', string="Programas")
    course_line_ids = fields.One2many(
        comodel_name='school.course.line',
        inverse_name='course_id',
        string="Líneas de Curso"
    )
    color = fields.Integer(default=lambda self: randint(1, 11))
