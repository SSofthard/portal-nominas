from odoo import fields, models, api


class ModelName (models.Model):
    _name = 'hr.table.index.consume.price'
    _description = 'Tabla de indice nacional de precios al consumidor'

    year = fields.Integer(string='Año', default= lambda self: fields.Date.context_today(self).year)
    month = fields.Selection([
                            ('01','Enero'),
                            ('02','Febrero'),
                            ('03','Marzo'),
                            ('04','Abril'),
                            ('05','Mayo'),
                            ('06','Junio'),
                            ('07','Julio'),
                            ('08','Agosto'),
                            ('09','Septiembre'),
                            ('10','Octubre'),
                            ('11','Noviembre'),
                            ('12','Diciembre'),
                        ],string='Mes')
    value = fields.Float(string = 'Valor')

    


