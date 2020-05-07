odoo.define('portal_chatter_attachment.chatter', function(require) {
    'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var qweb = core.qweb;
    var PortalChatter = require('portal.chatter').PortalChatter;

    PortalChatter.include({
        _loadTemplates: function() {
            return $.when(this._super(), ajax.loadXML('/portal_chatter_attachment/static/src/xml/chatter.xml', qweb));
        },
    });
});