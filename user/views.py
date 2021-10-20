from django.views import View
from user.models import Users, LoginHistory, Activity
from common.views import decode_post_request, commit_to_db, user_info_and_user_obj
from common.responses import response
from common.views import check_hash_password, hash_password
from user.payload_validation import LoginPayload, RegisterPayload
from datetime import datetime
from django.db.models import Q


class LoginWithPassword(View):
    def app_login_history(self, user_id, device_type, fcm_token):
        app_lh = LoginHistory()
        app_lh.user = Users(user_id)
        app_lh.log_in_time = datetime.now()
        status, error = commit_to_db(app_lh)
        if not error:
            app_lh_ = app_lh.login_history()
            return app_lh_['_id']
        else:
            print('Login history err', error)

    def post(self, request):
        try:
            input_values = decode_post_request(request)
            form = LoginPayload(input_values, False)
            if not form.is_valid():
                return response("create", "failed", form.errors)
            user = Users.objects.get(email__iexact=input_values['email'])
            valid = check_hash_password(input_values['password'], user.password)
            if not valid:
                return response('create', 'unauthorized', {}, " Invalid password!!")
            login_id = self.app_login_history(user._id)
            user_details = user.user_profile_information()
            user_details['access_token'] = user.generate_token(login_id)
            return response('create', 'success', user_details, "Login Successful!")
        except:
            return response('create', 'failure', {}, "User not exist!!")


class Logout(View):
    def post(self, request):
        user_info = user_info_and_user_obj(request)
        if 'login_id' in user_info and user_info['login_id']:
            try:
                app_lh = LoginHistory.objects.get(_id=user_info['login_id'])
            except:
                return response("update", "failed", {}, 'Comeback Soon!!')
            app_lh.log_out_time = datetime.now()
            # committing the object
            status, error = commit_to_db(app_lh)
            if status:
                return response("update", "success", {}, 'Comeback Soon!!')
            else:
                return response("update", "failed", {"error": error})
        else:
            return response("update", "failed", {}, 'Comeback Soon!!')


class Register(View):
    def post(self, request):
        try:
            input_values = decode_post_request(request)
            form = RegisterPayload(input_values, False)
            if not form.is_valid():
                return response("create", "failed", form.errors)
            Users.objects.get(Q(email__iexact=input_values['email']) | Q(mobile__iexact=input_values['mobile']) | Q(username__iexact=input_values['username']))
            return response('create', 'failure', {}, "User already exist!!")
        except:
            try:
                password = hash_password(input_values['password'])
                Users(email=input_values['email'],password = password,username=input_values['username'],mobile=input_values['mobile '],gender='gender' in input_values and input_values['gender'] or None,role='role' in input_values and input_values['role'] or 'USER',).save()
                return response('create', 'success', [], "New user created Successful!")
            except:
                return response('create', 'failure', {}, "Error while creating user!")

    def get(self, request, id):
            try:
                user = Users.objects.get(id=id)
                del user['password']
                return response('retrieve', 'success', user, "User retrived!")
            except:
                return response('retrieve', 'failure', {}, "Error while retriving user!")

    def put(self, request, id):
            try:
                input_values = decode_post_request(request)
                user = Users.objects.get(id=id)
                if 'email' in input_values and input_values['email']:
                    user.email = input_values['email']
                if 'gender' in input_values and input_values['gender']:
                    user.gender = input_values['gender']
                if 'mobile' in input_values and input_values['mobile']:
                    user.mobile = input_values['mobile']
                if 'username' in input_values and input_values['username']:
                    user.username = input_values['username']
                status, error = commit_to_db(user)
                if not error:
                    return response('update', 'success', user, "User updated!!")
                else:
                    return response('update', 'failure', {}, "Error while updating user!")
            except:
                return response('update', 'failure', {}, "Error while updating user!")

    def delete(self, request, id):
        try:
            user = Users.objects.get(id=id)
            user.deleted_at = datetime.now()
            status, error = commit_to_db(user)
            if not error:
                return response('destroy', 'success', user, "User deleted!!")
            else:
                return response('destroy', 'failure', {}, "Error while deleting user!")
        except:
            return response('destroy', 'failure', {}, "Error while deleting user!")

