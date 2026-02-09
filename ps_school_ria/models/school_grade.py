# -*- coding: utf-8 -*-
import base64
import io
import zipfile
from odoo import api, fields, models


class SchoolGrade(models.Model):
    _name = 'school.grade'
    _description = 'Grade'

    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    trimester = fields.Selection([
        ('0', 'Primer trimestre'),
        ('1', 'Segundo trimestre'),
        ('2', 'Tercer trimestre'),
        ('3', 'Primer cuatrimestre'),
        ('4', 'Segundo cuatrimestre'),
    ],
        string='Trimestre',
        default='0'
    )
    trimester_value = fields.Char(compute='_compute_trimester_value', store=True)
    # Academic year
    academic_period = fields.Char(related='course_line_id.academic_period', string="Año academico")
    teacher_ids = fields.Many2many(related='course_line_id.teacher_ids', string='Profesores')
    grade_line_ids = fields.One2many(comodel_name='school.grade.line', inverse_name='grade_id', string="Notas")
    course_line_id = fields.Many2one(comodel_name='school.course.line', string='Curso')
    course_id = fields.Many2one(related='course_line_id.course_id', string='Grupo')
    school_id = fields.Many2one(related='course_line_id.school_id', string='Escuela')
    school_logo = fields.Binary(related='school_id.image_1920', string='Logo de la escuela')
    show_school_logo = fields.Boolean(related='school_id.logo_in_grade', string='Mostrar logo de la escuela')
    program_id = fields.Many2one(related='course_line_id.program_id', string='Programa', required=True)
    state = fields.Selection([('draft', 'Borrador'), ('closed', 'Cerrado')], string='Estado', default='draft')
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Estudiantes',
        compute='_compute_student_ids',
        store=True,
        readonly=False,
    )
    outgoing_mail_id = fields.Many2one(comodel_name='ir.mail_server', string='Correo saliente',
                                   default=lambda self: self.env['ir.mail_server'].search([], limit=1))

    @api.depends('trimester')
    def _compute_trimester_value(self):
        for record in self:
            record.trimester_value = dict(self._fields['trimester'].selection).get(record.trimester, '')

    @api.depends('course_line_id.name', 'trimester')
    def _compute_name(self):
        for record in self:
            trimester_label = dict(self._fields['trimester'].selection).get(record.trimester, '')
            record.name = f"{trimester_label} - {record.course_line_id.name}"

    @api.depends('course_line_id.student_ids', 'state')
    def _compute_student_ids(self):
        for record in self:
            if record.course_line_id and record.state == 'draft':
                record.student_ids = record.course_line_id.student_ids

                if not record.student_ids:
                    # Clear lines if no students are selected
                    record.grade_line_ids = [(5, 0, 0)]
                    return

                # Get existing lines
                existing_lines = record.grade_line_ids
                record.grade_line_ids = [(5, 0, 0)]

                commands = []
                for student in record.student_ids:
                    commands.append((0, 0, {
                        'student_id': student.id,
                    }))

                # Clear lines for students that are no longer in the list
                current_student_ids = self.student_ids.ids
                for line in existing_lines:
                    if line.student_id.id not in current_student_ids:
                        # Delete line
                        commands.append((2, line.id, 0))

                if commands:
                    record.grade_line_ids = commands
            elif not record.course_line_id and record.state == 'draft':
                record.student_ids = False

    def action_close_grade(self):
        self.ensure_one()
        self.state = 'closed'

    def action_open_grade(self):
        self.ensure_one()
        self.state = 'draft'

    @api.depends('student_ids')
    def _compute_grade_lines(self):
        if not self.student_ids:
            # Clear lines if no students are selected
            self.grade_line_ids = [(5, 0, 0)]
            return

        # Get existing lines
        existing_lines = self.grade_line_ids
        existing_student_ids = existing_lines.mapped('student_id.id')

        # Create commands for new students
        commands = []
        for student in self.student_ids:
            if student.id not in existing_student_ids:
                commands.append((0, 0, {
                    'student_id': student.id,
                }))

        # Delete lines for students that are no longer in the list
        current_student_ids = self.student_ids.ids
        for line in existing_lines:
            if line.student_id.id not in current_student_ids:
                commands.append((2, line.id, 0))

        if commands:
            self.grade_line_ids = commands

    def action_mail_unsent_grades(self):
        self.ensure_one()
        for line in self.grade_line_ids:
            if not line.mail_sent_date:
                line.action_mail_grade_report()

    def action_mail_grades(self):
        self.ensure_one()
        for line in self.grade_line_ids:
            line.action_mail_grade_report()

    def action_download_all_reports(self):
        """ Download all grade reports as a ZIP file """
        self.ensure_one()

        if not self.grade_line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin evaluaciones',
                    'message': 'No hay evaluaciones para descargar',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Create a BytesIO object to hold the ZIP file
        zip_buffer = io.BytesIO()

        # Create the ZIP file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            report = self.env.ref('ps_school_ria.school_grade_report_action_report')

            for line in self.grade_line_ids:
                # Generate PDF for each grade line
                pdf_content, _ = report._render_qweb_pdf('ps_school_ria.report_school_grade_report_document',
                                                         res_ids=[line.id])

                # Create a filename for the PDF
                student_name = line.student_id.name or 'Sin_nombre'
                # Clean filename - remove special characters
                student_name = student_name.replace('/', '_').replace('\\', '_')
                filename = f"{student_name}_evaluacion.pdf"

                # Add the PDF to the ZIP file
                zip_file.writestr(filename, pdf_content)

        # Get the ZIP file content
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()
        zip_base64 = base64.b64encode(zip_content)

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Evaluaciones_{self.name or "notas"}.zip',
            'type': 'binary',
            'datas': zip_base64,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/zip'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
