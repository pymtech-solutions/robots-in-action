# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_teacher = fields.Boolean('Es profesor')

    student_ids = fields.Many2many(
        'res.partner',
        string='Estudiantes',
        domain=[('is_student', '=', True)],
        compute='_compute_student_ids',
    )

    school_ids = fields.Many2many(
        'res.partner',
        string='Colegios',
        compute='_compute_school_ids',
        store=True,
    )

    subject_line_ids = fields.Many2many(
        'school.course.line',
        'course_line_teacher_rel',  # Misma tabla intermedia
        'teacher_id',  # Campo inverso
        'course_line_id',  # Campo directo
        string="Líneas de Curso",
        help="Líneas de curso donde este profesor enseña"
    )

    # Schedule
    schedule_ids = fields.Many2many(
        related = "subject_line_ids.schedule_ids",
        string = "Horarios"
    )

    schedule_text = fields.Text(
        string="Resumen de horarios",
        compute="_compute_schedule_text"
    )

    @api.depends('schedule_ids')
    def _compute_schedule_text(self):
        for record in self:
            schedule_text = ""
            for schedule in record.subject_line_ids:
                schedules_related_text = ""
                for schedule_related in schedule.schedule_ids:
                    schedules_related_text += f"{schedule_related.name} - "
                if schedules_related_text:
                    schedule_text += f" -> {schedule.school_id.name} - {schedules_related_text.strip()}\n"
            record.schedule_text = schedule_text

    def _compute_student_ids(self):
        for record in self:
            # Filtrar solo las líneas donde el empleado es profesor y obtener estudiantes
            teacher_lines = self.env['school.course.line'].search([
                ('teacher_ids', 'in', record.id)
            ])

            record.student_ids = teacher_lines.mapped('student_ids')


    @api.depends('subject_line_ids.teacher_ids')
    def _compute_school_ids(self):
        if self.env.context.get('importing_data'):
            return

        for record in self:
            # Filtrar solo las líneas donde el empleado es profesor y obtener escuelas
            teacher_lines = self.env['school.course.line'].search([
                ('teacher_ids', 'in', record.id)
            ])

            record.school_ids = teacher_lines.mapped('school_id')