# -*- coding: utf-8 -*-
{
    'name': "Website/Portal Chatter Attachments",
    'category': 'Website',
    'summary': 'Allow users to attach multiple attachments with chatter comments/messages.',
    'license': 'OPL-1',
    'version': '1.2',
    'author': "Atharva System",
    'website': 'https://www.atharvasystem.com',
    'support': 'support@atharvasystem.com',
    'description': """  
        Website Comments Attachments
        Portal Chatter Attachments
        Website Project Attachments
        Website task Attachments
        Website Sales Order Attachments
        Website Quotation Attachments
        Website Invoice Attachments
        Website Helpdesk Ticket Attachments
        Website Project Task Attachment
        Website Message Attachments
        Website Message Attachment
        Attachment in Chatter
		sale order Attachments
		portal customer Attachment
		portal customer file upload 
		Document upload Portal
		Document attachment Portal
		Website Documents Attachment
		Portal Documents Attachment
		Portal Task Attachment
		Send Attachments From Helpdesk Ticket By Portal 
		Send Attachments From Sales Order / Quotation Portal

    """,
    'depends': ['portal','website'],
    'data': [
        'views/templates.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'images': [
        'static/description/portal_chatter.png',
    ],
    'installable': True,
    'application': True,
    'currency': 'EUR',
    'price': 35,
}
