from django.http import HttpResponse, JsonResponse


def homepage(request):
    return HttpResponse("<h4 style='text-align:center'>Social Network</h4>")


def handler500(request, *args, **argv):
    res = dict()
    res["content"] = {'err':'Internal Error'}
    res["response"] = {}
    res["status"] = 500
    res["message"] = "Invalid request,please try again"
    return JsonResponse(res, status=500, safe=False, content_type="application/json")


def handler404(request, *args, **argv):
    res = {
        "content": {'err':'Page Not Found'},
        "response": {"status": 404, "message": "Failure"}
    }
    return JsonResponse(res, status=404, safe=False, content_type="application/json")


