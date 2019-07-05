# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import traceback
import os
import unittest

import pytz
import werkzeug
import werkzeug.routing
import werkzeug.utils

import odoo
from odoo import api, models
from odoo import SUPERUSER_ID
from odoo.http import request
from odoo.tools import config, ustr
from odoo.exceptions import QWebException
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import FALSE_DOMAIN

from odoo.addons.http_routing.models.ir_http import ModelConverter, _guess_mimetype

from ..geoipresolver import GeoIPResolver

logger = logging.getLogger(__name__)


def sitemap_qs2dom(qs, route, field='name'):
    """ Convert a query_string (can contains a path) to a domain"""
    dom = []
    if qs and qs.lower() not in route:
        needles = qs.strip('/').split('/')
        # needles will be altered and keep only element which one is not in route
        # diff(from=['shop', 'product'], to=['shop', 'product', 'product']) => to=['product']
        unittest.util.unorderable_list_difference(route.strip('/').split('/'), needles)
        if len(needles) == 1:
            dom = [(field, 'ilike', needles[0])]
        else:
            dom = FALSE_DOMAIN
    return dom


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_converters(cls):
        """ Get the converters list for custom url pattern werkzeug need to
            match Rule. This override adds the website ones.
        """
        return dict(
            super(Http, cls)._get_converters(),
            model=ModelConverter,
        )

    @classmethod
    def _auth_method_public(cls):
        """ If no user logged, set the public user of current website, or default
            public user as request uid.
            After this method `request.env` can be called, since the `request.uid` is
            set. The `env` lazy property of `request` will be correct.
        """
        if not request.session.uid:
            env = api.Environment(request.cr, SUPERUSER_ID, request.context)
            website = env['website'].get_current_website()
            if website and website.user_id:
                request.uid = website.user_id.id
        if not request.uid:
            super(Http, cls)._auth_method_public()

    @classmethod
    def _add_dispatch_parameters(cls, func):
        if request.is_frontend:
            context = dict(request.context)
            if not context.get('tz'):
                context['tz'] = request.session.get('geoip', {}).get('time_zone')

            request.website = request.env['website'].get_current_website()  # can use `request.env` since auth methods are called
            context['website_id'] = request.website.id

        super(Http, cls)._add_dispatch_parameters(func)

        if request.is_frontend and request.routing_iteration == 1:
            request.website = request.website.with_context(context)

    @classmethod
<<<<<<< HEAD
    def _get_languages(cls):
        if getattr(request, 'website', False):
            return request.website.language_ids
        return super(Http, cls)._get_languages()

    @classmethod
    def _get_language_codes(cls):
        if request.website:
            return request.website._get_languages()
        return super(Http, cls)._get_language_codes()
=======
    def _geoip_setup_resolver(cls):
        # Lazy init of GeoIP resolver
        if cls._geoip_resolver is not None:
            return
        if odoo._geoip_resolver is not None:
            cls._geoip_resolver = odoo._geoip_resolver
            return
        geofile = config.get('geoip_database')
        try:
            odoo._geoip_resolver = GeoIPResolver.open(geofile) or False
        except Exception as e:
            logger.warning('Cannot load GeoIP: %s', ustr(e))

    @classmethod
    def _geoip_resolve(cls):
        if 'geoip' not in request.session:
            record = {}
            if odoo._geoip_resolver and request.httprequest.remote_addr:
                record = odoo._geoip_resolver.resolve(request.httprequest.remote_addr) or {}
            request.session['geoip'] = record
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09

    @classmethod
    def _get_default_lang(cls):
        if getattr(request, 'website', False):
            return request.website.default_lang_id
        return super(Http, cls)._get_default_lang()

    @classmethod
    def _serve_page(cls):
        req_page = request.httprequest.path

        domain = [('url', '=', req_page), '|', ('website_ids', 'in', request.website.id), ('website_ids', '=', False)]
        pages = request.env['website.page'].search(domain)

<<<<<<< HEAD
        if not request.website.is_publisher():
            pages = pages.filtered('is_visible')
=======
        # For website routes (only), add website params on `request`
        cook_lang = request.httprequest.cookies.get('website_lang')
        if request.website_enabled:
            try:
                if func:
                    cls._authenticate(func.routing['auth'])
                elif request.uid is None:
                    cls._auth_method_public()
            except Exception as e:
                return cls._handle_exception(e)

            request.redirect = lambda url, code=302: werkzeug.utils.redirect(url_for(url), code)
            request.website = request.env['website'].get_current_website()  # can use `request.env` since auth methods are called
            context = dict(request.context)
            context['website_id'] = request.website.id
            langs = [lg[0] for lg in request.website.get_languages()]
            path = request.httprequest.path.split('/')
            if first_pass:
                is_a_bot = cls.is_a_bot()
                nearest_lang = not func and cls.get_nearest_lang(path[1])
                url_lang = nearest_lang and path[1]
                preferred_lang = ((cook_lang if cook_lang in langs else False)
                                  or (not is_a_bot and cls.get_nearest_lang(request.lang))
                                  or request.website.default_lang_code)

                request.lang = context['lang'] = nearest_lang or preferred_lang
                # if lang in url but not the displayed or default language --> change or remove
                # or no lang in url, and lang to dispay not the default language --> add lang
                # and not a POST request
                # and not a bot or bot but default lang in url
                if ((url_lang and (url_lang != request.lang or url_lang == request.website.default_lang_code))
                        or (not url_lang and request.website_multilang and request.lang != request.website.default_lang_code)
                        and request.httprequest.method != 'POST') \
                        and (not is_a_bot or (url_lang and url_lang == request.website.default_lang_code)):
                    if url_lang:
                        path.pop(1)
                    if request.lang != request.website.default_lang_code:
                        path.insert(1, request.lang)
                    path = '/'.join(path) or '/'
                    request.context = context
                    redirect = request.redirect(path + '?' + request.httprequest.query_string)
                    redirect.set_cookie('website_lang', request.lang)
                    return redirect
                elif url_lang:
                    request.uid = None
                    path.pop(1)
                    request.context = context
                    return cls.reroute('/'.join(path) or '/')
            if request.lang == request.website.default_lang_code:
                context['edit_translations'] = False
            if not context.get('tz'):
                context['tz'] = request.session.get('geoip', {}).get('time_zone')
                try:
                    pytz.timezone(context['tz'] or '')
                except pytz.UnknownTimeZoneError:
                    context.pop('tz')

            # bind modified context
            request.context = context
            request.website = request.website.with_context(context)
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09

        mypage = pages[0] if pages else False
        _, ext = os.path.splitext(req_page)
        if mypage:
            return request.render(mypage.view_id.id, {
                # 'path': req_page[1:],
                'deletable': True,
                'main_object': mypage,
            }, mimetype=_guess_mimetype(ext))
        return False

    @classmethod
    def _serve_404(cls):
        req_page = request.httprequest.path
        return request.website.is_publisher() and request.render('website.page_404', {'path': req_page[1:]}) or False

    @classmethod
    def _serve_redirect(cls):
        req_page = request.httprequest.path
        domain = [
            '|', ('website_id', '=', request.website.id), ('website_id', '=', False),
            ('url_from', '=', req_page)
        ]
        return request.env['website.redirect'].search(domain, limit=1)

    @classmethod
    def _serve_fallback(cls, exception):
        # serve attachment before
        parent = super(Http, cls)._serve_fallback(exception)
        if parent:  # attachment
            return parent

        website_page = cls._serve_page()
        if website_page:
            return website_page

        redirect = cls._serve_redirect()
        if redirect:
            return request.redirect(redirect.url_to, code=redirect.type)

        return cls._serve_404()

    @classmethod
    def _handle_exception(cls, exception):
        code = 500  # default code
        is_website_request = bool(getattr(request, 'is_frontend', False) and getattr(request, 'website', False))
        if not is_website_request:
            # Don't touch non website requests exception handling
            return super(Http, cls)._handle_exception(exception)
        else:
            try:
                response = super(Http, cls)._handle_exception(exception)

                if isinstance(response, Exception):
                    exception = response
                else:
                    # if parent excplicitely returns a plain response, then we don't touch it
                    return response
            except Exception as e:
                if 'werkzeug' in config['dev_mode'] and (not isinstance(exception, QWebException) or not exception.qweb.get('cause')):
                    raise
                exception = e

            values = dict(
                exception=exception,
                traceback=traceback.format_exc(),
            )

            if isinstance(exception, werkzeug.exceptions.HTTPException):
                if exception.code is None:
                    # Hand-crafted HTTPException likely coming from abort(),
                    # usually for a redirect response -> return it directly
                    return exception
                else:
                    code = exception.code

            if isinstance(exception, odoo.exceptions.AccessError):
                code = 403

            if isinstance(exception, QWebException):
                values.update(qweb_exception=exception)
                if isinstance(exception.qweb.get('cause'), odoo.exceptions.AccessError):
                    code = 403

            if code == 500:
                logger.error("500 Internal Server Error:\n\n%s", values['traceback'])
                if 'qweb_exception' in values:
                    view = request.env["ir.ui.view"]
                    views = view._views_get(exception.qweb['template'])
                    to_reset = views.filtered(lambda view: view.model_data_id.noupdate is True and view.arch_fs)
                    values['views'] = to_reset
            elif code == 403:
                logger.warn("403 Forbidden:\n\n%s", values['traceback'])

            values.update(
                status_message=werkzeug.http.HTTP_STATUS_CODES[code],
                status_code=code,
            )

            if not request.uid:
                cls._auth_method_public()

            try:
                html = request.env['ir.ui.view'].render_template('website.%s' % code, values)
            except Exception:
                html = request.env['ir.ui.view'].render_template('website.http_error', values)
            return werkzeug.wrappers.Response(html, status=code, content_type='text/html;charset=utf-8')

    @classmethod
    def binary_content(cls, xmlid=None, model='ir.attachment', id=None, field='datas',
                       unique=False, filename=None, filename_field='datas_fname', download=False,
                       mimetype=None, default_mimetype='application/octet-stream',
                       access_token=None, env=None):
        env = env or request.env
        obj = None
        if xmlid:
            obj = env.ref(xmlid, False)
        elif id and model in env:
            obj = env[model].browse(int(id))
        if obj and 'website_published' in obj._fields:
            if env[obj._name].sudo().search([('id', '=', obj.id), ('website_published', '=', True)]):
                env = env(user=SUPERUSER_ID)
        return super(Http, cls).binary_content(
            xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype,
            default_mimetype=default_mimetype, access_token=access_token, env=env)


class ModelConverter(ModelConverter):

    def generate(self, uid, dom=None, args=None):
        Model = request.env[self.model].sudo(uid)
        domain = safe_eval(self.domain, (args or {}).copy())
        if dom:
            domain += dom
        for record in Model.search_read(domain=domain, fields=['write_date', Model._rec_name]):
            if record.get(Model._rec_name, False):
                yield {'loc': (record['id'], record[Model._rec_name])}
