# -*- coding: utf-8 -*-
from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SchoolCourseLine(models.Model):
    _name = 'school.course.line'
    _description = 'Course Line'
    _rec_name = 'name'

    name = fields.Char(string='Línea de Curso', compute='_compute_name', store=False)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=False)
    program_id = fields.Many2one(comodel_name='school.program', string='Programa')
    course_id = fields.Many2one(
        comodel_name='school.course',
        string='Grupo',
        required=True,
        ondelete='cascade'
    )
    related_program_ids = fields.Many2many(
        comodel_name='school.program',
        string='Programas relacionados',
        compute='_compute_related_program_ids',
        store=False,
    )

    @api.depends('course_id')
    def _compute_related_program_ids(self):
        for record in self:
            record.related_program_ids = record.course_id.program_ids

    # School related to this course line
    school_id = fields.Many2one(
        'res.partner',
        string='Escuela',
        required=True,
        domain=[('is_school', '=', True)],
        ondelete='cascade'
    )

    # Students related to this course line
    student_ids = fields.Many2many(
        'res.partner',
        'course_line_student_rel',
        'course_line_id',
        'student_id',
        string="Alumnos",
        domain=[('is_student', '=', True)],
    )
    student_qty = fields.Integer(string='Students', compute='_compute_student_qty', store=True)

    # Profesores asociados a la línea de curso
    teacher_ids = fields.Many2many(
        'hr.employee',
        'course_line_teacher_rel',
        'course_line_id',
        'teacher_id',
        string="Profesores",
        domain=[('is_teacher', '=', True)]
    )

    # Horarios asociados a la línea de curso
    schedule_ids = fields.Many2many(comodel_name='school.schedule', string='Horarios', )
    attendance_ids = fields.One2many(
        comodel_name='school.attendance',
        inverse_name='course_line_id',
        string='Asistencias'
    )
    # Fechas del curso
    start_date = fields.Date(string='Start', required=True)
    end_date = fields.Date(string='End', required=True)
    academic_period = fields.Char(string="Periodo académico")

    # This course material box
    box_ids = fields.Many2many(
        comodel_name='school.box',
        string='Caja de materiales',
        help="Caja de materiales"
    )

    @api.depends('student_ids')
    def _compute_student_qty(self):
        for record in self:
            record.student_qty = len(record.student_ids)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """ Verify that the end date is after the start date """
        for record in self:
            if record.start_date and record.end_date and record.end_date <= record.start_date:
                raise ValidationError(f"End date of program {record.program_id.name} must be after start date.")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-assign school to students when creating course lines"""
        records = super().create(vals_list)
        for record in records:
            record._auto_assign_school_to_students()
        return records

    def write(self, vals):
        """Override write to auto-assign school to students when updating course lines"""
        result = super().write(vals)
        # Si se modificaron los estudiantes o la escuela, actualizar asignación
        if 'student_ids' in vals or 'school_id' in vals:
            for record in self:
                record._auto_assign_school_to_students()
        return result

    def _auto_assign_school_to_students(self):
        """
        Método para asignar automáticamente la escuela a los estudiantes
        cuando se modifica la línea de curso
        """
        if self.env.context.get('importing_data'):
            return
        if self.school_id and self.student_ids:
            students_to_update = self.student_ids.filtered(lambda s: not s.school_id)
            if students_to_update:
                students_to_update.write({'school_id': self.school_id.id})

    # Mantener el onchange para la interfaz
    @api.onchange("student_ids")
    def _onchange_school_id(self):
        if self.student_ids:
            for student in self.student_ids:
                if not student.school_id:
                    student.school_id = self.school_id.id

    @api.onchange('start_date', 'end_date')
    def _compute_academic_period(self):
        for record in self:
            if record.start_date and record.end_date:
                record.academic_period = f"{record.start_date.year} - {record.end_date.year}"
            else:
                record.academic_period = ""

    @api.onchange('course_id')
    def _onchange_course_id(self):
        self.program_id = False
        if self.course_id:
            return {'domain': {'program_id': [('course_id', '=', self.course_id.id)]}}
        else:
            return {'domain': {'program_id': []}}

    def _get_name_parts(self):
        """Método auxiliar para obtener las partes del nombre"""
        name_parts = []
        # Verificar school_id
        if self.school_id:
            try:
                if self.school_id.name:
                    name_parts.append(f"Escuela: {self.school_id.name}")
            except:
                name_parts.append("Escuela")

        # Verificar course_id
        if self.course_id:
            try:
                if self.course_id.name:
                    name_parts.append(f"Grupo: {self.course_id.name}")
            except:
                name_parts.append("Curso")

        # Verificar program_id
        if self.program_id:
            try:
                if self.program_id.name:
                    name_parts.append(f"Programa: {self.program_id.name}")
            except:
                name_parts.append("Programa")

        return name_parts

    @api.depends('course_id', 'program_id', 'school_id')
    def _compute_name(self):
        for record in self:
            if record.env.context.get('importing_data'):
                continue
            try:
                name_parts = record._get_name_parts()
                if name_parts:
                    record.name = ' - '.join(name_parts)
                else:
                    record.name = f'Línea #{record.id}' if record.id else 'Nueva Línea'
            except Exception as e:
                _logger.error(f"Error computing name for course line {record.id}: {str(e)}")
                record.name = f'Error #{record.id}' if record.id else 'Error'

    @api.depends('course_id', 'program_id', 'school_id')
    def _compute_display_name(self):
        for record in self:
            if record.env.context.get('importing_data'):
                continue
            try:
                name_parts = record._get_name_parts()
                if name_parts:
                    record.display_name = ' - '.join(name_parts)
                else:
                    record.display_name = f'Línea #{record.id}' if record.id else 'Nueva Línea'
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error computing display_name for course line {record.id}: {str(e)}")
                record.display_name = f'Error #{record.id}' if record.id else 'Error'

    def name_get(self):
        """Override name_get como respaldo"""
        result = []
        for record in self:
            try:
                name_parts = record._get_name_parts()
                if name_parts:
                    name = ' - '.join(name_parts)
                else:
                    name = f'Línea #{record.id}' if record.id else 'Nueva Línea'
                result.append((record.id, name))
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error in name_get for course line {record.id}: {str(e)}")
                result.append((record.id, f'Error #{record.id}' if record.id else 'Error'))
        return result
