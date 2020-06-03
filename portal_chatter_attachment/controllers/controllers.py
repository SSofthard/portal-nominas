# -*- coding: utf-8 -*-

import base64
from odoo import http
from odoo.http import request
from odoo.tools import plaintext2html
from odoo.addons.portal.controllers.mail import PortalChatter
from odoo.tools import consteq, plaintext2html
import uuid

def _has_token_access(res_model, res_id, token=''):
    record = request.env[res_model].browse(res_id).sudo()
    token_field = request.env[res_model]._mail_post_token_field
    return (token and record and consteq(record[token_field], token))

def _message_post_helper(res_model='', res_id=None, message='', token='', nosubscribe=True, **kw):
    """ Generic chatter function, allowing to write on *any* object that inherits mail.thread.
        If a token is specified, all logged in users will be able to write a message regardless
        of access rights; if the user is the public user, the message will be posted under the name
        of the partner_id of the object (or the public user if there is no partner_id on the object).

        :param string res_model: model name of the object
        :param int res_id: id of the object
        :param string message: content of the message

        optional keywords arguments:
        :param string token: access token if the object's model uses some kind of public access
                             using tokens (usually a uuid4) to bypass access rules
        :param bool nosubscribe: set False if you want the partner to be set as follower of the object when posting (default to True)

        The rest of the kwargs are passed on to message_post()
    """
    record = request.env[res_model].browse(res_id)
    author_id = request.env.user.partner_id.id if request.env.user.partner_id else False
    if token:
        access_as_sudo = _has_token_access(res_model, res_id, token=token)
        if access_as_sudo:
            record = record.sudo()
            if request.env.user._is_public():
                if kw.get('pid') and consteq(kw.get('hash'), record._sign_token(int(kw.get('pid')))):
                    author_id = kw.get('pid')
                else:
                    # TODO : After adding the pid and sign_token in access_url when send invoice by email, remove this line
                    # TODO : Author must be Public User (to rename to 'Anonymous')
                    author_id = record.partner_id.id if hasattr(record, 'partner_id') and record.partner_id.id else author_id
            else:
                if not author_id:
                    raise NotFound()
        else:
            raise Forbidden()
    kw.pop('csrf_token', None)
    kw.pop('attachment_ids', None)
    return record.sudo().with_context(mail_create_nosubscribe=nosubscribe).message_post(body=message,
                                                                                   message_type=kw.pop('message_type', "comment"),
                                                                                   subtype=kw.pop('subtype', "mt_comment"),
                                                                                   author_id=author_id,
                                                                                   **kw)


class PortalChatter(PortalChatter):

    def _get_default_access_token(self):
        return str(uuid.uuid4())

    @http.route(['/mail/chatter_post'], type='http', methods=['POST'], auth='public', website=True)
    def portal_chatter_post(self, res_model, res_id, message, **kw):
        if 'attachments' in request.params and kw.get('attachments'):
            attached_files = request.httprequest.files.getlist('attachments')
            attachments = self.insert_attachment(res_model=res_model, res_id=int(res_id), files=attached_files)
            token = self._get_default_access_token()

            url = request.httprequest.referrer
            if message:
                msg = _message_post_helper(res_model=res_model, res_id=int(res_id), message=message, partner_ids=request.env.user.sudo().partner_id.ids)
            else:
                msg = _message_post_helper(res_model=res_model, res_id=int(res_id), message='', partner_ids=request.env.user.sudo().partner_id.ids)
            url = url + "#discussion"
            if attachments:
                msg.attachment_ids = [(6,0, attachments)]

            return request.redirect(url)
        else:
            message = plaintext2html(message)
            url = request.httprequest.referrer
            msg = _message_post_helper(res_model, int(res_id), message, **kw)
            url = url + "#discussion"
            return request.redirect(url)

    def insert_attachment(self, res_model, res_id, files):
        orphan_attachments = []
        for file in files:
            attachment_value = {
                'name': file.filename,
                'datas': base64.encodestring(file.read()),
                'datas_fname': file.filename,
                'res_model': res_model,
                'res_id': res_id,
            }
            attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
            orphan_attachments.append(attachment_id.id)
        return orphan_attachments
