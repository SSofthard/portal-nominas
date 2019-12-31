from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class ModelName (models.Model):
    _name = 'hr.table.index.consume.price'
    _description = 'Tabla de indice nacional de precios al consumidor'

    year = fields.Integer(string='Año', default= lambda self: fields.Date.context_today(self).year)
    month = fields.Selection([
                            (1,'Enero'),
                            (2,'Febrero'),
                            (3,'Marzo'),
                            (4,'Abril'),
                            (5,'Mayo'),
                            (6,'Junio'),
                            (7,'Julio'),
                            (8,'Agosto'),
                            (9,'Septiembre'),
                            (10,'Octubre'),
                            (11,'Noviembre'),
                            (12,'Diciembre'),
                        ],string='Mes')
    value = fields.Float(string = 'Valor', digits=dp.get_precision('Payroll Rate'))

    


