# -*- coding: utf-8 -*-
from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
import logging

_logger = logging.getLogger(__name__)


class OeProgram(models.Model):
    _name = 'oe.program'
    _description = 'Program'
    _order = 'name'

    name = fields.Char(
        string='Nombre del programa',
        required=True,
    )

    course_id = fields.Many2many(
        'oe.school.course',
        string='Curso',
    )


class OeSchoolCourse(models.Model):
    _name = 'oe.school.course'
    _description = 'Course'
    _order = 'name'

    name = fields.Char(
        string='Nombre del curso',
        required=True,
        index=True,
        translate=True
    )

    # Programas asociados
    program_ids = fields.Many2many(
        'oe.program',
        string="Programas"
    )

    # Líneas de curso (One2many - un curso puede tener varias líneas en diferentes escuelas)
    course_line_ids = fields.One2many(
        'oe.school.course.line',
        'course_id',
        string="Líneas de Curso"
    )

    # Color del curso, se escoge un color aleatorio entre 1 y 11
    color = fields.Integer(default=lambda self: randint(1, 11))


# Linea de curso
class OeSchoolCourseLine(models.Model):
    _name = 'oe.school.course.line'
    _description = 'Course Line'
    _rec_name = 'name'

    # Campo 'name' calculado para el display
    name = fields.Char(
        string='Línea de Curso',
        compute='_compute_name',
        store=False,
    )

    # Campo display_name explícito
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=False,
    )

    # CAMPOS CLAVE: Relaciones principales
    course_id = fields.Many2one(
        'oe.school.course',
        string='Grupo',
        required=True,
        ondelete='cascade'
    )

    related_program_ids = fields.Many2many(
        'oe.program',
        string='Programas relacionados',
        compute='_compute_related_program_ids',
        store=False,
    )

    @api.depends('course_id')
    def _compute_related_program_ids(self):
        for record in self:
            record.related_program_ids = record.course_id.program_ids

    program_id = fields.Many2one(
        'oe.program',
        string='Programa',
    )

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
    schedule_ids = fields.Many2many(
        'oe.school.schedule',
        string='Horarios',
    )

    attendance_ids = fields.One2many(
        'oe.attendance',
        'course_line_id',
        string='Asistencias'
    )

    # Fechas del curso
    start_date = fields.Date(string='Fecha de inicio')
    end_date = fields.Date(string='Fecha de fin')

    # Academic year
    academic_period = fields.Char(
        string="Periodo academico",
    )

    # This course material box
    box_id = fields.Many2one(
        'oe.boxes',
        string='Caja de materiales',
        help="Caja de materiales"
    )

    # Materials inside the related box
    box_line_ids = fields.One2many(
        related='box_id.oe_box_line_ids',
        string='Materiales en la caja',
        readonly=False,
    )

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


# Modelo nuevo para horarios
class OeSchedule(models.Model):
    _name = 'oe.school.schedule'
    _description = 'Schedule'
    _order = 'name'

    name = fields.Char(string='Horario', compute='_compute_name', store=True)

    # Horarios
    start_hour = fields.Float(
        string='Hora de inicio',
        required=True,
        default=8.0,
    )
    end_hour = fields.Float(
        string='Hora de fin',
        required=True,
        default=10.0,
    )
    weekday = fields.Selection([
        ('0', 'Lunes'),
        ('1', 'Martes'),
        ('2', 'Miércoles'),
        ('3', 'Jueves'),
        ('4', 'Viernes'),
        ('5', 'Sábado'),
        ('6', 'Domingo')
    ], string='Día de la semana', default='0', required=True)

    weekday_name = fields.Char(compute='_compute_weekday_name', store=True)

    @api.depends('weekday')
    def _compute_weekday_name(self):
        weekday_dict = dict(self._fields['weekday'].selection)
        for record in self:
            record.weekday_name = weekday_dict.get(record.weekday, '')

    @api.depends('start_hour', 'end_hour', 'weekday')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.weekday_name} {record.start_hour} - {record.end_hour}"
