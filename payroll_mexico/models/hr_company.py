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
    employer_register_ids = fields.One2many('res.employer.register','company_id', "Employer Register")
    rfc = fields.Char("RFC", copy=False, required=True)
    partner_ids = fields.One2many('res.company.partner','company_id', "Partners")
    fiel_csd_ids = fields.One2many('res.company.fiel.csd','company_id', "FIEL & CSD")
    branch_offices_ids = fields.One2many('res.company.branch.offices','company_id', "Branch Offices")
    bank_account_ids = fields.One2many('bank.account.company','company_id', "Bank account", required=True)
    power_attorney_ids = fields.One2many('company.power.attorney','company_id', "Power Attorney", required=True)


class employerRegister(models.Model):

    _name = 'res.employer.register'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    employer_registry = fields.Char("Employer Registry", copy=False, required=True)
    electronic_signature = fields.Many2one('ir.attachment', "Electronic Signature", required=True)
    validity_signature = fields.Date("Validity of Signature", required=True, copy=False)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    
class companyPartner(models.Model):

    _name = 'res.company.partner'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    partner_id = fields.Many2one('res.partner', "Partner", required=True, copy=False)

class companyFielCsd(models.Model):

    _name = 'res.company.fiel.csd'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    type = fields.Selection([
        ('fiel', 'FIEL'),
        ('csd', 'CSD'),],default="Type", required=True)
    track = fields.Char("Track", copy=False, required=True)
    effective_date = fields.Date("Effective date", required=True, copy=False)
    cer = fields.Many2one('ir.attachment', ".cer", required=True)
    key = fields.Many2one('ir.attachment', ".key", required=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    predetermined = fields.Boolean('Predetermined', copy=False)
    
class branchOffices(models.Model):

    _name = 'res.company.branch.offices'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    partner_id = fields.Many2one('res.partner', "Branch Offices", required=True, copy=False)

class bankDetailsCompany(models.Model):
    _name = "bank.account.company"
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    bank_id = fields.Many2one('res.bank', "Bank", required=True)
    beneficiary = fields.Char("Beneficiary", copy=False, required=True)
    bank_account = fields.Char("Bank account", copy=False, required=True)
    reference = fields.Char("Reference", copy=False, required=True)
    predetermined = fields.Boolean("Predetermined", copy=False, required=False)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ],default="active")
    
    _sql_constraints = [
        ('predetermined_uniq', 'unique (company_id,predetermined)', "There is already a default account number for this company.!"),
    ]
    
class companyPowerAttorney(models.Model):
    _name = "company.power.attorney"
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    bank_id = fields.Many2one('res.bank', "Bank", required=True)
    beneficiary = fields.Char("Beneficiary", copy=False, required=True)
    bank_account = fields.Char("Bank account", copy=False, required=True)
    reference = fields.Char("Reference", copy=False, required=True)
    predetermined = fields.Boolean("Predetermined", copy=False, required=False)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ],default="active")
    
    _sql_constraints = [
        ('predetermined_uniq', 'unique (company_id,predetermined)', "There is already a default account number for this company.!"),
    ]
    
