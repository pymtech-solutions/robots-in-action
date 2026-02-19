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
    is_student = fields.Boolean('Es estudiante', compute='_compute_school_role', store=True)
    is_parent = fields.Boolean('Es padre/madre', compute='_compute_school_role', store=True)
    is_teacher = fields.Boolean('Es profesor', compute='_compute_school_role', store=True)
    is_school = fields.Boolean(string='Es colegio', compute='_compute_school_role', store=True)
    school_role = fields.Selection([
        ('teacher', 'Profesor'),
        ('student', 'Estudiante'),
        ('parent', 'Padre/Madre'),
        ('school', 'Colegio')
    ],
        string='Rol escolar'
    )

    school_id = fields.Many2one(comodel_name='res.partner', string='Colegio', domain="[('is_school', '=', True)]")
    student_course_line_ids = fields.Many2many(
        'school.course.line',
        'course_line_student_rel',  # Misma tabla intermedia
        'student_id',  # Columna para student
        'course_line_id',  # Columna para course_line
        string="Líneas de curso del estudiante",
        help="Líneas de curso donde este estudiante está inscrito"
    )
    guardian_ids = fields.One2many(comodel_name='school.legal.guardian', string='Tutores legales',
                                   inverse_name='student_id')

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
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('other', 'Otro'),
    ], string='Género')

    country_birth = fields.Many2one('res.country', string='País de nacimiento')
    country_nationality = fields.Many2one('res.country', string='Nacionalidad')

    # Medical Info
    student_complexion = fields.Char(string='Complexión')
    student_weight = fields.Float(string='Peso (en kg)')
    student_height = fields.Float(string='Altura (en cm)')
    student_mark_identify = fields.Text(string='Señas particulares')
    student_emergency_contact = fields.Char(string='Contacto de emergencia')
    student_emergency_phone = fields.Char(string='Teléfono de emergencia')

    @api.constrains('guardian_ids')
    def _check_dates(self):
        for record in self:
            if record.guardian_ids:
                # Only one guardian can be marked for invoice
                if len(record.guardian_ids.filtered(lambda g: g.invoice)) > 1:
                    raise ValidationError("Solo se puede marcar un padre para facturar.")

    @api.depends('school_role', 'employee_ids', 'employee_ids.is_teacher')
    def _compute_school_role(self):
        for record in self:
            record.is_school = False
            record.is_student = False
            record.is_parent = False
            record.is_teacher = False

            if record.employee_ids and record.employee_ids[0].is_teacher:
                record.school_role = 'teacher'
            elif record.employee_ids and not record.employee_ids[0].is_teacher:
                record.school_role = None

            if record.school_role == 'teacher':
                record.is_teacher = True
            elif record.school_role == 'student':
                record.is_student = True
            elif record.school_role == 'parent':
                record.is_parent = True
            elif record.school_role == 'school':
                record.is_school = True