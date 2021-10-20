from django.db.models import Q, Value, BooleanField

from authentication.models import StoreDetail
from orders.models import WhatsAppSession
from chats.views import send_two_way_message_to_user_with_sms
from common.responses import response
from django.views import View
from common.wa_messages import messages
from more.settings import logger
from orders.models import OrderStatus, Cart, PurchaseDetails, CancelOrderReason
from common.views import decode_post_request
from orders.payload_validation import CancelPayload
from datetime import datetime, timedelta
from django.contrib.postgres.aggregates import ArrayAgg
from decouple import config

from orders.views import initiate_refund


class CancelOrder(View):
    def post(self, request):
        try:
            input_values = decode_post_request(request)
            form = CancelPayload(input_values, False)
            if not form.is_valid():
                return response("create", "failed", form.errors)
            purchase_det = PurchaseDetails.objects.get(Q(_id=input_values['purchase_id']), ~Q(
                status__in=['payment_done', 'items_delivered']))
            purchase_det.status = 'cancelled'
            purchase_det.cancel_reason = input_values['reason']
            purchase_det.is_cancelled = True
            purchase_det.paid_amount = 0
            purchase_det.save()
            Cart.objects.filter(purchase_detail___id=purchase_det._id).update(is_cancelled=True, status='cancelled')
            order_data = {'status': 'cancelled', 'purchase_detail_id_id': input_values['purchase_id'],
                          'status_updated_on': 'sm'}
            OrderStatus.objects.update_or_create(
                status='canceled', purchase_detail_id___id=input_values['purchase_id'], defaults=order_data)
            try:
                msg = messages()['cancel_orders'].format(order_id=str(purchase_det.divum_order_id),
                                                         reason=input_values['reason'])
                send_two_way_message_to_user_with_sms({'message': msg, 'to_user': purchase_det.user_id.mobile})
                on_going_order = list(PurchaseDetails.objects.filter(user_id_id=purchase_det.user_id_id,
                                                                     status__in=['order placed', 'picking_done',
                                                                                 'billing_done',
                                                                                 'payment_done']).values(
                    'store_code').annotate(
                    order_ids=ArrayAgg('divum_order_id')).values('store_code',
                                                                 'order_ids'))
                if len(on_going_order) > 0:
                    time_threshold = datetime.now() - timedelta(hours=24)
                    try:
                        wa_number = len(
                            purchase_det.user_id.mobile) == 10 and '91' + purchase_det.user_id.mobile or purchase_det.user_id.mobile
                        wa_session = WhatsAppSession.objects.get(wa_number=wa_number, is_active_session=True,
                                                                 created_at__gte=time_threshold)
                        wa_session.is_active_session = False
                        wa_session.save()
                        logger.debug('TRY function')
                        for order in on_going_order:
                            store_det = StoreDetail.objects.get(store_code=order['store_code'])
                            msg = messages()['on_going_orders'].format(
                                order_id=','.join(map(str, order['order_ids'])),
                                sm_number=config('customer_care_number'),
                                store_time=str(store_det.open_time)[:-3] + ' AM - ' + str(
                                    int(str(store_det.close_time)[
                                        :-3].split(':')[0]) - 12) + ':' + str(store_det.close_time)[
                                                                          :-3].split(':')[1] + ' PM')
                            logger.debug('Before sms function' + msg)
                            send_two_way_message_to_user_with_sms({'message': msg, 'to_user': wa_number})
                    except Exception as e:
                        logger.debug('Exception error' + str(e))
                        pass
                        print('except on item delivery wa')
            except:
                pass
            try:
                logger.debug('Before If')
                if purchase_det.pos_upi_payment_type not in ['cod', 'online_payment']:
                    logger.debug('Inside If')
                    if float(purchase_det.initial_paid_amount) > float(purchase_det.paid_amount):
                        logger.debug('Inside second If')
                        resp, is_success = initiate_refund(purchase_det._id)
                        logger.debug('After initiate' + str(resp) + str(is_success))
                        if is_success:
                            logger.debug('Success')
                            purchase_det.sm_initiated_txn = 'refund_initiated'
                            purchase_det.save()
                logger.debug('Outside If')
            except Exception as e:
                logger.debug('Exception on refund' + str(e))
                pass
            return response('create', 'success', '', "Order cancelled successfully")
        except Exception as e:
            return response('create', 'failure', {'error': str(e)}, "Error while Cancelling order!!")


class CancelOrderReasonList(View):
    def get(self, request):
        reasons = list(CancelOrderReason.objects.filter(type='sm', deleted_at=None).annotate(
            is_selected=Value(False, output_field=BooleanField())
        ).values('_id', 'reason', 'is_selected'))
        return response('retrive', 'success', {'data': reasons}, "reasons fetched successfully")
