# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64

class SchoolGradeLine(models.Model):
    _name = 'school.grade.line'
    _description = 'Grade Line'

    grade_id = fields.Many2one(
        comodel_name='school.grade',
        string='Asistencia',
        required=True,
        ondelete='cascade'
    )
    print_record = fields.Boolean(related='grade_id.can_print_grades')
    outgoing_mail_id = fields.Many2one(related='grade_id.outgoing_mail_id', readonly=True)
    mail_sent_date = fields.Date(string='Enviado', readonly=True)

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

    @api.depends('grade_id')
    def _compute_print_record(self):
        for record in self:
            if record.grade_id.show_school_logo and not record.grade_id.school_logo:
                record.print_record = False
            else:
                record.print_record = True

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

    def action_mail_grade_report(self):
        """ Send individual grade report as email with customizable template """
        self.ensure_one()
        
        if not self.outgoing_mail_id:
            raise UserError('No se ha configurado un servidor de correo saliente para enviar el reporte de calificaciones.')
        elif not self.student_id.email and not self.student_id.parent_id.email:
            raise UserError('El estudiante no tiene correo electrónico configurado.')

        # Get mail templates from configuration
        subject_template, body_template = self.grade_id._get_mail_template_values()
        
        # Replace placeholders in templates
        student_name = self.student_id.name or 'Estudiante'
        subject = subject_template.replace('{student_name}', student_name)
        body = body_template.replace('{student_name}', student_name)
        
        # Generate PDF report
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'ps_school_ria.school_grade_report_action_report',
            self.ids
        )

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Reporte_Calificaciones_{student_name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.student_id.email or self.student_id.parent_id.email,
            'email_from': self.outgoing_mail_id.smtp_user,
            'attachment_ids': [(6, 0, [attachment.id])],
            'mail_server_id': self.outgoing_mail_id.id,
        }

        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        self.mail_sent_date = fields.Date.today()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Correo enviado',
                'message': 'El reporte de calificaciones ha sido enviado exitosamente.',
                'type': 'success',
                'sticky': False,
            }
        }