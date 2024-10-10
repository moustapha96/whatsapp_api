# -*- coding: utf-8 -*-
from .whatsApp_controller import *
import sys
import time

_logger = logging.getLogger(__name__)


# List of REST resources in current file:
#   (url prefix)            (method)     (action)
# /api/auth/get_tokens        GET     - Login in Odoo and get access tokens
# /api/auth/refresh_token     POST    - Refresh access token
# /api/auth/delete_tokens     POST    - Delete access tokens from token store


# List of IN/OUT data (json data and HTTP-headers) for each REST resource:

# /api/auth/get_tokens  GET  - Login in Odoo and get access tokens
# IN data:
#   JSON:
#       {
#           "username": "XXXX",     # Odoo username
#           "password": "XXXX",     # Odoo user password
#           "access_lifetime": XXX, # (optional) access token lifetime (seconds)
#           "refresh_lifetime": XXX # (optional) refresh token lifetime (seconds)
#       }
# OUT data:
OUT__auth_gettokens__SUCCESS_CODE = 200             # editable
#   Possible ERROR CODES:
#       400 'empty_username_or_password'
#       401 'odoo_user_authentication_failed'
#   JSON:
#       {
#           "uid":                  XXX,
#           "user_context":         {....},
#           "company_id":           XXX,
#           "access_token":         "XXXXXXXXXXXXXXXXX",
#           "expires_in":           XXX,
#           "refresh_token":        "XXXXXXXXXXXXXXXXX",
#           "refresh_expires_in":   XXX
#       }

# /api/auth/refresh_token  POST  - Refresh access token
# IN data:
#   JSON:
#       {
#           "refresh_token": "XXXXXXXXXXXXXXXXX",
#           "access_lifetime": XXX  # (optional) access token lifetime (seconds)
#       }
# OUT data:
OUT__auth_refreshtoken__SUCCESS_CODE = 200          # editable
#   Possible ERROR CODES:
#       400 'no_refresh_token'
#       401 'invalid_token'
#   JSON:
#       {
#           "access_token": "XXXXXXXXXXXXXXXXX",
#           "expires_in":   XXX
#       }

# /api/auth/delete_tokens  POST  - Delete access tokens from token store
# IN data:
#   JSON:
#       {"refresh_token": "XXXXXXXXXXXXXXXXX"}
# OUT data:
OUT__auth_deletetokens__SUCCESS_CODE = 200          # editable
#   Possible ERROR CODES:
#       400 'no_refresh_token'


# HTTP controller of REST resources:

class ControllerREST(http.Controller):

    def set_verification_status(self, email, is_verified):
        # Stocker la valeur de isVerified dans ir.config_parameter
        request.env['ir.config_parameter'].sudo().set_param(f'user_verification_{email}', is_verified)

    def get_verification_status(self, email):
        # Récupérer la valeur de isVerified depuis ir.config_parameter
        return request.env['ir.config_parameter'].sudo().get_param(f'user_verification_{email}')

    def get_user_avatar(self, email):
        # Récupérer la valeur de isVerified depuis ir.config_parameter
        return request.env['ir.config_parameter'].sudo().get_param(f'user_avatar_{email}')


    def set_user_avatar(self, email, avatar):
        # Stocker la valeur de isVerified dans ir.config_parameter
        request.env['ir.config_parameter'].sudo().set_param(f'user_avatar_{email}', avatar)
    def define_token_expires_in(self, token_type, jdata):
        token_lifetime = jdata.get('%s_lifetime' % token_type)
        try:
            token_lifetime = float(token_lifetime)
        except:
            pass
        if isinstance(token_lifetime, (int, float)):
            expires_in = token_lifetime
        else:
            try:
                expires_in = float(request.env['ir.config_parameter'].sudo()
                    .get_param('rest_api.%s_token_expires_in' % token_type))
            except:
                expires_in = None
        return int(round(expires_in or (sys.maxsize - time.time())))

    # Login in Odoo database and get access tokens:
    @http.route('/api/auth/get_tokens', methods=['GET', 'POST'], type='http', auth='none', cors="*", csrf=False)
    def api_auth_gettokens(self, **kw):
        args = request.httprequest.args.to_dict()
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
      
        jdata = args.copy()
        jdata.update(body)
        
        username = jdata.get('username')
        password = jdata.get('password')
        
        if not username or not password:
            error_descrip = "Empty value of 'username' or 'password'!"
            error = 'empty_username_or_password'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        

        email_admin = 'ccbmtech@ccbm.sn'
        password_admin = 'ccbmE@987'

        if username  and password:
            try:
                request.session.authenticate(db_name, username, password)
            except:
                pass
            uid = request.session.uid
            if uid:
                partner_hold = request.env['res.partner'].sudo().search([('email', '=', username)], limit=1)
                if partner_hold:
                    partner_hold.write({'password': password , 'is_verified': True})


        user_partner = request.env['res.partner'].sudo().search([('email', '=', username), ('password' , '=', password)], limit=1)
        if not user_partner:
            error_descrip = "Email ou mot de passe incorrecte!"
            error = 'empty_username_or_password'
            _logger.error(error_descrip)
            return error_resp(400, error_descrip)

        if user_partner and user_partner.is_verified == False:
            error_descrip = "Email non verifié!"
            error = 'email_not_verified'
            _logger.error(error_descrip)
            return error_resp(400, error_descrip)
        
        if user_partner and user_partner.is_verified == True:
            try:
                request.session.authenticate(db_name, email_admin, password_admin)
            except:
                pass
            
            uid = request.session.uid
        
            # Odoo login failed:
            if not uid:
                error_descrip = "Odoo User authentication failed!"
                error = 'odoo_user_authentication_failed'
                _logger.error(error_descrip)
                return error_response(401, error, error_descrip)
            
            # Generate tokens
            access_token = generate_token()
            expires_in = 3600  # 10 minutes
            refresh_token = generate_token()
            refresh_expires_in = 7200  # 1 heure
            
            if refresh_expires_in < expires_in:
                refresh_expires_in = expires_in
            
            # Save all tokens in store
            _logger.info("Save OAuth2 tokens of user in Token Store...")
            token_store.save_all_tokens(
                request.env,
                access_token = access_token,
                expires_in = expires_in,
                refresh_token = refresh_token,
                refresh_expires_in = refresh_expires_in,
                user_id = uid)
            
            user_context = request.session.context if uid else {}
            company_id = request.env.user.company_id.id if uid else 'null'
         
            user_data = {
                'id': uid,
                'name': user_partner.name,
                'email': user_partner.email,
                'company_id': user_partner.company_id.id,
                'partner_id':user_partner.id,
                'company_id': user_partner.company_id.id,
                'company_name': user_partner.company_id.name,
                'partner_city':user_partner.city,
                'partner_phone':user_partner.phone,
                'country_id':user_partner.country_id.id,
                'country_name':user_partner.country_id.name,
                'country_code':user_partner.country_id.code,
                'country_phone_code':user_partner.country_id.phone_code,
                'is_verified' : user_partner.is_verified,
                'avatar': user_partner.avatar
            }
            # Logout from Odoo and close current 'login' session:
            # request.session.logout()
            
            # Successful response:
            resp = werkzeug.wrappers.Response(
                status = OUT__auth_gettokens__SUCCESS_CODE,
                content_type = 'application/json; charset=utf-8',
                headers = [ ('Cache-Control', 'no-store'),
                            ('Pragma', 'no-cache')  ],
                response = json.dumps({
                    'uid':                  uid,
                    'user_context':         user_context,
                    'company_id':           company_id,
                    'access_token':         access_token,
                    'expires_in':           expires_in,
                    'refresh_token':        refresh_token,
                    'refresh_expires_in':   refresh_expires_in,
                    'user_info':            user_data,
                    'is_verified' :         user_partner.is_verified
                }),
            )
            # Remove cookie session
            resp.set_cookie = lambda *args, **kwargs: None
        else:
            resp =  werkzeug.wrappers.Response(
                status = 401,
                content_type = 'application/json; charset=utf-8',
                response = json.dumps({ 'error': 'Email ou mot de passe incorrecte' })
                )
        return resp
    
    # Refresh access token:
    @http.route('/api/auth/refresh_token', methods=['POST'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    def api_auth_refreshtoken(self, **kw):
        # Get request parameters from url
        args = request.httprequest.args.to_dict()
        # Get request parameters from body
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        
        # Get and check refresh token
        refresh_token = jdata.get('refresh_token')
        if not refresh_token:
            error_descrip = "No refresh token was provided in request!"
            error = 'no_refresh_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        # Validate refresh token
        refresh_token_data = token_store.fetch_by_refresh_token(request.env, refresh_token)
        if not refresh_token_data:
            return error_response_401__invalid_token()
        
        old_access_token = refresh_token_data['access_token']
        new_access_token = generate_token()
        expires_in = self.define_token_expires_in('access', jdata)
        uid = refresh_token_data['user_id']
        
        # Update access (and refresh) token in store
        token_store.update_access_token(
            request.env,
            old_access_token = old_access_token,
            new_access_token = new_access_token,
            expires_in = expires_in,
            refresh_token = refresh_token,
            user_id = uid)
        
        # Successful response:
        resp = werkzeug.wrappers.Response(
            status = OUT__auth_refreshtoken__SUCCESS_CODE,
            content_type = 'application/json; charset=utf-8',
            headers = [ ('Cache-Control', 'no-store'),
                        ('Pragma', 'no-cache')  ],
            response = json.dumps({
                'access_token': new_access_token,
                'expires_in':   expires_in,
            }),
        )
        # Remove cookie session
        resp.set_cookie = lambda *args, **kwargs: None
        return resp
    
    # Delete access tokens from token store:
    @http.route('/api/auth/delete_tokens', methods=['POST'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    def api_auth_deletetokens(self, **kw):
        # Get request parameters from url
        args = request.httprequest.args.to_dict()
        # Get request parameters from body
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        
        # Get and check refresh token
        refresh_token = jdata.get('refresh_token')
        if not refresh_token:
            error_descrip = "No refresh token was provided in request!"
            error = 'no_refresh_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        token_store.delete_all_tokens_by_refresh_token(request.env, refresh_token)
        
        # Successful response:
        return successful_response(
            OUT__auth_deletetokens__SUCCESS_CODE,
            {}
        )
