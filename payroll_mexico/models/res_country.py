# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CountryState(models.Model):
    """ Add Municipalities reference in State """
    _name = 'res.country.state'
    _inherit = 'res.country.state'

    municipality_ids = fields.One2many('res.country.state.municipality', 'state_id', 'Municipalities')


class MunicipalityZone(models.Model):
    _name = 'res.municipality.zone'
    _description = "Municipality zone"
    _rec_name = "municipality_id"
    _order = 'date_from desc'

    municipality_id = fields.Many2one('res.country.state.municipality', 'Municipality',
        help='Municipality')
    zone = fields.Selection([
            ('freezone', 'Zona Libre de la Frontera Norte'),
            ('singlezone', 'Salarios Mínimos Generales'),
        ], string="Zone", default="singlezone", required=True,
        help="Geographical distribution of minimum wages in Mexico.")
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date",)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('zone_date_from_uniq', 'unique(municipality_id, zone, date_from)', 'Already zone for this municipality!')
    ]


class StateMunicipality(models.Model):
    _name = 'res.country.state.municipality'
    _description="State municipalities"

    state_id = fields.Many2one('res.country.state', 'State', required=True, 
        help='Name of the State to which the municipality belongs')
    name = fields.Char('Municipality', required=True, 
        help='Municipality name')
    code = fields.Char('Code', size=5, required=True, 
        help='Municipality code in max. five chars.')
    zone_ids = fields.One2many('res.municipality.zone', 'municipality_id', string='Zones')
    active = fields.Boolean(default=True)

