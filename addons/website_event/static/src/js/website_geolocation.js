odoo.define('website_event.geolocation', function (require) {
'use strict';

var sAnimation = require('website.content.snippets.animation');

<<<<<<< HEAD
sAnimation.registry.visitor = sAnimation.Class.extend({
    selector: '.oe_country_events',

    /**
     * @override
     */
    start: function () {
        var defs = [this._super.apply(this, arguments)];
        var self = this;
        defs.push(this._rpc({route: '/event/get_country_event_list'}).then(function (data) {
            if (data) {
                self.$('.country_events_list').replaceWith(data);
=======
animation.registry.visitor = animation.Class.extend({
    selector: ".oe_country_events, .country_events",
    start: function () {
        var self = this;
        $.get("/event/get_country_event_list").then(function( data ) {
            if(data){
                self.$(".country_events_list").replaceWith( data );
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09
            }
        }));
        return $.when.apply($, defs);
    },
});
});
