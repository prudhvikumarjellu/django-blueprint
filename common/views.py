from django.contrib.auth.hashers import make_password, check_password
# from decouple import config
# from authentication.models import User
from common.responses import response
import json
import jwt
# import uuid
from social.settings import SECRET_KEY
from django.utils.crypto import get_random_string
from threading import Thread
import hashlib
from user.models import Users


def random_string_generator(length=8):
    return get_random_string(length=length)


def decode_post_request(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except:
        return response("create", "failure", {}, "Invalid payload")


def decode_post_request_with_dict(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except:
        return {}


def generate_md5_json(content):
    strval = json.dumps(content, sort_keys=True, indent=2)
    return hashlib.md5(strval.encode("utf-8")).hexdigest()


def user_info_and_user_obj(request) -> object:
    try:
        auth = request.META.get('HTTP_X_ACCESS_TOKEN')
        token = auth.split()
        payload = None
        if len(token):
            payload = dict(jwt.decode(token[0], SECRET_KEY))
        if payload:
            try:
                user = Users.objects.get(_id=payload["_id"])
                return {
                    'user_obj': user,
                    'user_details': user.user_profile_information(),
                    'login_id': 'login_id' in payload and payload['login_id'] or None,
                    'is_guest': 'is_guest' in payload and payload['is_guest'] or True
                }
            except:
                return 0
        else:
            return 0
    except:
        return 0


def hash_password(value):
    password = make_password(value)
    return password


def check_hash_password(user_password, db_password):
    return check_password(user_password, db_password)


def commit_to_db(model_object):
    # model_object._id = str(uuid.uuid4())
    try:
        model_object.save()
        return True, None
    except Exception as e:
        return False, e


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def find_index_from_array(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == str(value):
            return i
    return -1
