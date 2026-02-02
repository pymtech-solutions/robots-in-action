# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SchoolAttendanceLine(models.Model):
    _name = 'school.attendance.line'
    _description = 'Attendance Line'

    attendance_id = fields.Many2one(comodel_name='school.attendance', string='Attendance')
    school_id = fields.Many2one(related='attendance_id.school_id', string='Escuela')
    date = fields.Date(related='attendance_id.date', string='Fecha')
    course_id = fields.Many2one(related='attendance_id.course_line_id', string='Curso')
    student_id = fields.Many2one(comodel_name='res.partner', string='Student')
    attended = fields.Boolean(string='Presente', default=False)
    student_domain_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Estudiantes',
        domain=[('is_student', '=', True)],
        compute='_compute_student_id_domain',
    )

    @api.depends('attendance_id.course_line_id')
    def _compute_student_id_domain(self):
        for line in self:
            if line.attendance_id and line.attendance_id.course_line_id:
                # Directly assign the student_ids from the course_line_id
                line.student_domain_ids = line.attendance_id.course_line_id.student_ids
            else:
                # Important to clear if no course
                line.student_domain_ids = False
