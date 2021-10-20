from django.http import JsonResponse


# keys type: create, update, retrieve, destroy, login and status: success, unauthorized, failure
def response(type, status, content, message=None):
    res = dict()
    res["content"] = content
    res["response"] = {}
    resp = dict()
    if type == "create":
        if status == "success":
            resp["status"] = 200
            resp["message"] = "Successfully Created"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=200, safe=False, content_type="application/json")

        elif status == "unauthorized":
            resp["status"] = 401
            resp["message"] = "Unauthorized to Create"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=401, safe=False, content_type="application/json")
        elif status == "acceptable":
            resp["status"] = 201
            resp["message"] = "Acceptable request"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=201, safe=False, content_type="application/json")
        else:
            resp["status"] = 400
            resp["message"] = "Failed to Create"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=409, safe=False, content_type="application/json")
    elif type == "update":
        if status == "success":
            resp["status"] = 200
            resp["message"] = "Successfully Updated"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=200, safe=False, content_type="application/json")
        elif status == "unauthorized":
            resp["status"] = 401
            resp["message"] = "Unauthorized to Update"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=401, safe=False, content_type="application/json")
        else:
            resp["status"] = 400
            resp["message"] = "Failed to Update"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=400, safe=False, content_type="application/json")
    elif type == "retrieve":
        if status == "success":
            resp["status"] = 200
            resp["message"] = "Successfully Retrieved"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=200, safe=False, content_type="application/json")
        elif status == "unauthorized":
            resp["status"] = 401
            resp["message"] = "Unauthorized to Retrieve"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=401, safe=False, content_type="application/json")
        else:
            resp["status"] = 400
            resp["message"] = "Failed to Retrieve"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=400, safe=False, content_type="application/json")
    elif type == "destroy":
        if status == "success":
            resp["status"] = 200
            resp["message"] = "Successfully Deleted"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=200, safe=False, content_type="application/json")
        elif status == "unauthorized":
            resp["status"] = 401
            resp["message"] = "Unauthorized to Delete"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=401, safe=False, content_type="application/json")
        else:
            resp["status"] = 400
            resp["message"] = "Failed to Delete"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=400, safe=False, content_type="application/json")
    elif type == "login":
        if status == "success":
            resp["status"] = 200
            resp["message"] = "Successfully Logged In"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=200, safe=False, content_type="application/json")
        elif status == "unauthorized":
            resp["status"] = 401
            resp["message"] = "Unauthorized to Login"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=401, safe=False, content_type="application/json")
        else:
            resp["status"] = 400
            resp["message"] = "Failed to Login"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=400, safe=False, content_type="application/json")
    elif type == "methodNotAllowed":
        resp["status"] = 405
        resp["message"] = "Method Not Allowed"
        if message:
            resp["message"] = message
        res["response"] = resp
        return JsonResponse(res, status=405, safe=False, content_type="application/json")
    else:
        if status == "failure":
            resp["status"] = 400
            resp["message"] = "Failure"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=400, safe=False, content_type="application/json")
        else:
            resp["status"] = 200
            resp["message"] = "Success"
            if message:
                resp["message"] = message
            res["response"] = resp
            return JsonResponse(res, status=200, safe=False, content_type="application/json")
