odoo.define('hr_public_holidays.public_holiday_bookmark', function (require) {
'use strict';

var calendarView = require('web_calendar.CalendarView');
var Model = require('web.Model');

calendarView.include({
    willStart: function () {
        var self = this;

        var hrHolidays = new Model('hr.days.public.holidays');
        var irConfigParameter = new Model('ir.config_parameter');

        var publicHolidays = hrHolidays.call('search_read', [[], ['date']]);
        var holidayColor = irConfigParameter.call(
            'get_param', ['calendar.public_holidays_color']);

        return $.when(publicHolidays, holidayColor, this._super())
            .then(function (publicHolidays, holidayColor) {
                self.publicHolidays = publicHolidays.map(x => x['date']);
                self.holidayColor = holidayColor;
            });
    },
    get_fc_init_options: function () {
        var res = this._super();
        var self = this;

        var oldRenderHandler = res['viewRender'];
        res['viewRender'] = function (view) {
            oldRenderHandler.apply(this, arguments);
            var visibleDays = self.$('.o_calendar_view .fc-day');
            _.each(visibleDays, function (day) {
                var dayDate = day.getAttribute('data-date');
                if (self.publicHolidays.includes(dayDate)) {
                    day.style.backgroundColor = self.holidayColor;
                }
            });
        };

        return res;
    }
});

});
