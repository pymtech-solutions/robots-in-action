# -*- coding: utf-8 -*-
from operator import index

from odoo import api, fields, models


class OeAssessment(models.Model):
    """ This model represents oe.assessment."""
    _name = 'oe.assessment'
    _description = 'OeAssessment'
    _order = 'academic_group_sequence, id'

    academic_group_sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Secuencia para ordenar los grupos"
    )

    name = fields.Char(
        string='Nombre',
        required=True,
    )

    trimester = fields.Selection([
        ('0', 'Primer trimestre'),
        ('1', 'Segundo trimestre'),
        ('2', 'Tercer trimestre'),
    ],
        string='Trimestre',
        default='0'
    )

    # Academic year
    academic_period = fields.Char(
        related='course_line_id.academic_period',
        string="Año academico"
    )

    academic_group = fields.Char(
        string="Grupo academico",
        compute="_compute_academic_group",
        store=True,
        index=True
    )

    # teacher_ids = fields.Many2many(
    #     'hr.employee',
    #     string='Profesores',
    #     domain=[('is_teacher', '=', True)],
    # )

    teacher_ids = fields.Many2many(
        related='course_line_id.teacher_ids',
        string='Profesores',
    )

    assessment_line_ids = fields.One2many(
        'oe.assessment.line',
        'oe_assessment_id',
        string="Notas"
    )

    course_line_id = fields.Many2one(
        'oe.school.course.line',
        string='Curso',
    )

    course_id = fields.Many2one(
        related='course_line_id.course_id',
        string='Grupo'
    )

    school_id = fields.Many2one(
        related='course_line_id.school_id',
        string='Escuela',
    )

    program_id = fields.Many2one(
        related='course_line_id.program_id',
        string='Programa',
    )

    student_ids = fields.Many2many(
        'res.partner',
        string='Estudiantes',
        compute='_compute_student_ids',
        store=True,  # Almacenar en BD para mejor rendimiento
        readonly=False,  # Permitir edición si es necesario
    )

    @api.depends('course_line_id.student_ids')
    def _compute_student_ids(self):
        for record in self:
            if record.course_line_id:
                record.student_ids = record.course_line_id.student_ids

                if not record.student_ids:
                    record.assessment_line_ids = [(5, 0, 0)]  # Limpiar todas las líneas
                    return

                # Obtener líneas existentes
                existing_lines = record.assessment_line_ids
                existing_student_ids = existing_lines.mapped('student_id.id')
                record.assessment_line_ids = [(5, 0, 0)]

                commands = []
                for student in record.student_ids:
                    commands.append((0, 0, {
                        'student_id': student.id,
                    }))

                # Eliminar líneas de estudiantes que ya no están
                current_student_ids = self.student_ids.ids
                for line in existing_lines:
                    if line.student_id.id not in current_student_ids:
                        commands.append((2, line.id, 0))  # Eliminar línea

                if commands:
                    record.assessment_line_ids = commands


            else:
                record.student_ids = False

    @api.depends('course_line_id', 'trimester', 'academic_period')
    def _compute_academic_group(self):
        for record in self:
            if record.academic_period and record.trimester:
                trimestre_label = dict(self._fields['trimester'].selection).get(record.trimester, '')
                record.academic_group = f"{trimestre_label} - {record.academic_period}"
            else:
                record.academic_group = ""

    @api.depends('student_ids')
    def _onchange_student_ids(self):
        if not self.student_ids:
            self.assessment_line_ids = [(5, 0, 0)]  # Limpiar todas las líneas
            return

        # Obtener líneas existentes
        existing_lines = self.assessment_line_ids
        existing_student_ids = existing_lines.mapped('student_id.id')

        # Crear comandos para nuevos estudiantes
        commands = []
        for student in self.student_ids:
            if student.id not in existing_student_ids:
                commands.append((0, 0, {
                    'student_id': student.id,
                }))

        # Eliminar líneas de estudiantes que ya no están
        current_student_ids = self.student_ids.ids
        for line in existing_lines:
            if line.student_id.id not in current_student_ids:
                commands.append((2, line.id, 0))  # Eliminar línea

        if commands:
            self.assessment_line_ids = commands


class OeAssessmentLine(models.Model):
    _name = 'oe.assessment.line'
    _description = 'OeAssessmentLine'

    oe_assessment_id = fields.Many2one(
        'oe.assessment',
        string='Asistencia',
        required=True,
        ondelete='cascade'
    )

    student_id = fields.Many2one(
        'res.partner',
        string='Estudiante',
        domain=[('is_student', '=', True)],
    )

    # Constant for reusable selection values
    ASSESSMENT_LEVELS = [
        ('1', 'Suspendido'),
        ('2', 'Necesita mejorar'),
        ('3', 'Bien'),
        ('4', 'Muy bien'),
        ('5', 'Excelente'),
    ]

    cognitive_capacity = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Capacidad cognitiva',
        default='3'
    )

    dexterity = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Destreza manual',
        default='3'
    )

    logic_reasoning = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Lógica y razonamiento',
        default='3'
    )

    creativity = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Creatividad',
        default='3'
    )

    learning_improvement = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Mejora en el aprendizaje',
        default='3'
    )

    teamwork = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Trabajo grupal',
        default='3'
    )

    motivation = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Motivación',
        default='3'
    )

    attitude = fields.Selection(
        ASSESSMENT_LEVELS,
        string='Actitud',
        default='3'
    )

    comments = fields.Text(
        string='Observaciones'
    )
