# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .tool_convert_numbers_letters import numero_to_letras

class Contract(models.Model):

    _inherit = 'hr.contract'

    code = fields.Char('Code',required=True)
    type_id = fields.Many2one(string="Type Contract")
    type_contract = fields.Selection(string="Type", related="type_id.type", invisible=True)
    productivity_bonus = fields.Float('Productivity bonus', required=False)
    attendance_bonus = fields.Float('Attendance bonus', required=False)
    punctuality_bonus = fields.Float('Punctuality Bonds', required=False)
    social_security = fields.Float('Social security', required=False)
    company_id = fields.Many2one('res.company', default = ['employee_id','=', False])
    previous_contract_date = fields.Date('Previous Contract Date', help="Start date of the previous contract for antiquity.")
    power_attorney_id = fields.Many2one('company.power.attorney',string="Power Attorney")
    
    @api.onchange('company_id')
    def onchange_default_power_attorney(self):
        for contract in self:
            power = self.env['company.power.attorney'].search([('company_id','=',contract.company_id.id),('state','in',['valid']),('predetermined','=',True)])
            if power:
                contract.power_attorney_id = power.id
            else:
                power = self.env['company.power.attorney'].search([('company_id','=',contract.company_id.id),('state','in',['valid'])], limit=1)
                if power:
                    contract.power_attorney_id = power.id 
    
    @api.onchange('employee_id')
    def onchange_search_company_id(self):
        domain={}
        vals=[]
        value={}
        for company in self.employee_id.company_ids:
            vals.append(company.company_id.id)
        if vals:
            domain={'company_id': [('id','in', vals)]}
        else:
            domain={'company_id': [('id','in', vals)]}
            value['company_id']=False
        return {'value': value, 'domain': domain}
    
    
    def print_contract(self):
        contract_dic = {}
        for contract in self:
            report=self.type_id.report_id
            if not report:
                msg="The type of contract does not have an assigned report"
                raise  UserError(_(msg))
            date = self.date_start
            previous_contract_date = ''
            if self.type_id.type == 'with_seniority':
                previous_contract_date = self.previous_contract_date.strftime('%d')+' del mes de '+self.previous_contract_date.strftime('%B').upper()+' de '+self.previous_contract_date.strftime('%Y')
            
            contract_dic[contract.id]=[date.strftime('%d')+' días del mes de '+date.strftime('%B').upper()+' de '+numero_to_letras(int(date.strftime('%Y'))).lower(),previous_contract_date]
        data={
            'contract_data':contract_dic
            }
        return self.env.ref('payroll_mexico.report_contract_type_template').report_action(self,data)

