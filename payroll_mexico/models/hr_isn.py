# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp


class HrIsn(models.Model):
    _name = 'hr.isn'
    _description = 'Payroll Tax'
    _order = 'state_id asc, year desc'

    name = fields.Char(string="Name", store=True, readonly=True, copy=False)
    year = fields.Integer(string='Year', size=4, required=True, copy=False)
    country_id = fields.Many2one('res.country', string='Country', store=True,
        default=lambda self: self.env['res.company']._company_default_get().country_id)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    type = fields.Selection([
            ('fixed', 'Fixed fee'),
            ('range', 'Range'),
        ], required=True, default='fixed', string='Type',
        help="Select type of tax by state.\n"\
        "Select 'Fixed fee' if it is a fixed rate.\n"\
        "Select 'Range' if it is a Range.")
    isn_line = fields.One2many('hr.isn.range.line', 'isn_id', string="Entidade Federativas")

    @api.multi
    def name_get(self):
        result = []
        for isn in self:
            name = 'ISN %s %s ' %(isn.state_id.name.upper(), str(isn.year))
            result.append((isn.id, name))
        return result

    @api.constrains('year','isn_line')
    def validate_isn(self):
        for record in self:
            if record.year and len(str(record.year)) != 4:
                raise ValidationError(_('The format of the year is incorrect, configure the format of the year YYYY'))
            if not record.isn_line and record.type == 'range':
                raise ValidationError(_('You must select the range percentage for this state.'))

    @api.model
    def create(self, vals):
        isn = super(HrIsn, self).create(vals)
        isn.name = 'ISN %s %s ' %(isn.state_id.name.upper(), str(isn.year))
        return isn

    @api.multi
    def write(self, vals):
        print (vals)
        print (vals.get('state_id'))
        print (vals.get('state_id'))
        print (vals.get('state_id'))
        print (vals.get('state_id'))
        vals['name'] = vals.get('name')
        return super(HrIsn, self).write(vals)


class HrIsnLine(models.Model):
    _name = 'hr.isn.range.line'
    _order = 'lim_inf'

    isn_id = fields.Many2one('hr.isn', string='ISN')
    lim_inf = fields.Float(string='Lower limit')
    lim_sup = fields.Float(string='Upper limit')
    c_fija = fields.Float(string='Fixed fee') 
    s_excedente = fields.Float(string='Over surplus (%)', digits=dp.get_precision('Excess'),
        help="percent to be applied over the lower limit surplus")

    # ~ @api.onchange('tax_percent')
    # ~ def _onchange_tax_percent(self):
        # ~ return self._tax_percent_get()

    # ~ def _tax_percent_get(self):
        # ~ self.tax_percent_to = self.tax_percent

    # ~ @api.constrains('state_id','tax_percent','tax_percent_to')
    # ~ def validate_isn_line(self):
        # ~ for record in self:
            # ~ if not record.state_id:
                # ~ raise ValidationError(_('The format of the year is incorrect, configure the format of the year YYYY'))
            # ~ if record.tax_percent <= 0:
                # ~ raise ValidationError(_('The tax percentage cannot be less than 0.'))
            # ~ if record.tax_percent_to <= 0:
                # ~ raise ValidationError(_('The tax percentage to cannot be less than 0.'))
