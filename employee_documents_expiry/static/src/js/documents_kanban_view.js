odoo.define('employee_documents_expiry.DocumentsKanbanView', function (require) {
"use strict";

var DocumentsKanbanView = require('documents.DocumentsKanbanView');
DocumentsKanbanView.include({
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        // add the fields used in the DocumentsInspector to the list of fields to fetch
        var inspectorFields = [
            'employee_id',
            'contract_id',
            'company_document_id',
            'description',
            'expiry_date'
        ];
        _.defaults(this.fieldsInfo[this.viewType], _.pick(this.fields, inspectorFields));
         
        }
       
    });
return DocumentsKanbanView
});
