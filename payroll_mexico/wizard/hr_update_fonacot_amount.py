# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class UpdateFonacotWizard(models.TransientModel):
    _name = "hr.update.fonacot"
    
    def _default_employee_id(self):
        employee_id=self.env['hr.employee'].search([('id','in',self.env.context.get('active_ids', []))])
        return employee_id
    
    #Columns
    employee_id = fields.Many2one('hr.employee', string='Employees', default=_default_employee_id)
    amount_debt = fields.Float(string="Deuda actual")
    amount_dues = fields.Float(string="Monto de cuota de descuento")
    name = fields.Char(string="Concepto")

    def update_fonacot_amount(self):
        '''
        Este metodo calculara la diferencia de montos de fonacot y creara movimientos corresmondientes para actualizar los montos.
        '''
        amount_debt = self.amount_debt - self.employee_id.fonacot_amount_debt
        self.employee_id.ammount_discounted = self.amount_dues
        self.employee_id.last_amount_update = self.amount_debt
        self.env['hr.credit.employee.account'].create_move(description='Actualización de montos:%s' % self.name, credit=amount_debt, employee=self.employee_id)
