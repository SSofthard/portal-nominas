# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Company(models.Model):

    _inherit = 'res.company'
    

    business_name = fields.Char("Business Name", copy=False, required=True, )
    legal_representative_id = fields.Many2one('res.partner', "Legal Representative", required=True, copy=False)
    write_number = fields.Integer("Write Number", copy=False, required=True)
    constitution_date = fields.Date("Constitution Date", required=True, copy=False)
    public_notary_holder_id = fields.Many2one('res.partner', "Public Notary Holder", required=True, copy=False)
    public_notary_address_id = fields.Many2one('res.partner', "Public Notary Address", required=True, copy=False)
    code = fields.Char("Code", copy=False, required=True)
    employer_register_ids = fields.One2many('res.employer.register','company_id', "Employer Register")
    rfc = fields.Char("RFC", copy=False, required=True)
    partner_ids = fields.One2many('res.company.partner','company_id', "Partners")
    fiel_csd_ids = fields.One2many('res.company.fiel.csd','company_id', "FIEL & CSD")
    branch_offices_ids = fields.One2many('res.company.branch.offices','company_id', "Branch Offices")
    bank_account_ids = fields.One2many('bank.account.company','company_id', "Bank account", required=True)
    power_attorney_ids = fields.One2many('company.power.attorney','company_id', "Power Attorney", required=True)
    country_id=fields.Many2one(default=lambda self: self.env['res.country'].search([('code','=','MX')]))

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "And there is a company with this code.!"),
    ]
    
class employerRegister(models.Model):

    _name = 'res.employer.register'
    
    company_id = fields.Many2one('res.company', "Company")
    employer_registry = fields.Char("Employer Registry", copy=False, required=True)
    electronic_signature = fields.Many2many('ir.attachment', string="Electronic Signature", required=True)
    validity_signature = fields.Date("Validity of Signature", required=True, copy=False)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    
    @api.multi
    def action_revoked(self):
        for employer in self:
            employer.state = 'revoked'
            
    @api.multi
    def action_timed_out(self):
        for employer in self:
            employer.state = 'timed_out'
    
class companyPartner(models.Model):

    _name = 'res.company.partner'
    
    company_id = fields.Many2one('res.company', "Company")
    partner_id = fields.Many2one('res.partner', "Partner", required=True, copy=False)

class companyFielCsd(models.Model):

    _name = 'res.company.fiel.csd'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    type = fields.Selection([
        ('fiel', 'FIEL'),
        ('csd', 'CSD'),],default="Type", required=True)
    track = fields.Char("Track", copy=False, required=True)
    effective_date = fields.Date("Effective date", required=True, copy=False)
    cer = fields.Many2many('ir.attachment', string=".cer", required=True)
    key = fields.Many2many('ir.attachment', string=".key", required=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    predetermined = fields.Boolean('Predetermined', copy=False)
    
    _sql_constraints = [
        ('predetermined_uniq', 'unique (company_id,predetermined,type)', "A default record for the type of certificate already exists.!"),
    ]
    
    @api.multi
    def action_revoked(self):
        for power in self:
            power.state = 'revoked'
            
    @api.multi
    def action_timed_out(self):
        for power in self:
            power.state = 'timed_out'
    
class branchOffices(models.Model):

    _name = 'res.company.branch.offices'
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    partner_id = fields.Many2one('res.partner', "Branch Offices", required=True, copy=False)

class bankDetailsCompany(models.Model):
    _name = "bank.account.company"
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    bank_id = fields.Many2one('res.bank', "Bank", required=True)
    account_holder = fields.Char("Account holder", copy=False, required=True)
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
    
    @api.multi
    def action_active(self):
        for account in self:
            account.state = 'active'
            
    @api.multi
    def action_inactive(self):
        for account in self:
            account.state = 'inactive'
    
class companyPowerAttorney(models.Model):
    _name = "company.power.attorney"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    company_id = fields.Many2one('res.company', "Company", required=True)
    representative_id = fields.Many2one('res.partner', "Representative", required=True, copy=False)
    book = fields.Integer("Book", copy=False, required=True)
    public_deed_number = fields.Char("Instrument or public deed number.", copy=False, required=True)
    public_notary  = fields.Many2one('res.partner', "Public Notary", required=True, copy=False)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    
    @api.multi
    def action_revoked(self):
        for power in self:
            power.state = 'revoked'
            
    @api.multi
    def action_timed_out(self):
        for power in self:
            power.state = 'timed_out'
    
    @api.multi
    def _document_count(self):
        for power in self:
            document_ids = self.env['ir.attachment'].sudo().search([('res_model','=','company.power.attorney'),('res_id','=',power.id)])
            power.document_count = len(document_ids)

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [
            ('res_model','=','company.power.attorney'),('res_id','=',self.id)]
        return {
            'name': _('Documents Power Attorney'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_company_document_id': '%s','default_res_model':'company.power.attorney','default_res_model':%s'}" % (self.company_id.id,self.id)
        }

    document_count = fields.Integer(compute='_document_count', string='# Documents')

    
class Partner(models.Model):
    _inherit = 'res.partner'
    
    legal_representative = fields.Boolean(string='Legal Representative?', copy=False)
    public_notary = fields.Boolean(string='Public Notary?', copy=False)
    notary_public_number = fields.Integer("Notary Public Number", copy=False, required=True)
    notary_public = fields.Boolean(string='Notary Public?', copy=False)
    partner_company = fields.Boolean(string='Partner Company?', copy=False)
    branch_offices = fields.Boolean(string='Branch Offices?', copy=False)
    country_id=fields.Many2one(default=lambda self: self.env['res.country'].search([('code','=','MX')]))
