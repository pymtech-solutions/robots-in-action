# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path

_logger = logging.getLogger(__name__)


class School(models.Model):
    _inherit = "res.partner"

    is_school = fields.Boolean(string='Es colegio')

    course_line_ids = fields.One2many(
        comodel_name='school.course.line',
        inverse_name='school_id',
        string="Líneas de Curso",
    )
    student_qty = fields.Integer(string='Alumnos totales', compute='_compute_student_qty', store=True)
    active_student_qty = fields.Integer(string='Alumnos de alta', compute='_compute_student_qty', store=True)
    inactive_student_qty = fields.Integer(string='Alumnos de baja', compute='_compute_student_qty', store=True)

    @api.depends('course_line_ids.student_ids', 'course_line_ids.student_ids.enrollment_state')
    def _compute_student_qty(self):
        for school in self:
            school.student_qty = len(school.course_line_ids.mapped('student_ids'))
            school.active_student_qty = len(
                school.course_line_ids.mapped('student_ids').filtered(lambda s: s.enrollment_state == 'active'))
            school.inactive_student_qty = len(
                school.course_line_ids.mapped('student_ids').filtered(lambda s: s.enrollment_state == 'inactive'))
