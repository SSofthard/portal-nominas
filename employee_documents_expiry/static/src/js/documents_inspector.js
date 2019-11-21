odoo.define('employee_documents_expiry.DocumentsInspector', function (require) {
"use strict";

var DocumentsInspector = require('documents.DocumentsInspector');
DocumentsInspector.include({
    /**
     * @override
     */
    _renderFields: function () {
        this._super.apply(this, arguments);
        var options = {mode: 'edit'};
        if (this.records.length === 1) {
            this._renderField('employee_id', options);
            this._renderField('description', options);
            this._renderField('expiry_date', options);
        }
        
    },
    })
return DocumentsInspector
});
