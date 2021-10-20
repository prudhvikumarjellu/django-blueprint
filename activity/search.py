from common.responses import response
from django.views import View

from more.settings import logger
from orders.models import PurchaseDetails, Cart
from authentication.models import User
from common.views import user_info_and_user_obj
from orders.order_details import status_display
from django.db.models import Q, F


class Search(View):
    def get(self, request, order_id):
        page = int(request.GET.get('page', 1))
        skip = (page - 1) * 20
        limit = page * 20
        try:
            resp = []
            user_info = user_info_and_user_obj(request)
            print("storecode", user_info['user_details']['storecode'], order_id)
            try:
                resp = list(
                    PurchaseDetails.objects.filter((Q(divum_order_id=order_id)),
                                                   store_code=user_info['user_details']['storecode'],
                                                   ).exclude(
                        status__in=['added']).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at').order_by('-order_created_at',
                                                                                              '-slot__slot_start_time'
                                                                                              ))[skip:limit]
            except Exception as e:
                pass
            for obj in resp:
                obj['status'] = status_display(obj['status'])
            resp2 = list(
                Cart.objects.filter(
                    (Q(user_id__mobile__icontains=order_id) | (Q(purchase_detail__order_id__icontains=order_id)) | Q(
                        name__icontains=order_id) | Q(description__icontains=order_id) | Q(
                        purchase_detail__status__icontains=order_id)),
                    purchase_detail__store_code=user_info['user_details'][
                        'storecode']).annotate(
                    order_created_at=F('purchase_detail__order_created_at'),
                    divum_order_id=F('purchase_detail__divum_order_id'),
                    slot__slot_end_time=F('purchase_detail__slot__slot_end_time'),
                    slot_date=F('purchase_detail__slot_date'),
                    slot__slot_start_time=F('purchase_detail__slot__slot_start_time'),
                    user_id__mobile=F('purchase_detail__user_id__mobile'),
                    paid_amount=F('purchase_detail__paid_amount'),
                    order_id=F('purchase_detail__order_id'),
                    purchase_detail___id=F('purchase_detail___id'),
                    purchase_detail__created_at=F('purchase_detail__created_at'),
                    purchase_detail__status=F('purchase_detail__status'), ).values(
                    'purchase_detail___id', 'order_id', 'purchase_detail__created_at', 'paid_amount',
                    'purchase_detail__status', 'user_id__mobile',
                    'slot__slot_start_time', 'slot_date',
                    'slot__slot_end_time', 'divum_order_id', 'order_created_at').order_by(
                    '-purchase_detail__order_created_at',
                    '-purchase_detail__slot__slot_start_time'))[skip:limit]

            for obj in resp2:
                obj['_id'] = obj['purchase_detail___id']
                obj['created_at'] = obj['purchase_detail__created_at']
                obj['status'] = status_display(obj['purchase_detail__status'])
                resp.append(obj)
            return response('retrive', 'success', resp, "Data Fetched successfully")

        except Exception as e:
            return response('retrive', 'failure', {}, "Order Not Found")
