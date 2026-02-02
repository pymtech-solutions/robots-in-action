# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class SchoolSection(models.Model):
    _name = 'school.course.section'
    _description = 'Course Section'
    _rec_name = 'display_name'
    
    name = fields.Char(string='Course', required=True, index=True, translate=True) 
    course_id = fields.Many2one('school.course', string='Course', required=True)
    display_name = fields.Char(string="Display Name")
