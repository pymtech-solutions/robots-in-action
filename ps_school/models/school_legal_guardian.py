# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SchoolLegalGuardian(models.Model):
    """ This model represents school.legal.tutor."""
    _name = 'school.legal.guardian'
    _description = 'SchoolLegalGuardian'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Tutor', domain=[('is_parent', '=', True)])
    type = fields.Selection(
        selection = [
            ('father', 'Padre'),
            ('mother', 'Madre'),
            ('guardian', 'Tutor'),
            ('other', 'Otro')
        ],
        string='Tipo de tutor'
    )
    invoice = fields.Boolean(string='Facturar')
    student_id = fields.Many2one(comodel_name='res.partner', string='Estudiante', ondelete='cascade')