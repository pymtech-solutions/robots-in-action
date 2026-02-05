# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Schedule(models.Model):
    _name = 'school.schedule'
    _description = 'Schedule'
    _order = 'name'

    name = fields.Char(string='Horario', compute='_compute_name', store=True)
    start_hour = fields.Float(string='Hora de inicio', required=True, default=8.0)
    end_hour = fields.Float(string='Hora de fin', required=True, default=10.0)
    weekday_name = fields.Char(compute='_compute_weekday_name', store=True)
    weekday = fields.Selection([
        ('0', 'Lunes'),
        ('1', 'Martes'),
        ('2', 'Miércoles'),
        ('3', 'Jueves'),
        ('4', 'Viernes'),
        ('5', 'Sábado'),
        ('6', 'Domingo')
    ], string='Día de la semana', default='0', required=True)

    @api.constrains('start_hour', 'end_hour')
    def _check_dates(self):
        """ Verify that the end hour is after the start hour """
        for record in self:
            if record.start_hour and record.end_hour and record.end_hour <= record.start_hour:
                raise ValidationError(f"End hour must be after start hour.")

    @api.depends('weekday')
    def _compute_weekday_name(self):
        weekday_dict = dict(self._fields['weekday'].selection)
        for record in self:
            record.weekday_name = weekday_dict.get(record.weekday, '')

    @api.depends('start_hour', 'end_hour', 'weekday')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.weekday_name} {record.start_hour} - {record.end_hour}"
