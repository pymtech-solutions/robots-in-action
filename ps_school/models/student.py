# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from psycopg2 import sql, DatabaseError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['display_name', 'email', 'ref', 'vat', 'company_registry']

    # Is it parent or student?
    is_student = fields.Boolean('Es estudiante')
    is_parent = fields.Boolean('Es padre/madre')

    # Related school
    school_id = fields.Many2one(comodel_name='res.partner', string='Colegio', domain="[('is_school', '=', True)]")
    student_course_line_ids = fields.Many2many(
        'school.course.line',
        'course_line_student_rel',  # Misma tabla intermedia
        'student_id',  # Columna para student
        'course_line_id',  # Columna para course_line
        string="Líneas de Curso del Estudiante",
        help="Líneas de curso donde este estudiante está inscrito"
    )

    # Inscription dates and state
    start_date = fields.Date(string='Fecha de alta')
    finish_date = fields.Date(string='Fecha de baja')
    # Todo: auto change status when finish_date is reached
    enrollment_state = fields.Selection([
        ('active', 'Alta'),
        ('inactive', 'Baja'),
    ],
        string='Estado', default='active'
    )

    # Demographic Info
    date_birth = fields.Date(string='Fecha de nacimiento')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Género')

    country_birth = fields.Many2one('res.country', 'Country of Birth')
    country_nationality = fields.Many2one('res.country', 'Nationality')

    # Medical Info
    student_complexion = fields.Char('Complexion')
    student_weight = fields.Float('Weight (in kg)')
    student_height = fields.Float('Height (in cm)')
    student_mark_identify = fields.Text('Mark for Identity')
    student_emergency_contact = fields.Char('Emergency Contact Name')
    student_emergency_phone = fields.Char('Emergency Contact Number')

    @api.depends('parent_id')
    def _compute_parent(self):
        for record in self:
            if record.parent_id.is_student:
                record.is_parent_student = True
            else:
                record.is_parent_student = False

    def attach_document(self, **kwargs):
        pass
