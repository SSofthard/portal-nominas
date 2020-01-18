# -*- coding: utf-8 -*-

import datetime
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from odoo.addons.payroll_mexico.pyfiscal.generate_company import GenerateRfcCompany

from odoo.addons.payroll_mexico.models.zip_data import zip_data

class Company(models.Model):

    _inherit = 'res.company'

    def _default_country(self):
        country_id = self.env['res.country'].search([('code','=','MX')], limit=1)
        return country_id

    business_name = fields.Char("Business Name", copy=False, required=True, )
    legal_representative_id = fields.Many2one('res.partner', "Legal Representative", required=True, copy=False)
    write_number = fields.Integer("Write Number", copy=False, required=True)
    constitution_date = fields.Date("Constitution Date", required=True, copy=False)
    public_notary_holder_id = fields.Many2one('res.partner', "Public Notary Holder", required=True, copy=False)
    public_notary_address_id = fields.Many2one('res.partner', "Public Notary Address", required=True, copy=False)
    code = fields.Char("Code", copy=False, required=True)
    employer_register_ids = fields.One2many('res.employer.register','company_id', "Employer Register")
    rfc = fields.Char("RFC", copy=False, required=False)
    partner_ids = fields.One2many('res.company.partner','company_id', "Partners")
    fiel_csd_ids = fields.One2many('res.company.fiel.csd','company_id', "FIEL & CSD")
    branch_offices_ids = fields.One2many('res.company.branch.offices','company_id', "Branch Offices")
    bank_account_ids = fields.One2many('bank.account.company','company_id', "Bank account", required=True)
    power_attorney_ids = fields.One2many('company.power.attorney','company_id', "Power Attorney", required=True)
    country_id = fields.Many2one('res.country', compute='_compute_address', inverse='_inverse_country', string="Country", default=lambda self: self.env.user.company_id.country_id.id)
    municipality_id = fields.Many2one('res.country.state.municipality', string='Municipality')
    suburb_id = fields.Many2one('res.municipality.suburb', string='Colonia')
    tax_regime = fields.Selection(
        selection=[('601', _('General de Ley Personas Morales')),
                   ('603', _('Personas Morales con Fines no Lucrativos')),
                   ('605', _('Sueldos y Salarios e Ingresos Asimilados a Salarios')),
                   ('606', _('Arrendamiento')),
                   ('608', _('Demás ingresos')),
                   ('609', _('Consolidación')),
                   ('610', _('Residentes en el Extranjero sin Establecimiento Permanente en México')),
                   ('611', _('Ingresos por Dividendos (socios y accionistas)')),
                   ('612', _('Personas Físicas con Actividades Empresariales y Profesionales')),
                   ('614', _('Ingresos por intereses')),
                   ('616', _('Sin obligaciones fiscales')),
                   ('620', _('Sociedades Cooperativas de Producción que optan por diferir sus ingresos')),
                   ('621', _('Incorporación Fiscal')),
                   ('622', _('Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras')),
                   ('623', _('Opcional para Grupos de Sociedades')),
                   ('624', _('Coordinados')),
                   ('628', _('Hidrocarburos')),
                   ('607', _('Régimen de Enajenación o Adquisición de Bienes')),
                   ('629', _('De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales')),
                   ('630', _('Enajenación de acciones en bolsa de valores')),
                   ('615', _('Régimen de los ingresos por obtención de premios')),],
        string=_('Tax regime'), 
    )
    origen_recurso = fields.Selection(
        selection=[('IP', _('Ingresos Propios')),
                   ('IF', _('Ingresos Federales')),
                   ('IM', _('Ingresos Mixtos')),
                   ],
        string=_('Origen de recursos'),
    )

    @api.onchange('zip')
    def _onchange_zip(self):       
        if self.zip and self.zip not in zip_data.postal_code:
            self.zip = False
            warning = {}
            title = False
            message = False
            if True:
                title = _("Código Postal incorrecto")
                message = 'Debe ingresar un Código Postal valido'
                warning = {
                    'title': title,
                    'message': message
                }
                return {'warning': warning}
 
    _sql_constraints = [
        ('code_uniq', 'unique (code)', "And there is a company with this code.!"),
    ]

    @api.constrains('bank_account_ids','bank_account_ids.predetermined','employer_register_ids',
        'employer_register_ids.employer_registry','employer_register_ids.company_id',
        'power_attorney_ids','power_attorney_ids.predetermined','power_attorney_ids.company_id',
        'fiel_csd_ids','fiel_csd_ids.predetermined','fiel_csd_ids.company_id')
    def _check_predetermined(self):
        # By @jeisonpernia1
        for record in self:
            # Validar numero de registro patronal único
            employer_register_ids = record.employer_register_ids.filtered(lambda l: l.state == 'valid').mapped('employer_registry')
            if len(list(set(employer_register_ids))) != len(employer_register_ids):
                raise ValidationError(_('Advertencia! \
                        Solo debe existir un Registro Patronal con el mismo número.'))
            #Validar única cuenta bancaria predeterminada 
            bank_account_ids = record.bank_account_ids.filtered(lambda l: l.predetermined == True)
            if len(bank_account_ids) > 1:
                raise ValidationError(_('Advertencia! \
                        Solo debe existir una cuenta predeterminada'))
            #Validar único poder notariado predeterminada 
            power_attorney_ids = record.power_attorney_ids.filtered(lambda l: l.predetermined == True and l.state == 'valid')
            if len(power_attorney_ids) > 1:
                raise ValidationError(_('Advertencia! \
                        Solo debe existir un Poder Notariado predeterminado.'))
            #Validar único certificado predeterminada 
            fiel_csd_ids = record.fiel_csd_ids.filtered(lambda l: len(l.search([('predetermined','=',True),('type','=',l.type)])) > 1)
            if len(fiel_csd_ids) > 1:
                raise ValidationError(_('Advertencia! \n'
                        'Ya existe un registro predeterminado para el tipo de certificado selecionado.'))

    def get_rfc_data(self):
        kwargs = {
            "complete_name": self.business_name,
            "constitution_date": self.constitution_date.strftime('%d-%m-%Y'),
        }
        rfc = GenerateRfcCompany(**kwargs)
        self.rfc = rfc.data
    
    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            self.municipality_id = False
            
    @api.onchange('municipality_id')
    def onchange_municipality_id(self):
        if self.municipality_id:
            self.suburb_id = False


class employerRegister(models.Model):
    _name = 'res.employer.register'
    _rec_name='employer_registry'
    
    def _default_country(self):
        country_id = self.env['res.country'].search([('code','=','MX')], limit=1)
        return country_id

    
    company_id = fields.Many2one('res.company', "Company")
    employer_registry = fields.Char("Employer Registry", copy=False, required=True)
    electronic_signature = fields.Many2many('ir.attachment', string="Electronic Signature", required=True)
    validity_signature = fields.Date("Validity of Signature", required=True, copy=False)
    
    delegacion_id = fields.Many2one('res.company.delegacion', "Delegacion", required=True)
    subdelegacion_id = fields.Many2one('res.company.subdelegacion', "Sub-Delegacion", required=True)
    economic_activity = fields.Char("Economic activity", copy=False, required=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    geographic_area = fields.Selection([
        ('1', 'General Minimum Wages'),
        ('2', 'Northern border'),], 'Geographic area',required=True)
    risk_factor_ids = fields.One2many('res.group.risk.factor','employer_id', string="Factor de riesgo anual")
    job_risk = fields.Selection([
        ('1', 'Clase I'),
        ('2', 'Clase II'),
        ('3', 'Clase III'),
        ('4', 'Clase IV'),
        ('5', 'Clase V'),
        ('99', 'No aplica'),
        ], string='Job risk', required=True)
    subcide_reimbursement_agreement = fields.Boolean("Subcide reimbursement agreement")
    country_id = fields.Many2one('res.country', default=_default_country, string="Country")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string="Fed. State")
    zip = fields.Char(string="ZIP")
    municipality_id = fields.Many2one('res.country.state.municipality', string='Municipality')
    suburb_id = fields.Many2one('res.municipality.suburb', string='Colonia')
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    sector_economico_id = fields.Many2one('res.company.sector_economico', 
                    "Fracción de RT", 
                    required=False)


    _sql_constraints = [
        ('employer_registryt_uniq', 'UNIQUE (employer_registry)', "Ya hay un número patronal registrado con el número ingresado!"),
    ]


    @api.multi
    def action_revoked(self):
        for employer in self:
            employer.state = 'revoked'
            
    @api.multi
    def action_timed_out(self):
        for employer in self:
            employer.state = 'timed_out'
    
    def get_risk_factor(self, date_factor):
        risk_factor = 0.0
        for group in self:
            if group.risk_factor_ids:
                factor_ids = group.risk_factor_ids.filtered(
                    lambda factor: date_factor >= factor.date_from \
                    and date_factor <= factor.date_to)
                if factor_ids:
                    risk_factor = factor_ids.mapped('risk_factor')[0]
                else:
                    risk_factor = 0.0
        return risk_factor


class HrGroupRiskFactor(models.Model):
    _name = "res.group.risk.factor"
    _description="Annual Risk Factor"
    
    employer_id = fields.Many2one('res.employer.register', string="group")
    risk_factor = fields.Float(string="Risk Factor", required=True, digits=dp.get_precision('Risk'))
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)


class companyDelegacion(models.Model):

    _name = 'res.company.delegacion'
    
    name = fields.Char('Delegacion', required=True)
    code = fields.Char('Code', required=True)
    subdelegacion_ids = fields.One2many('res.company.subdelegacion', 'delegacion_id', 'Sub-Delegacion')


class companySubDelegacion(models.Model):

    _name = 'res.company.subdelegacion'
    
    delegacion_id = fields.Many2one('res.company.delegacion', "Delegacion")
    name = fields.Char('Sub-Delegacion', required=True)
    code = fields.Char('Code', required=True)


class companyPartner(models.Model):

    _name = 'res.company.partner'
    
    company_id = fields.Many2one('res.company', "Company")
    partner_id = fields.Many2one('res.partner', "Partner", required=True, copy=False)


class companyFielCsd(models.Model):

    _name = 'res.company.fiel.csd'
    
    company_id = fields.Many2one('res.company', "Company", required=False)
    type = fields.Selection([
        ('fiel', 'FIEL'),
        ('csd', 'CSD'),],default="Type", required=True)
    track = fields.Char("Track", copy=False, required=True)
    effective_date = fields.Date("Effective date", required=True, copy=False)
    cer = fields.Many2many('ir.attachment','cer_attachment_rel','cer_id','attachment_id', string=".cer", required=True)
    key = fields.Many2many('ir.attachment', 'key_attachment_rel','key_id','attachment_id', string=".key", required=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),],default="valid")
    predetermined = fields.Boolean('Predetermined', copy=False)

    @api.multi
    def action_revoked(self):
        for fc in self:
            fc.state = 'revoked'
            fc.predetermined = False
            
            
    @api.multi
    def action_timed_out(self):
        for fc in self:
            fc.state = 'timed_out'
            fc.predetermined = False


class branchOffices(models.Model):

    _name = 'res.company.branch.offices'
    
    company_id = fields.Many2one('res.company', "Company", required=False)
    partner_id = fields.Many2one('res.partner', "Branch Offices", required=True, copy=False)


class bankDetailsCompany(models.Model):
    _name = "bank.account.company"
    
    company_id = fields.Many2one('res.company', "Company", required=False)
    bank_id = fields.Many2one('res.bank', "Bank", required=True)
    account_holder = fields.Char("Account holder", copy=False, required=True)
    bank_account = fields.Char("Bank account", copy=False, required=True)
    reference = fields.Char("Reference", copy=False, required=True)
    predetermined = fields.Boolean("Predetermined", copy=False, required=False)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ],default="active")
    account_type = fields.Selection([
        ('clabe', 'Clabe'),
        ('tarjeta', 'Tarjeta'),
    ],'Account Type ')

    @api.multi
    def action_active(self):
        for account in self:
            account.state = 'active'

    @api.multi
    def action_inactive(self):
        for account in self:
            account.state = 'inactive'
            account.predetermined = False


class companyPowerAttorney(models.Model):
    _name = "company.power.attorney"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "representative_id"

    company_id = fields.Many2one('res.company', "Company", required=False)
    representative_id = fields.Many2one('res.partner', "Representative", required=True, copy=False)
    book = fields.Integer("Book", copy=False, required=True)
    public_deed_number = fields.Char("Instrument or public deed number.", copy=False, required=True)
    public_notary  = fields.Many2one('res.partner', "Public Notary", required=True, copy=False)
    predetermined = fields.Boolean("Predetermined", copy=False, required=False)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('timed_out', 'Timed out'),
        ('revoked', 'Revoked'),], "Status",default="valid")

    def _get_name(self):
        return "%s ‒ %s" % (self.representative_id.name, self.public_deed_number)

    @api.multi
    def name_get(self):
        res = []
        for power in self:
            name = power._get_name()
            res.append((power.id, name))
        return res

    @api.multi
    def action_revoked(self):
        for power in self:
            power.state = 'revoked'
            power.predetermined = False

    @api.multi
    def action_timed_out(self):
        for power in self:
            power.state = 'timed_out'
            power.predetermined = False

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
    notary_public_number = fields.Integer("Notary Public Number", copy=False)
    notary_public = fields.Boolean(string='Notary Public?', copy=False)
    partner_company = fields.Boolean(string='Partner Company?', copy=False)
    branch_offices = fields.Boolean(string='Branch Offices?', copy=False)
    country_id = fields.Many2one(default=lambda self: self.env['res.country'].search([('code','=','MX')]))
    municipality_id = fields.Many2one('res.country.state.municipality', string='Municipality')
    suburb_id = fields.Many2one('res.municipality.suburb', string='Colonia')

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip and self.zip not in zip_data.postal_code:
            self.zip = False
            warning = {}
            title = False
            message = False
            if True:
                title = _("Código Postal incorrecto")
                message = 'Debe ingresar un Código Postal valido'
                warning = {
                    'title': title,
                    'message': message
                }
                return {'warning': warning}

    @api.multi
    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        return address_format % args
    
    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            self.municipality_id = False


class companySectorEconomico(models.Model):

    _name = 'res.company.sector_economico'
    
    name = fields.Char('Sector Economico', required=True)
    code = fields.Char('Código', required=True)
