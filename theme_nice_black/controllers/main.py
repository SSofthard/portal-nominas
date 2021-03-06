# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import werkzeug

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.web_settings_dashboard.controllers.main import WebSettingsDashboard as Dashboard
from odoo.exceptions import UserError,AccessError
from odoo.http import request
from odoo.addons.mail.controllers.main import MailController
from odoo import http


_logger = logging.getLogger(__name__)

MENU_ACCESS = {
    'setting': {
        'model': 'base',
        'action': 'res_config_setting_act_window',
        'menu': 'menu_administration',
        'acces': 'accesdeny',
    },
    'app': {
        'model': 'base',
        'action': 'open_module_tree',
        'menu': 'menu_management',
        'acces': 'accesdeny',
    },
    'attendance': {
        'model': 'hr_attendance',
        'action': 'hr_attendance_action',
        'menu': 'menu_hr_attendance_root',
        'acces': 'accesdeny',
    },
    'leave': {
        'model': 'hr_holidays',
        'action': 'action_hr_holidays_dashboard',
        'menu': 'menu_hr_holidays_root',
        'acces': 'accesdeny',
    },
    'calendar': {
        'model': 'calendar',
        'action': 'action_calendar_event',
        'menu': 'mail_menu_calendar',
        'acces': 'accesdeny',
    },
    'mail': {
        'model': 'mail',
        'action': 'action_discuss',
        'menu': 'menu_root_discuss',
        'acces': 'accesdeny',
    },
    'documents': {
        'model': 'documents',
        'action': 'document_action',
        'menu': 'menu_root',
        'acces': 'accesdeny',
    },
    'expense': {
        'model': 'hr_expense',
        'action': 'hr_expense_actions_my_unsubmitted',
        'menu': 'menu_hr_expense_root',
        'acces': 'accesdeny',
    },
    'hr': {
        'model': 'hr',
        'action': 'open_view_employee_list_my',
        'menu': 'menu_hr_root',
        'acces': 'accesdeny',
    },
    'payroll': {
        'model': 'hr_payroll',
        'action': 'action_view_hr_payslip_form',
        'menu': 'menu_hr_payroll_root',
        'acces': 'accesdeny',
    },
}

class AuthSignupHome(Home):
    
    @http.route('/web', type='http', auth="user")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        # ~ print (kw)
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        try:
            httpObj=request.env['ir.http']
            context = httpObj.webclient_rendering_context()
            if 'reload' in kw.keys():
                response = request.render('web.webclient_bootstrap', qcontext=context)
            else:
                user_menu_access = request.env.user.check_access_menu(MENU_ACCESS)
                context.update({'dataMenu': MENU_ACCESS})
                response = request.render('theme_nice_black.custom_menu_hr', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            return werkzeug.utils.redirect('/web/login?error=access')
            
    @http.route('/web2', type='http', auth="user")
    def web_client2(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        try:
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render('web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            return werkzeug.utils.redirect('/web/login?error=access')


class MenuApp(http.Controller):

    @http.route(['/web/action/<string:model>/<string:action>/<string:menu>'], type='http', auth="user", methods=['GET'])
    def menu_redirect(self,model,action,menu):
        actionXmlId="%s.%s" % (model,action)
        menuXmlId="%s.%s" % (model,menu)
        action_id=request.env.ref(actionXmlId, False)
        menu_id=request.env.ref(menuXmlId, False)
        menu_id.check_access_rights('read')
        if not menu_id._filter_visible_menus():
            redirect="/web?msg='Acceso denegado, contacte al Administrador del portal.'"
            return werkzeug.utils.redirect(redirect)
        print ()
        redirect="/web2#menu_id=%d&action_id=%d" % (menu_id.id,action_id.id)
        print (redirect)
        return werkzeug.utils.redirect(redirect)
        
        
        
