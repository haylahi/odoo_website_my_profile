# -*- coding: utf-8 -*-
import logging
import werkzeug

from odoo import http, _
from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.http import request

_logger = logging.getLogger(__name__)


class MyProfile(website_account):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email",
                                "street", "city", "country_id", "birthday"]
    OPTIONAL_BILLING_FIELDS = ["zipcode",
                               "state_id", "vat", "company_name", "active", "gender"]

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def details(self, redirect=None, **post):
        partner = request.env.user.partner_id
        values = {
            'error': {},
            'error_message': []
        }

        if post:
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key]
                          for key in self.MANDATORY_BILLING_FIELDS}
                values.update(
                    {key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                values.update({'zip': values.pop('zipcode', '')})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        # genders = request.env['hr.employee.gender'].sudo().search([])
        genders = request.env['res.partner'].get_value_gender()

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'genders': genders,
            'redirect': redirect,
        })

        return request.render("website_portal.details", values)


class ResetPassword(AuthSignupHome):

    @http.route('/web/reset_password', type='http', auth='public', website=True)
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        # get parameter in url
        if 'error' not in qcontext and 'reset_directly' in request.httprequest.query_string:
            user = request.env['res.users'].search(
                [('id', '=', request.session.uid)])
            login = user.login
            if not login:
                login = 'empty'
            assert login, "No login provided."
            user = request.env['res.users'].search(
                [('login', '=', login)])
            partner = request.env['res.partner'].search(
                [('id', '=', user.partner_id.id)])
            qcontext['token'] = partner.signup_token
            qcontext['name'] = partner.name
            qcontext['login'] = login

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return super(AuthSignupHome, self).web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, "No login provided."
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _(
                        "An email has been sent with credentials to reset your password")
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception, e:
                qcontext['error'] = e.message or e.name

        return request.render('auth_signup.reset_password', qcontext)

    def do_signup(self, qcontext):
        values = {key: qcontext.get(key) for key in (
            'login', 'name', 'birthday', 'password')}
        print 'o la ', qcontext.get('birthday')
        assert values.values(), "The form was not properly filled in."
        assert values.get('password') == qcontext.get(
            'confirm_password'), "Passwords do not match; please retype them."
        supported_langs = [lang['code'] for lang in request.env[
            'res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()
