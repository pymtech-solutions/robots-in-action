# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path

_logger = logging.getLogger(__name__)


class School(models.Model):
    _inherit = "res.partner"

    is_school = fields.Boolean(string='School')

    # Líneas de curso específicas de esta escuela
    course_line_ids = fields.One2many(
        'oe.school.course.line',
        'school_id',
        string="Líneas de Curso",
    )