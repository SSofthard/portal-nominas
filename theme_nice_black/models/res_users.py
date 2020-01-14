# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields

class User(models.Model):
    _inherit = 'res.users'

    def check_access_menu(self, MENU_ACCESS):
        menu_access_ids=self.groups_id.mapped('menu_access').ids
        for menu in MENU_ACCESS:
            menuXml=MENU_ACCESS[menu]['menu']
            model=MENU_ACCESS[menu]['model']
            menuXmlId="%s.%s" % (model,menuXml)
            menu_id=self.env.ref(menuXmlId, False)
            if menu_id:
                if menu_id.id in menu_access_ids:
                    MENU_ACCESS[menu]['acces']=""
        return MENU_ACCESS
