# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

from odoo.addons import decimal_precision as dp

class TableUma(models.Model):
    _name = 'table.uma'
    _rec_name = 'year'
    _order = 'year desc'
    
    @api.depends('daily_amount')
    def calculate_amount_uma(self):
        for uma in self:
            uma.monthly_amount = uma.daily_amount * 30.4
            uma.annual_amount = (uma.daily_amount * 30.4) * 12
            
    
    year = fields.Integer('Year', required=True)
    daily_amount = fields.Float('Daily amount', required=True)
    monthly_amount = fields.Float('Monthly amount', compute='calculate_amount_uma')
    annual_amount = fields.Float('Annual amount', compute='calculate_amount_uma')
    

    _sql_constraints = [
        ('year_uniq', 'unique (year)', "There is already a record with the same year.!"),
    ]
    
class TableMinimumWages(models.Model):
    _name = 'table.minimum.wages'
    _order = 'date desc'
    
    date = fields.Date('Validity', required=True)
    zone_a = fields.Float('Zone A')
    zone_b = fields.Float('Zone B')
    zone_c = fields.Float('Zone C')
    border_crossing = fields.Float('Border Crossing')
    
    
class TableSettings(models.Model):
    _name = 'table.settings'
    _order = 'year desc'
    
    @api.one
    @api.depends('uma_id',
                'pantry_voucher_factor',
                'holiday_bonus_factor',
                'bonus_factor',
                'savings_fund_factor',
                'extra_time_factor',
                'sunday_prime_factor',
                'clearance_factor',
                'factor_ptu')
    def _compute_exemptions(self):
        self.ex_pantry_voucher_factor = self.uma_id.daily_amount * self.pantry_voucher_factor
        self.ex_holiday_bonus_factor = self.uma_id.daily_amount * self.holiday_bonus_factor
        self.ex_bonus_factor = self.uma_id.daily_amount * self.bonus_factor
        self.ex_savings_fund_factor = self.uma_id.daily_amount * self.savings_fund_factor
        self.ex_extra_time_factor = self.uma_id.daily_amount * self.extra_time_factor
        self.ex_sunday_prime_factor = self.uma_id.daily_amount * self.sunday_prime_factor
        self.ex_clearance_factor = self.uma_id.daily_amount * self.clearance_factor
        self.ex_factor_ptu = self.uma_id.daily_amount * self.factor_ptu
    
    name = fields.Char('Name', required=True)
    year = fields.Integer('Year', required=True)
    uma_id = fields.Many2one('table.uma', string='UMA', required=True)
    daily_amount_uma = fields.Float('UMA amount', related='uma_id.daily_amount')
    
    pantry_voucher_factor= fields.Float(string=_('Pantry Voucher (UMA)'))
    holiday_bonus_factor = fields.Float(string=_('Holiday Bonus (UMA)'))
    bonus_factor = fields.Float(string=_('Bonus (UMA)'),)
    savings_fund_factor = fields.Float(string=_('Savings Fund (UMA)'),)
    extra_time_factor = fields.Float(string=_('Extra Time (UMA)'),)
    sunday_prime_factor = fields.Float(string=_('Sunday prime (UMA)'),)
    clearance_factor = fields.Float(string=_('Clearance (UMA)'), )
    factor_ptu = fields.Float(string=_('PTU (UMA)'))
    
    ex_pantry_voucher_factor= fields.Float(string=_('Pantry Voucher'), compute="_compute_exemptions")
    ex_holiday_bonus_factor = fields.Float(string=_('Holiday Bonus'), compute="_compute_exemptions")
    ex_bonus_factor = fields.Float(string=_('Bonus'), compute="_compute_exemptions")
    ex_savings_fund_factor = fields.Float(string=_('Savings Fund'), compute="_compute_exemptions")
    ex_extra_time_factor = fields.Float(string=_('Extra Time'), compute="_compute_exemptions")
    ex_sunday_prime_factor = fields.Float(string=_('Sunday prime'), compute="_compute_exemptions")
    ex_clearance_factor = fields.Float(string=_('Clearance'), compute="_compute_exemptions")
    ex_factor_ptu = fields.Float(string=_('PTU'), compute="_compute_exemptions")
    
    infonavit_contribution = fields.Float(string=_('INFONAVIT contribution (%)'))
    umi = fields.Float(string=_('UMI (Mixed Unit INFONAVIT)'))
    sbcm_general = fields.Float(string=_('General (UMA)'))
    sbcm_inv_inf = fields.Float(string=_('For disability and Infonavit (UMA)'))
    
    average_active_life = fields.Float(string=_('Average Active Life (años)'))
    premium_factor = fields.Float(string=_('Premium Factor'))
    minimum_premium = fields.Float(string=_('Minimum Premium (%)'))
    maximum_premium = fields.Float(string=_('Maximum Premium (%)'))
    maximum_premium_variation = fields.Float(string=_('Maximum Premium Variation (%)'))
    
    em_fixed_fee = fields.Float(string=_('Fixed Fee (%)'))
    em_surplus_p = fields.Float(string=_('3 UMA surplus (%)'))
    em_surplus_e = fields.Float(string=_('3 UMA surplus (%)'))

    em_cash_benefits_p = fields.Float(string=_('Cash benefits (%)'))
    em_cash_benefits_e = fields.Float(string=_('Cash benefits (%)'))
    em_personal_medical_expenses_p = fields.Float(string=_('Personal medical expenses (%)'))
    em_personal_medical_expenses_e = fields.Float(string=_('Personal medical expenses (%)'))
    
    
    disability_life_p = fields.Float(string=_('Disability and life (%)'))
    disability_life_e = fields.Float(string=_('Disability and life (%)'))

    unemployment_old_age_p = fields.Float(string=_('Unemployment and old age (%)'))
    unemployment_old_age_e = fields.Float(string=_('Unemployment and old age (%)'))

    retirement = fields.Float(string=_('Retirement (%)'))
    nursery_social_benefits = fields.Float(string=_('Nursery and social benefits (%)'))
    
    
    isr_daily_ids = fields.One2many('table.isr.daily','table_id', "ISR Daily")
    isr_daily_subsidy_ids = fields.One2many('table.isr.daily.subsidy','table_id', "ISR Daily (Subsidy)")
    
    isr_weekly_ids = fields.One2many('table.isr.weekly','table_id', "ISR Weekly")
    isr_Weekly_subsidy_ids = fields.One2many('table.isr.weekly.subsidy','table_id', "ISR Weekly (Subsidy)")

    isr_decennial_ids = fields.One2many('table.isr.decennial','table_id', "ISR Decennial")
    isr_decennial_subsidy_ids = fields.One2many('table.isr.decennial.subsidy','table_id', "ISR Decennial (Subsidy)")

    isr_biweekly_ids = fields.One2many('table.isr.biweekly','table_id', "ISR Biweekly")
    isr_biweekly_subsidy_ids = fields.One2many('table.isr.biweekly.subsidy','table_id', "ISR Biweekly (Subsidy)")
    
    isr_monthly_ids = fields.One2many('table.isr.monthly','table_id', "ISR Monthly")
    isr_monthly_subsidy_ids = fields.One2many('table.isr.monthly.subsidy','table_id', "ISR Monthly (Subsidy)")
    
    isr_annual_ids = fields.One2many('table.isr.annual','table_id', "ISR Annual")

class TableIsrDaily(models.Model):
    _name = 'table.isr.daily'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Daily')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    c_fija = fields.Float('Fixed fee') 
    s_excedente = fields.Float('Over surplus (%)', digits=dp.get_precision('Excess') )
    sequence = fields.Integer('Sequence')

class TableIsrDailySubsidy(models.Model):
    _name = 'table.isr.daily.subsidy'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Daily')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    s_mensual = fields.Float('Daily allowance')
    sequence = fields.Integer('Sequence')
    
class TableIsrWeekly(models.Model):
    _name = 'table.isr.weekly'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Weekly')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    c_fija = fields.Float('Fixed fee') 
    s_excedente = fields.Float('Over surplus (%)', digits=dp.get_precision('Excess') )
    sequence = fields.Integer('Sequence')

class TableIsrWeeklySubsidy(models.Model):
    _name = 'table.isr.weekly.subsidy'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Weekly')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    s_mensual = fields.Float('Weekly allowance')
    sequence = fields.Integer('Sequence')
    
class TableIsrDecennial(models.Model):
    _name = 'table.isr.decennial'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Decennial')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    c_fija = fields.Float('Fixed fee') 
    s_excedente = fields.Float('Over surplus (%)', digits=dp.get_precision('Excess') )
    sequence = fields.Integer('Sequence')

class TableIsrDecennialSubsidy(models.Model):
    _name = 'table.isr.decennial.subsidy'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Decennial')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    s_mensual = fields.Float('Decennial allowance')
    sequence = fields.Integer('Sequence')
    
class TableIsrBiweekly(models.Model):
    _name = 'table.isr.biweekly'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Biweekly')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    c_fija = fields.Float('Fixed fee') 
    s_excedente = fields.Float('Over surplus (%)', digits=dp.get_precision('Excess') )
    sequence = fields.Integer('Sequence')

class TableIsrBiweeklySubsidy(models.Model):
    _name = 'table.isr.biweekly.subsidy'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Biweekly')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    s_mensual = fields.Float('Biweekly allowance')
    sequence = fields.Integer('Sequence')
    
class TableIsrMonthly(models.Model):
    _name = 'table.isr.monthly'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Monthly')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    c_fija = fields.Float('Fixed fee') 
    s_excedente = fields.Float('Over surplus (%)', digits=dp.get_precision('Excess') )
    sequence = fields.Integer('Sequence')

class TableIsrMonthlySubsidy(models.Model):
    _name = 'table.isr.monthly.subsidy'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Monthly')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    s_mensual = fields.Float('Monthly allowance')
    sequence = fields.Integer('Sequence')
    
class TableIsrAnnual(models.Model):
    _name = 'table.isr.annual'
    _order = 'sequence'

    table_id = fields.Many2one('table.settings', string='ISR Annual')
    lim_inf = fields.Float('Lower limit')
    lim_sup = fields.Float('Upper limit')
    c_fija = fields.Float('Fixed fee') 
    s_excedente = fields.Float('Over surplus (%)', digits=dp.get_precision('Excess') )
    sequence = fields.Integer('Sequence')


    
