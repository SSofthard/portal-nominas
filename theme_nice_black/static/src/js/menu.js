odoo.define('theme_nice_black.menu', function (require) {
"use strict";
try {
    var Menu = require('web_enterprise.Menu');
    Menu.include({
        _onToggleHomeMenu: function (ev) {
            ev.preventDefault();
            window.location.href=window.location.origin+'/web'
            //~ this.trigger_up(this.home_menu_displayed ? 'hide_home_menu' : 'show_home_menu');
            //~ this.$el.parent().removeClass('o_mobile_menu_opened');
        }
    });
    return Menu
    
    }catch(error) {
}


});


