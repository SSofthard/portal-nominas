# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .tool_convert_numbers_letters import numero_to_letras

class Contract(models.Model):

    _inherit = 'hr.contract'

    code = fields.Char('Code',required=True, default= lambda self: self.env['ir.sequence'].next_by_code('Contract'))
    type_id = fields.Many2one(string="Type Contract")
    type_contract = fields.Selection(string="Type", related="type_id.type", invisible=True)
    productivity_bonus = fields.Float('Productivity bonus', required=False)
    attendance_bonus = fields.Float('Attendance bonus', required=False)
    punctuality_bonus = fields.Float('Punctuality Bonds', required=False)
    social_security = fields.Float('Social security', required=False)
    company_id = fields.Many2one('res.company', default = ['employee_id','=', False])
    previous_contract_date = fields.Date('Previous Contract Date', help="Start date of the previous contract for antiquity.")
    power_attorney_id = fields.Many2one('company.power.attorney',string="Power Attorney")
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free'),
        ], string='Contracting Regime', required=True, default="2")
    
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
    
    def print_contract(self):
        contract_dic = {}
        mensaje = []
        for contract in self:
            employee=contract.employee_id
            if not employee:
                mensaje.append('Debe llenar el campo empleado en la ficha del Contrato \n')
            
            company=contract.company_id
            if not company:
                mensaje.append('Debe llenar el campo Compañia en el contrato \n')
            
            birthday=contract.employee_id.birthday
            if not birthday:
                mensaje.append('Debe llenar la fecha de nacimiento en la ficha de empleado \n')
            
            const_date=contract.company_id.constitution_date
            if not const_date:
                mensaje.append('Debe llenar la fecha Constitucion de la compañia \n')
            
            title_emplo=contract.employee_id.title.shortcut
            if not title_emplo:
                mensaje.append('Debe llenar el titulo en la ficha de empleado \n')
            
            direccion=contract.employee_id.address_home_id
            if not direccion:
                mensaje.append('Debe llenar la dirección de la ficha de empleado \n')
            
            dir_state=contract.employee_id.address_home_id.state_id
            if not dir_state:
                mensaje.append('Debe llenar el estado en la dirección de la ficha de empleado \n')
            
            report=self.type_id.report_id
            if not report:
                mensaje.append('Debe llenar el campo reporte dentro de la categoria de empleado \n')
                
            job=self.job_id
            if not job:
                mensaje.append('Debe llenar el campo puesto de trabajo en la ficha del contrato \n')
                
            rfc=self.employee_id.rfc
            if not rfc:
                mensaje.append('Debe llenar el campo RFC en la ficha del empleado \n')
                
            curp=self.employee_id.curp
            if not curp:
                mensaje.append('Debe llenar el campo CURP en la ficha del empleado \n')
                
            country=self.employee_id.country_id
            if not country:
                mensaje.append('Debe llenar el campo país en la ficha del empleado \n')
                
            nationality=self.employee_id.country_id.nationality
            if not nationality:
                mensaje.append('Debe llenar el campo nacionalidad donde se registra país en la parte técnica del sistema \n')
                
            if len(mensaje):
                msg="".join(mensaje)
                raise  UserError(_(msg))
            date = self.date_start
            previous_contract_date = ''
            if self.type_id.type == 'with_seniority':
                previous_contract_date = self.previous_contract_date.strftime('%d')+' del mes de '+self.previous_contract_date.strftime('%B').upper()+' de '+self.previous_contract_date.strftime('%Y')
            
            contract_dic[contract.id]=[date.strftime('%d')+' días del mes de '+date.strftime('%B').upper()+' de '+numero_to_letras(int(date.strftime('%Y'))).lower(),
            previous_contract_date,contract.employee_id.birthday.strftime('%d/%m/%Y'),
            contract.company_id.constitution_date.strftime('%d')+' de '+contract.company_id.constitution_date.strftime('%B').upper()+' de '+contract.company_id.constitution_date.strftime('%Y'),
            date.strftime('%d')+' de '+date.strftime('%B').upper()+' '+date.strftime('%Y'),
            date.strftime('%d')+' días del mes de '+date.strftime('%B').upper()+' de '+date.strftime('%Y'),
            ]
        data={
            'contract_data':contract_dic
            }
        return self.env.ref('payroll_mexico.report_contract_type_template').report_action(self,data)

