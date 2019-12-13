# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CountryState(models.Model):
    """ Add Municipalities reference in State """
    _name = 'res.country.state'
    _inherit = 'res.country.state'

    municipality_ids = fields.One2many('res.country.state.municipality', 'state_id', 'Municipalities')


class StateMunicipality(models.Model):
    _name = 'res.country.state.municipality'
    _description="State municipalities"

    state_id = fields.Many2one('res.country.state', 'State', required=True, 
        help='Name of the State to which the municipality belongs')
    name = fields.Char('Municipality', required=True, 
        help='Municipality name')
    code = fields.Char('Code', size=5, required=True, 
        help='Municipality code in max. five chars.')
    zone = fields.Selection([
            ('freezone', 'Zona Libre de la Fronteriza'),
            ('singlezone', 'Salarios Mínimos Generales'),
        ], string="Zone", default="singlezone",
        help="Determines where the Commercial Zone should be placed")
