# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

import logging

_logger = logging.getLogger(__name__)


class SchoolAttendance(models.Model):
    _name = 'school.attendance'
    _description = 'Registro de Asistencia'
    _order = 'date desc, id desc'

    name = fields.Char(string='Asistencia', compute='_compute_name', store=True)
    date = fields.Date(string='Fecha', required=True, default=fields.Date.today)
    course_line_id = fields.Many2one(
        comodel_name='school.course.line',
        string='Curso',
        required=True,
        ondelete='cascade',
    )
    course_schedule_ids = fields.Many2many(related='course_line_id.schedule_ids', string='Horario')
    teacher_ids = fields.Many2many(related='course_line_id.teacher_ids', string='Profesores')
    substitute_teacher_ids = fields.Many2many(comodel_name='hr.employee', string="Profesores Sustitutos")
    attendance_line_ids = fields.One2many(
        comodel_name='school.attendance.line',
        inverse_name='attendance_id',
        string='Líneas de Asistencia',
        store=True
    )

    school_id = fields.Many2one(related='course_line_id.school_id', string='Colegio', )
    program_id = fields.Many2one(related='course_line_id.program_id', string='Programa')
    program_subject_ids = fields.Many2many(comodel_name='school.subject', string='Materias del Programa',
                                           compute='_compute_program_subjects', store=True)
    subject_id = fields.Many2one(comodel_name='school.subject', string='Materia')
    box_ids = fields.Many2many(related='course_line_id.box_ids', string='Caja de Materiales')
    material_movement_ids = fields.One2many(
        comodel_name='school.material.movement',
        inverse_name='attendance_id',
        string='Movimientos de Materiales'
    )

    materials_status = fields.Selection([
        ('review', 'Borrador'),
        ('closed', 'Cerrado'),
    ], string='Estado', default='review')

    @api.depends('program_id')
    def _compute_program_subjects(self):
        for record in self:
            record.program_subject_ids = record.course_line_id.program_id.subject_ids

    def action_adjust_materials(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajustar Materiales',
            'res_model': 'attendance.adjust.box.material',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_attendance_id': self.id,
                'default_box_id': self.box_ids[:1].id,
            }
        }

    @api.model_create_multi
    def create(self, vals):
        record = super().create(vals)
        if record.course_line_id:
            record._generate_attendance_lines()
        return record

    def write(self, vals):
        result = super().write(vals)
        if 'course_line_id' in vals:
            for record in self:
                # Generate attendance lines after course line change
                record._generate_attendance_lines()
        return result

    def _generate_attendance_lines(self):
        for record in self:
            # Ensure only one record is processed
            self.ensure_one()

            # Clear previous attendance lines
            record.attendance_line_ids = [(5, 0, 0)]

            # Create a new attendance line for each student in the course line
            if record.course_line_id:
                lines = [(0, 0, {
                    'student_id': student.id,
                    'attended': False
                }) for student in record.course_line_id.student_ids]

                record.attendance_line_ids = lines

    @api.depends('date', 'course_line_id')
    def _compute_name(self):
        for record in self:
            record.name = f'Asistencia {record.date} - {record.course_line_id.name}'

    def action_view_material_movements(self):
        """
        Acción para ver los movimientos de materiales relacionados con esta asistencia
        """
        self.ensure_one()
        action = {
            'name': f'Movimientos de Materiales - {self.course_line_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'school.material.movement',
            'view_mode': 'list,form',
            'domain': [('attendance_id', '=', self.id)],
            'context': {
                'default_attendance_id': self.id,
                'default_box_id': self.box_id.id if self.box_id else False,
            },
        }
        return action

    def action_close_attendance(self):
        self.ensure_one()
        self.materials_status = 'closed'

    def action_reopen_attendance(self):
        self.ensure_one()
        self.materials_status = 'review'

    def action_undo_material_movements(self):
        for record in self:
            if record.material_movement_ids:
                record.material_movement_ids.unlink()

    @api.model
    def create_attendance_with_lines(self):
        """Create attendance records for today's course lines automatically via cron job"""
        try:
            _logger.info("Iniciando creación automática de asistencias...")

            today = fields.Date.today()
            today_weekday = today.weekday()

            weekday_mapping = {
                0: '0',  # Monday
                1: '1',
                2: '2',
                3: '3',
                4: '4',
                5: '5',
                6: '6'  # Sunday
            }

            today_weekday_str = weekday_mapping.get(today_weekday)
            if not today_weekday_str:
                _logger.warning(f"No se pudo mapear el día de la semana: {today_weekday}")
                return

            # Buscar líneas de curso con horario en el día de hoy
            course_lines = self.env['school.course.line'].search([
                ('schedule_ids.weekday', '=', today_weekday_str)
            ])

            _logger.info(f"Encontradas {len(course_lines)} líneas de curso para hoy")

            created_count = 0
            for course_line in course_lines:
                _logger.info(f"Procesando curso: {course_line.id}")

                existing_attendance = self.search([
                    ('date', '=', today),
                    ('course_line_id', '=', course_line.id)
                ])

                if existing_attendance:
                    _logger.info(f"Ya existe asistencia para el curso {course_line.id} en fecha {today}")
                    continue

                attendance = self.create({
                    'date': today,
                    'course_line_id': course_line.id,
                })

                _logger.info(f"Creada asistencia ID: {attendance.id} con estudiantes y materiales automáticamente")
                created_count += 1

            _logger.info(f"Proceso completado. Creadas {created_count} asistencias nuevas")

        except Exception as e:
            _logger.error(f"Error en create_attendance_with_lines: {str(e)}")
            raise