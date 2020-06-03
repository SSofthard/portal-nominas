odoo.define('payroll_mexico.tree_view_buttons', function (require) {
    "use strict";

    var KanbanController = require('web.KanbanController');
    var ListController = require('web.ListController');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;


    ListController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (!this.$buttons) {
                return;
            }
            this.$buttons.on('click', '.import_employee_tree_view_button',
                this.open_view_import_employee.bind(this));
        },
        
        open_view_import_employee: function () {
            var action = {
                name: _t("Importar Empleados"),
                type: 'ir.actions.act_window',
                res_model: 'hr.employee.import',
                view_mode: 'form',
                view_type: 'form',
                view_id: 'payroll_mexico.action_employee_import_form',
                views: [[false, 'form']],
                target: 'new',
                context: {},
            };
            this.do_action(action);
        },
    });
    
    KanbanController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (!this.$buttons) {
                return;
            }
            this.$buttons.on('click', '.import_employee_kanban_view_button',
                this.open_view_import_employee.bind(this));
        },
        
        open_view_import_employee: function () {
            var action = {
                name: _t("Importar Empleados"),
                type: 'ir.actions.act_window',
                res_model: 'hr.employee.import',
                view_mode: 'form',
                view_type: 'form',
                view_id: 'payroll_mexico.action_employee_import_form',
                views: [[false, 'form']],
                target: 'new',
                context: {},
            };
            this.do_action(action);
        },
    });
});
