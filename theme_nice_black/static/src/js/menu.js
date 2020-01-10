odoo.define('web_enterprise.HomeMenuHr', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var utils = require('web.utils');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var NBR_ICONS = 6;

var HomeMenuHr = Widget.extend({
    template: 'HomeMenuHr',
    events: {
        'click .o_menuitem': '_onMenuitemClick',
        'input input.o_menu_search_input': '_onMenuSearchInput',
        'compositionstart': '_onCompositionStart',
        'compositionend': '_onCompositionEnd',
    },
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    console.log('jeison')
    /**
     * @override
     * @param {web.Widget} parent
     * @param {Object[]} menuData
     */
    init: function (parent, menuData) {
        this._super.apply(this, arguments);
        this._menuData = this._processMenuData(menuData);
        this._state = this._getInitialState();
    },
    /**
     * @override
     */
    start: function () {
        this.$input = this.$('input');
        this.$menuSearch = this.$('.o_menu_search');
        this.$mainContent = this.$('.o_home_menu_scrollable');
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    _render: function () {
        this.$menuSearch.toggleClass('o_bar_hidden', !this._state.isSearching);
        this.$mainContent.html(QWeb.render('HomeMenuHr.Content', { widget: this }));
        var $focused = this.$mainContent.find('.o_focused');
        if ($focused.length && !config.device.isMobile) {
            if (!this._state.isComposing) {
                $focused.focus();
            }
            this.$el.scrollTo($focused, {offset: {top:-0.5*this.$el.height()}});
        }

        var offset = window.innerWidth -
                        (this.$mainContent.offset().left * 2 + this.$mainContent.outerWidth());
        if (offset) {
            this.$el.css('padding-left', "+=" + offset);
        }
    },

});
core.action_registry.add('HomeMenuHr', HomeMenuHr);

return HomeMenuHr;

});

