# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SchoolSubject(models.Model):
    """ This model represents school.subject."""
    _name = 'school.subject'
    _description = 'Asignatura'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')