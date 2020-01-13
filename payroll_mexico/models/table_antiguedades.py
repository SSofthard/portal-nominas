# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class TablasAntiguedadesLine(models.Model):
    _name = 'tablas.antiguedades.line'

    @api.one
    def _get_factor_integration(self):
        '''
        Este metodo calcula el factor de integración en base a la antiguedad del empleado
        '''
        self.factor = ((((self.vacaciones*(self.prima_vac/100))+365+self.aguinaldo)/365)-1)*100

    form_id = fields.Many2one('tablas.antiguedades', string='Vacaciones y aguinaldos')
    antiguedad = fields.Float('Antigüedad/Años', digits=dp.get_precision('Excess'))
    vacaciones = fields.Float('Vacaciones/Días', digits=dp.get_precision('Excess'))
    prima_vac = fields.Float('Prima vacacional (%)', digits=dp.get_precision('Excess'))
    aguinaldo = fields.Float('Aguinaldo/Días', digits=dp.get_precision('Excess'))
    factor = fields.Float('Factor de integración', digits=dp.get_precision('Payroll Rate'), compute='_get_factor_integration')

class TablaAntiguedadesAguinaldos(models.Model):
    _name = 'tablas.antiguedades'
    
    name = fields.Char("Nombre")
    tabla_antiguedades = fields.One2many(comodel_name='tablas.antiguedades.line', inverse_name='form_id')

