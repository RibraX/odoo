odoo.define('website_event.registration_form.instance', function (require) {
'use strict';

require('web_editor.ready');
var EventRegistrationForm = require('website_event.website_event');

var $form = $('#registration_form');
if (!$form.length) {
    return null;
}

var instance = new EventRegistrationForm();
return instance.appendTo($form).then(function () {
    return instance;
});
});

//==============================================================================

odoo.define('website_event.website_event', function (require) {

var ajax = require('web.ajax');
var Widget = require('web.Widget');

// Catch registration form event, because of JS for attendee details
var EventRegistrationForm = Widget.extend({
    start: function () {
        var self = this;
        var res = this._super.apply(this.arguments).then(function () {
            $('#registration_form .a-submit')
                .off('click')
                .removeClass('a-submit')
                .click(function (ev) {
                    $(this).attr('disabled', true);
                    self.on_click(ev);
                });
        });
        return res;
    },
    on_click: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $form = $(ev.currentTarget).closest('form');
        var $button = $(ev.currentTarget).closest('[type="submit"]');
        var post = {};
        $('#registration_form select').each(function () {
            post[$(this).attr('name')] = $(this).val();
        });
<<<<<<< HEAD
        var tickets_ordered = _.some(_.map(post, function (value, key) { return parseInt(value); }));
        if (!tickets_ordered) {
            return $('#registration_form table').after(
                '<div class="alert alert-info">Please select at least one ticket.</div>'
            );
        } else {
            return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal) {
                var $modal = $(modal);
                $modal.appendTo($form).modal();
                $modal.on('click', '.js_goto_event', function () {
                    $modal.modal('hide');
                });
=======
        return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal) {
            // Only needed for 9.0 up to saas-14
            if (modal === false) {
                $button.prop('disabled', false);
                return;
            }
            var $modal = $(modal);
            $modal.modal({backdrop: 'static', keyboard: false});
            $modal.find('.modal-body > div').removeClass('container'); // retrocompatibility - REMOVE ME in master / saas-19
            $modal.insertAfter($form).modal();
            $modal.on('click', '.js_goto_event', function () {
                $modal.modal('hide');
                $button.prop('disabled', false);
            });
            $modal.on('click', '.close', function () {
                $button.prop('disabled', false);
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09
            });
        }
    },
});

return EventRegistrationForm;
});
