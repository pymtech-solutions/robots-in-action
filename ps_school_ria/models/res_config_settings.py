# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    school_grade_mail_subject = fields.Char(
        string='Asunto del correo',
        config_parameter='ps_school_ria.school_grade_mail_subject',
        default='Reporte de Calificaciones - {student_name}',
        help='Puedes usar {student_name} como variable'
    )
    
    # CAMBIADO DE Html A Char
    school_grade_mail_body = fields.Char(
        string='Cuerpo del correo',
        config_parameter='ps_school_ria.school_grade_mail_body',
        default='<p>Estimado/a,</p><p>Adjunto encontrará el reporte de calificaciones de {student_name}.</p><br/><p>Saludos cordiales,</p>',
        help='Puedes usar {student_name} como variable. Puedes usar etiquetas HTML'
    )