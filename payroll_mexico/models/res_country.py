# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CountryState(models.Model):
    """ Add Municipalities reference in State """
    _name = 'res.country.state'
    _inherit = 'res.country.state'

    municipality_ids = fields.One2many('res.country.state.municipality', 'state_id', 'Mayoralty/Municipality')


class MunicipalityZone(models.Model):
    _name = 'res.municipality.zone'
    _description = "Municipality zone"
    _rec_name = "municipality_id"
    _order = 'date_from desc'

    municipality_id = fields.Many2one('res.country.state.municipality', 'Mayoralty/Municipality',
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
    _description="State Mayoralty/Municipality"

    state_id = fields.Many2one('res.country.state', 'State', required=True, 
        help='Name of the State to which the municipality belongs')
    name = fields.Char('Municipality', required=True, 
        help='Municipality name')
    code = fields.Char('Code', size=5, required=True, 
        help='Municipality code in max. five chars.')
    zone_ids = fields.One2many('res.municipality.zone', 'municipality_id', string='Zones')
    suburb_ids = fields.One2many('res.municipality.suburb', 'municipality_id', string='Colonias')
    active = fields.Boolean(default=True)

    def get_salary_min(self, date):
        '''
        Este metodo busca el salario minimo en las tablas de salarios minimos, teniendo en cuenta segun el registro actual y la fecha de vigencia
        '''
        zone = 'border_crossing' if self.env['res.municipality.zone'].search([('municipality_id','=',self.id)]).zone == 'freezone' else 'zone_a'
        salary = getattr(self.env['table.minimum.wages'].search([('date','<=',date)],order='date DESC', limit=1),zone)
        return salary


class StateMunicipalitySuburb(models.Model):
    _name = 'res.municipality.suburb'
    _description="Suburb"

    municipality_id = fields.Many2one('res.country.state.municipality', 'Mayoralty/Municipality',
        help='Municipality')
    name = fields.Char('Nombre', required=True, 
        help='Nombre de la colonia')
    code = fields.Char('Código', size=5, required=False,
        help='Codigo corto de la colonia max. cinco carácteres.')
    active = fields.Boolean(default=True)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.name.upper().replace(' ', '').rjust(5, '0')
            self.code = name[0:5]

    # _sql_constraints = [
    #     ('code_uniq', 'unique(municipality_id, code)',
    #      'Already code for this municipality!')
    # ]


