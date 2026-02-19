# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SchoolLegalGuardian(models.Model):
    """ This model represents school.legal.tutor."""
    _name = 'school.legal.guardian'
    _description = 'Tutor legal'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Tutor',
        domain=[('is_parent', '=', True)],
        context={'default_school_role': 'parent', 'default_company_type': 'person'},
        required=True
    )
    type = fields.Selection(
        selection = [
            ('father', 'Padre'),
            ('mother', 'Madre'),
            ('guardian', 'Tutor legal'),
            ('grandfather', 'Abuelo'),
            ('grandmother', 'Abuela'),
            ('uncle', 'Tío'),
            ('aunt', 'Tía'),
            ('sibling', 'Hermano/a'),
            ('other', 'Otro')
        ],
        string='Tipo de tutor',
        required=True
    )
    invoice = fields.Boolean(string='Facturar')
    student_id = fields.Many2one(comodel_name='res.partner', string='Estudiante', ondelete='cascade')