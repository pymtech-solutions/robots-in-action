# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

import logging

_logger = logging.getLogger(__name__)


class OeAttendance(models.Model):
    _name = 'oe.attendance'
    _description = 'Attendance tracking'
    _order = 'date desc, id desc'

    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today)

    course_line_id = fields.Many2one(
        'oe.school.course.line',
        string='Course',
        required=True,
        ondelete='cascade',
    )

    course_schedule_ids = fields.Many2many(
        related='course_line_id.schedule_ids',
        string='Horario',
    )

    teacher_ids = fields.Many2many(
        related='course_line_id.teacher_ids',
        string='Profesores',
    )

    substitute_teacher_ids = fields.Many2many(
        'hr.employee',
        string="Profesores sustitutos"
    )

    attendance_line_ids = fields.One2many(
        'oe.attendance.line',
        'attendance_id',
        string='Registros de asistencia',
        store=True
    )

    school_id = fields.Many2one(
        related='course_line_id.school_id',
        string='Colegio',
    )

    # Course box
    box_id = fields.Many2one(
        related='course_line_id.box_id',
        string='Caja de materiales',
        help="Caja de materiales"
    )

    # NUEVO SISTEMA DE GESTIÓN DE MATERIALES
    attendance_material_line_ids = fields.One2many(
        'oe.attendance.material.line',
        'attendance_id',
        string='Control de materiales'
    )

    # Movimientos de materiales relacionados
    material_movement_ids = fields.One2many(
        'oe.material.movement',
        'attendance_id',
        string='Movimientos de materiales'
    )

    # Estado de materiales
    materials_status = fields.Selection([
        ('review', 'Borrador'),
        ('closed', 'Cerrado'),
    ], string='Estado de materiales', default='review')

    # Campos computados para resumen
    total_materials_lost = fields.Integer(
        compute='_compute_material_summary',
        string='Total materiales perdidos',
        store=True
    )

    total_materials_damaged = fields.Integer(
        compute='_compute_material_summary',
        string='Total materiales dañados',
        store=True
    )

    has_material_issues = fields.Boolean(
        compute='_compute_material_summary',
        string='Tiene problemas de materiales',
        store=True
    )

    @api.depends('attendance_material_line_ids.lost_quantity', 'attendance_material_line_ids.damaged_quantity')
    def _compute_material_summary(self):
        for record in self:
            record.total_materials_lost = sum(record.attendance_material_line_ids.mapped('lost_quantity'))
            record.total_materials_damaged = sum(record.attendance_material_line_ids.mapped('damaged_quantity'))
            record.has_material_issues = record.total_materials_lost > 0 or record.total_materials_damaged > 0

    @api.model_create_multi
    def create(self, vals):
        record = super().create(vals)
        if record.course_line_id:
            record._generate_attendance_material_lines()
            record._generate_attendance_lines()
        return record

    def write(self, vals):
        """
        Override write para regenerar líneas cuando cambie course_line_id
        """
        result = super().write(vals)
        if 'course_line_id' in vals:
            for record in self:
                record._generate_attendance_material_lines()
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
                lines = [
                    (0, 0, {
                        'student_id': student.id,
                        'attended': False
                    })
                    for student in record.course_line_id.student_ids
                ]

                record.attendance_line_ids = lines


    def _generate_attendance_material_lines(self):
        for record in self:
            # Ensure only one record is processed
            self.ensure_one()

            # Clear previous attendance lines and material lines
            record.attendance_material_line_ids = [(5, 0, 0)]

            if record.course_line_id:
                # Only proceed if there is a material box assigned
                if not (record.box_id and record.box_id.oe_box_line_ids):
                    continue

                material_lines = []
                for box_line in record.box_id.oe_box_line_ids:
                    # Usar exists() para verificar que el registro existe en la BD
                    if box_line.product_id and box_line.product_id.exists():
                        material_lines.append((0, 0, {
                            'product_id': box_line.product_id.id,
                            'original_expected_quantity': box_line.expected_quantity or 0,
                            'original_real_quantity': box_line.real_quantity or 0,
                            'current_quantity': box_line.real_quantity or 0,
                            'lost_quantity': 0,
                            'damaged_quantity': 0,
                        }))

                record.attendance_material_line_ids = material_lines

    def action_view_material_movements(self):
        """
        Acción para ver los movimientos de materiales relacionados con esta asistencia
        """
        self.ensure_one()
        action = {
            'name': f'Movimientos de Materiales - {self.course_line_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'oe.material.movement',
            'view_mode': 'list,form',
            'domain': [('attendance_id', '=', self.id)],
            'context': {
                'default_attendance_id': self.id,
                'default_box_id': self.box_id.id if self.box_id else False,
            },
        }
        return action

    def action_close_materials(self):
        """
        Acción para cerrar la gestión de materiales y actualizar la caja original
        """
        self.ensure_one()
        self._update_original_box()
        self._create_material_movements()
        self.materials_status = 'closed'

    def action_reopen_materials(self):
        """
        Acción para reabrir la asistencia y deshacer los movimientos de los materiales
        """
        self.ensure_one()
        self._undo_update_original_box()
        self._undo_material_movements()
        self.materials_status = 'review'

    def _create_material_movements(self):
        """
        Crear registros de movimientos de materiales
        """
        for material_line in self.attendance_material_line_ids:
            if material_line.lost_quantity > 0 or material_line.damaged_quantity > 0:
                # Crear movimiento por pérdidas
                if material_line.lost_quantity > 0:
                    self.env['oe.material.movement'].create({
                        'box_id': self.box_id.id,
                        'attendance_id': self.id,
                        'product_id': material_line.product_id.id,
                        'quantity_before': material_line.original_real_quantity,
                        'quantity_after': material_line.current_quantity,
                        'quantity_lost': material_line.lost_quantity,
                        'movement_type': 'loss',
                        'notes': material_line.notes,
                    })

                # Crear movimiento por daños
                if material_line.damaged_quantity > 0:
                    self.env['oe.material.movement'].create({
                        'box_id': self.box_id.id,
                        'attendance_id': self.id,
                        'product_id': material_line.product_id.id,
                        'quantity_before': material_line.original_real_quantity,
                        'quantity_after': material_line.current_quantity,
                        'quantity_lost': material_line.damaged_quantity,
                        'movement_type': 'damage',
                        'notes': material_line.notes,
                    })

    def _undo_material_movements(self):
        """
        Deshace los movimientos creados anteriormente en la misma asistencia
        """
        for record in self:
            if record.material_movement_ids:
                record.material_movement_ids.unlink()

    def _update_original_box(self):
        """
        Update the original box with the current quantity of materials.
        """
        for material_line in self.attendance_material_line_ids:
            # Search the corresponding material box
            box_line = self.box_id.oe_box_line_ids.filtered(
                lambda l: l.product_id.id == material_line.product_id.id
            )
            if box_line:
                # Update the real quantity of materials inside the box, not allowing negative quantities
                box_line.real_quantity = max(0, material_line.current_quantity)

    def _undo_update_original_box(self):
        for material_line in self.attendance_material_line_ids:
            # Search the corresponding material box
            box_line = self.box_id.oe_box_line_ids.filtered(
                lambda l: l.product_id.id == material_line.product_id.id
            )
            if box_line:
                # Update the real quantity of materials inside the box, not allowing negative quantities
                box_line.real_quantity = max(0, (material_line.current_quantity + material_line.total_difference))

    @api.model
    def create_attendance_with_lines(self):
        """
        Método para crear asistencias automáticamente via cron.
        """
        try:
            _logger.info("Iniciando creación automática de asistencias...")

            today = fields.Date.today()
            today_weekday = today.weekday()

            weekday_mapping = {
                0: '0',  # Lunes
                1: '1',
                2: '2',
                3: '3',
                4: '4',
                5: '5',
                6: '6'  # Domingo
            }

            today_weekday_str = weekday_mapping.get(today_weekday)
            if not today_weekday_str:
                _logger.warning(f"No se pudo mapear el día de la semana: {today_weekday}")
                return

            # Buscar líneas de curso con horario en el día de hoy
            course_lines = self.env['oe.school.course.line'].search([
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


class OeAttendanceLine(models.Model):
    _name = 'oe.attendance.line'
    _description = 'Attendance Line'

    attendance_id = fields.Many2one(
        'oe.attendance',
        string='Attendance')

    student_id = fields.Many2one(
        'res.partner',
        string='Student')

    attended = fields.Boolean(
        string='Presente',
        default=False)

    student_domain_ids = fields.Many2many(
        'res.partner',
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
