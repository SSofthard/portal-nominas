odoo.define('payroll_mexico.report_layout_credential', function (require) {
"use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var relational_fields = require('web.relational_fields');
    var registry = require('web.field_registry');
    var FieldSelection = relational_fields.FieldSelection;
    var QWeb = core.qweb;
    var _t = core._t;


    var FieldReportLayoutCredential = relational_fields.FieldMany2One.extend({
    // this widget is not generic, so we disable its studio use
    // supportedFieldTypes: ['many2one', 'selection'],
    events: _.extend({}, relational_fields.FieldMany2One.prototype.events, {
        'click img': '_onImgClicked',
    }),

    willStart: function () {
        var self = this;
        this.previews = {};
        return this._super()
            .then(function () {
                return self._rpc({
                    model: 'report.layout.credential',
                    method: "search_read"
                }).then(function (values) {
                    self.previews = values;
                });
            });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _render: function () {
        var self = this;
        this.$el.empty();
        var value = _.isObject(this.value) ? this.value.data.id : this.value;
        _.each(this.previews, function (val) {
            var $container = $('<div>').addClass('col-3 text-center');
            var $img = $('<img>')
                .addClass('img img-fluid img-thumbnail ml16')
                .toggleClass('btn-info', val.view_id[0] === value)
                .attr('src', val.image)
                .data('key', val.view_id[0]);
            $container.append($img);
            if (val.pdf) {
                var $previewLink = $('<a>')
                    .text('Preview')
                    .attr('href', val.pdf)
                    .attr('target', '_blank');
                $container.append($previewLink);
            }
            self.$el.append($container);
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     * @param {MouseEvent} event
     */
    _onImgClicked: function (event) {
        this._setValue($(event.currentTarget).data('key'));
    },
});


return {
    FieldReportLayoutCredential: FieldReportLayoutCredential,
};
});


odoo.define('payroll_mexico._field_registry', function(require) {
"use strict";

var registry = require('web.field_registry');
var payroll_mexico_fields = require('payroll_mexico.report_layout_credential');

registry
    .add('report_layout_credential', payroll_mexico_fields.FieldReportLayoutCredential);
});
