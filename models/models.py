# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = "res.partner"

    birthday = fields.Date(string='Birthday')
    # gender_id = fields.Many2one(
    #     'hr.employee.gender', string='Gender')
    gender = fields.Selection(
        [('Male', 'Male'), ('Female', 'Female'), ('Unknow', 'Unknow')], string='Gender')

    def get_value_gender(self):
        return ['Male', 'Female', 'Unknow']


class Gender(models.Model):
    _name = 'hr.employee.gender'

    name = fields.Char('Gender of The Employee')
    gender = fields.Char(string="Gender", default="Male")
