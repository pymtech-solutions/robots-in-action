# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Student grade
    grade_ids = fields.One2many(comodel_name='school.grade.line', inverse_name='student_id', string='Evaluaciones')

    # Mark if the logo of a school should be displayed in the grade
    logo_in_grade = fields.Boolean(string='Logo en evaluaciones')

    def open_grade_info(self):
        action = self.env.ref('ps_school_ria.grade_action').read()[0]
        action.update({
            'name': 'Grade History',
            'view_mode': 'list',
            'res_model': 'school.grade.line',
            'type': 'ir.actions.act_window',
            'domain': [('student_id', '=', self.id)],
            'context': {
                'default_student_id': self.id,
            }
        })
        return action
