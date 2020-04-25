# -*- coding: utf-8 -*-

import io
import base64

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class payrollRunDetails(models.TransientModel):
    _name = "payroll.run.details.wizard"
    _description = 'Imprimir detalles de la nómina'

    #Columns
    estructure_ids = fields.Many2many('hr.payroll.structure', required=True,
                                      default=lambda self: self.env['hr.payslip.run'].browse([self._context.get('active_id')]).mapped('slip_ids.struct_id')._ids,
                                      domain=lambda self: [
                                          ('id',
                                           'in',
                                           self.env['hr.payslip.run'].browse([self._context.get('active_id')]).mapped('slip_ids.struct_id')._ids)])
    company_ids = fields.Many2many('res.company',
                                   required=True,
                                   default = lambda self: self.env['hr.payslip.run'].browse([self._context.get('active_id')]).mapped('slip_ids.company_id')._ids,
                                   domain = lambda self: [
                                       ('id',
                                        'in',
                                        self.env['hr.payslip.run'].browse([self._context.get('active_id')]).mapped('slip_ids.company_id')._ids)])
    employer_register_ids = fields.Many2many('res.employer.register', required = True,
                                             default = lambda self: self.env['hr.payslip.run'].browse([self._context.get('active_id')]).mapped('slip_ids.employer_register_id')._ids,
                                             domain=lambda self: [
                                                 ('id',
                                                  'in',
                                                  self.env['hr.payslip.run'].browse([self._context.get('active_id')]).mapped('slip_ids.employer_register_id')._ids)]
                                             )

    def print_report(self):
        '''
        Este metodo imprime el reporte de detalles de la nomina, teniendo en cuenta los criterios seleccionados
        :return:
        '''
        print (self._context)
        print (self._context)
        print (self._context)
        doc_ids = self._context.get('active_ids')
        payslips = self.env['hr.payslip'].search([('payslip_run_id','in',doc_ids),
                                                  ('struct_id','in',self.estructure_ids._ids),
                                                  ('company_id','in',self.company_ids._ids),
                                                  ('employer_register_id','in',self.employer_register_ids._ids)
                                                  ],
                                                 order='complete_name ASC')
        return self.env.ref('payroll_mexico.report_payslip_run_template').report_action(doc_ids, {'slip_ids':payslips._ids})