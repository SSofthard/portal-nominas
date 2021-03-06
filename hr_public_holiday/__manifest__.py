{
    "name" : "Public holidays",
    "version" : "1.0",
    "author": "JUVENTUD PRODUCTIVA VENEZOLANA",
    "category": "HR",
    "website" : "https://www.youtube.com/channel/UCTj66IUz5M-QV15Mtbx_7yg",
    "description": "Module for the control of days employee public holiday. It allows you to manage the order of the public holiday from your odoo system, generating ease for the management of your company's human resources.",
    "license": "AGPL-3",
    "depends" : ["mail","base","hr",'hr_holidays'],
    "data" : [
            "security/ir.model.access.csv",
            'report/hr_public_holidays_report.xml',
            "data/mail_template.xml",
            "data/ir_config_parameter.xml",
            # ~ 'templates/assets.xml',
            "wizard/hr_public_holidays_wizard_view.xml",
            "wizard/hr_public_holidays_email.xml",
            "views/public_holidays_view.xml",
            "wizard/hr_public_holidays_import_view.xml",
            ],
    "images": ['static/images/holiday_screenshot.png'],
    "active": True,
    "installable": True,
    "currency": 'EUR',
    "price": 19.00,
}
