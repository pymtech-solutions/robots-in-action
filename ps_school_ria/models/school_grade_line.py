# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SchoolGradeLine(models.Model):
    _name = 'school.grade.line'
    _description = 'Grade Line'

    grade_id = fields.Many2one(
        comodel_name='school.grade',
        string='Asistencia',
        required=True,
        ondelete='cascade'
    )

    student_id = fields.Many2one(
        comodel_name='res.partner',
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
    comments = fields.Text(string='Observaciones')

    def action_open_form(self):
        """ Opens the form view of the model."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'school.grade.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    def action_download_grade_report(self):
        """ Download individual grade report as PDF """
        self.ensure_one()
        return self.env.ref('ps_school_ria.school_grade_report_action_report').report_action(self)
