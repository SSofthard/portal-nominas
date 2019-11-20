# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Company(models.Model):

    _inherit = 'res.company'

    business_name = fields.Char("Business Name", copy=False, required=True, copy=False)
    legal_representative_id = fields.Many2one('res.partner', "Legal Representative", required=True, copy=False)
    write_number = fields.Integer("Write Number", copy=False, required=True, copy=False)
    constitution_date = fields.Date("Constitution Date", required=True, copy=False)
    notary_public_number = fields.Integer("Notary Public Number", copy=False, required=True, copy=False)
    public_notary_holder_id = fields.Many2one('res.partner', "Public Notary Holder", required=True, copy=False)
    public_notary_address_id = fields.Many2one('res.partner', "Public Notary Address", required=True, copy=False)
    code = fields.Char("Code", copy=False, required=True, copy=False)
    employer_registry = fields.Char("Employer Registry", copy=False, required=True)
    write_number = fields.Integer("Write Number", copy=False, required=True)
    validity_signature = fields.Date("Validity of Signature", required=True, copy=False)
    state_signature = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),
    ],default="active")
    rfc = fields.Char("RFC", copy=False, required=True)
    partner_ids = fields.One2many('res.company.partner','company_id', "Partners")


class companyPartner(models.Model):

    _name = 'res.company.partner'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    partner_id = fields.Many2one('res.partner', "Partner", required=True, copy=False)

class companyFiel(models.Model):

    _name = 'res.company.fiel'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    partner_id = fields.Many2one('res.partner', "Partner", required=True, copy=False)
