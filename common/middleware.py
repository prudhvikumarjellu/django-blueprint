from datetime import datetime

import jwt
from django.utils.deprecation import MiddlewareMixin
import time
from common.responses import response
from social.settings import logger, SECRET_KEY
from user.models import Users, LoginHistory, Activity


# Logs creation
class LogsCreationsReqMiddleware(MiddlewareMixin):
    def process_request(self, request):
        breaks = "\n----------------------\n"
        input_data = breaks
        input_data += "IP : [ " + request.META.get('REMOTE_ADDR') + " ]"
        input_data += breaks
        input_data += " Method : [ " + request.method + " ]"
        input_data += breaks
        input_data += " Path : [ " + request.path + " ]"
        input_data += breaks
        if "HTTP_AUTHORIZATION" in request.META:
            input_data += "Auth Token \n" + request.META.get('HTTP_AUTHORIZATION')
            input_data += breaks
        input_data += "\n"
        if not request.FILES:
            try:
                input_data += " data : [ " + str(request.body.decode('utf-8')) + " ]"
            except:
                input_data += " data : [ " + str(request) + " ]"
        # else:
        #     input_data += request.FILES
        try:
            input_data += "\n\n\n"
            print(input_data)
        except Exception as e:
            print(e.message)

        return None


class LogsCreationsResMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        breaks = "\n\n----------------------\n\n"
        print("\n\n" + str(response) + breaks)
        return response


# Auth token checks
class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        api = (request.get_full_path().split('?')[0]).split('/')
        length = len(api)
        if request.method == "OPTIONS":
            pass
        elif api[length - 1] in ["", "login"]:
            pass
        else:
            try:
                check = valid_auth(request)
                if check is 1:
                    pass
                elif check is -1:
                    return response("create", "unauthorized", [], "Unauthorized to access")
                else:
                    return response("create", "unauthorized", [], "Unauthorized to access")
            except:
                return response("create", "unauthorized", [], "Unable to check")


def valid_auth(request):
    try:
        auth = request.META.get('HTTP_X_ACCESS_TOKEN')
        payload = None
        if auth is not None:
            payload = dict(jwt.decode(auth, SECRET_KEY))
        if payload:
            try:
                Users.objects.get(_id=payload["_id"])
                if 'login_id' in payload and payload['login_id']:
                    try:
                        LoginHistory.objects.get(_id=payload['login_id'], log_out_time=None)
                    except:
                        return -1
                return 1
            except:
                return -1

        return -1
    except:
        return -1




class RequestLogMiddleware(object):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):

        if response['content-type'] == 'application/json':
            if getattr(response, 'streaming', False):
                response_body = '<<<Streaming>>>'
            else:
                response_body = response.content
        else:
            response_body = '<<<Not JSON>>>'

        log_data = {
            'user': request.user.pk,

            'remote_address': request.META['REMOTE_ADDR'],
            'server_hostname': socket.gethostname(),

            'request_method': request.method,
            'request_path': request.get_full_path(),
            'request_body': request.body,

            'response_status': response.status_code,
            'response_body': response_body,

            'run_time': time.time() - request.start_time,
        }

        # save log_data in some way

        return response