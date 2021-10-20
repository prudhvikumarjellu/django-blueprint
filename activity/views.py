from datetime import datetime, timedelta

from decouple import config
from django.contrib.postgres.aggregates import ArrayAgg

from orders.models import WhatsAppSession, WhatsappTemplate
from chats.views import send_two_way_message_to_user_with_sms, send_sms_to_user, send_two_way_message_to_user, \
    send_two_way_message_to_user_for_template
from common.responses import response
from django.views import View
from common.wa_messages import messages
from orders.models import OrderStatus, Cart, PurchaseDetails
from common.views import decode_post_request
from orders.payload_validation import UpdateStatusPayload, PickupPayload
from more.settings import logger
from authentication.models import StoreDetail
import requests


def status_key(status):
    if status == 'Picking Done':
        return 'picking_done'
    elif status == 'Billing Done':
        return 'billing_done'
    elif status == 'Payment Done':
        return 'payment_done'
    elif status == 'Items Delivered':
        return 'items_delivered'
    else:
        return status


class PickItem(View):
    def post(self, request):
        try:
            input_values = decode_post_request(request)
            form = PickupPayload(input_values, False)
            if not form.is_valid():
                return response("create", "failed", form.errors)
            Cart.objects.filter(purchase_detail___id=input_values['purchase_id'],
                                product_id___id=input_values['product_id']).update(is_picked=input_values['is_picked'],
                                                                                   status='billing_done')
            count = Cart.objects.filter(purchase_detail___id=input_values['purchase_id'], is_picked=False).count()
            if count == 0:
                PurchaseDetails.objects.filter(_id=input_values['purchase_id']).update(status='billing_done')
                order_data = {'status': 'billing_done', 'purchase_detail_id_id': input_values['purchase_id'],
                              'status_updated_on': 'sm'}
                OrderStatus.objects.update_or_create(
                    status='billing_done', purchase_detail_id___id=input_values['purchase_id'],
                    defaults=order_data)
            return response('update', 'success', '', "Data Fetched successfully")
        except:
            return response('update', 'failure', '', "Error while fetching data!!")


class UpdateStatus(View):
    def post(self, request):
        try:
            input_values = decode_post_request(request)
            form = UpdateStatusPayload(input_values, False)
            if not form.is_valid():
                return response("create", "failed", form.errors)
            input_values['status'] = status_key(input_values['status'])
            if input_values['status'] == 'picking_done':
                purchase_det = PurchaseDetails.objects.get(_id=input_values['purchase_id'], status='order placed')
                purchase_det.status = input_values['status']
                purchase_det.save()
                Cart.objects.filter(purchase_detail___id=purchase_det._id).update(is_picked=True, status='picking_done')
            else:
                purchase_det = PurchaseDetails.objects.get(_id=input_values['purchase_id'])
                purchase_det.status = input_values['status']
                purchase_det.save()
                Cart.objects.filter(purchase_detail___id=purchase_det._id).update(status=input_values['status'])
            order_data = {'status': input_values['status'], 'purchase_detail_id_id': input_values['purchase_id'],
                          'status_updated_on': 'sm'}
            OrderStatus.objects.update_or_create(
                status=input_values['status'], purchase_detail_id___id=input_values['purchase_id'], defaults=order_data)
            wa_number = len(
                purchase_det.user_id.mobile) == 10 and '91' + purchase_det.user_id.mobile or purchase_det.user_id.mobile
            if input_values['status'] == 'items_delivered':
                on_going_order = list(PurchaseDetails.objects.filter(user_id_id=purchase_det.user_id_id,
                                                                     status__in=['order placed', 'picking_done',
                                                                                 'billing_done',
                                                                                 'payment_done']).values(
                    'store_code').annotate(
                    order_ids=ArrayAgg('divum_order_id')).values('store_code',
                                                                 'order_ids'))
                if len(on_going_order) == 0:
                    time_threshold = datetime.now() - timedelta(hours=24)
                    try:
                        wa_session = WhatsAppSession.objects.get(wa_number=wa_number, is_active_session=True,
                                                                 created_at__gte=time_threshold)
                        wa_session.is_active_session = False
                        wa_session.save()
                    except:
                        print('except on item delivery wa')
            start_time = str(purchase_det.slot.slot_start_time)[:-3].split(':')
            end_time = str(purchase_det.slot.slot_end_time)[:-3].split(':')
            if int(start_time[0]) <= 11:
                start_time = str(start_time[0]) + ':' + str(start_time[1]) + ' AM'
            elif int(start_time[0]) == 12:
                start_time = str(start_time[0]) + ':' + str(start_time[1]) + ' PM'
            else:
                start_time = str(int(start_time[0]) - 12) + ':' + str(start_time[1]) + ' PM'
            if int(end_time[0]) <= 11:
                end_time = str(end_time[0]) + ':' + str(end_time[1]) + ' AM'
            elif int(end_time[0]) == 12:
                end_time = str(end_time[0]) + ':' + str(end_time[1]) + ' PM'
            else:
                end_time = str(int(end_time[0]) - 12) + ':' + str(end_time[1]) + ' PM'
            try:
                time_threshold = datetime.now() - timedelta(hours=24)
                WhatsAppSession.objects.get(wa_number=wa_number, is_active_session=True,
                                            created_at__gte=time_threshold)
                if input_values['status'] == 'billing_done':
                    if purchase_det.pos_upi_payment_type == 'cod':
                        msg = messages()['billing_done_cod'].format(order_id=str(purchase_det.divum_order_id),
                                                                    slot=str(start_time) + ' - ' + str(end_time))
                        send_two_way_message_to_user_with_sms({'message': msg, 'to_user': wa_number})
                    else:
                        msg = messages()['billing_done_online'].format(order_id=str(purchase_det.divum_order_id))
                        send_two_way_message_to_user_with_sms({'message': msg, 'to_user': wa_number})
                elif input_values['status'] == 'payment_done':
                    msg = messages()['payment_done'].format(order_id=str(purchase_det.divum_order_id),
                                                            slot=str(start_time) + ' - ' + str(end_time))
                    send_sms_to_user(msg, wa_number)
                    wa_msg = messages()['payment_done_wa'].format(order_id=str(purchase_det.divum_order_id),
                                                                  slot=str(start_time) + ' - ' + str(end_time))
                    send_two_way_message_to_user({'message': wa_msg, 'to_user': wa_number})
                elif input_values['status'] == 'items_delivered':
                    msg = messages()['items_delivered'].format(order_id=str(purchase_det.divum_order_id))
                    send_two_way_message_to_user_with_sms({'message': msg, 'to_user': wa_number})
                    try:
                        logger.debug('TRY function' + str(on_going_order))
                        if len(on_going_order):
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
            except:
                msg = ""
                template_msg = ""
                other_wa_number = purchase_det.user_id.whatsapp_consent_accepted and purchase_det.user_id.wa_mobile or wa_number
                if input_values['status'] == 'billing_done':
                    if purchase_det.pos_upi_payment_type == 'cod':
                        msg = messages()['billing_done_cod'].format(order_id=str(purchase_det.divum_order_id),
                                                                    slot=str(start_time) + ' - ' + str(end_time))
                        template_details = WhatsappTemplate.objects.get(key='billing_cod')
                        template_msg = messages()['billing_done_cod_template'].format(
                            template_id=template_details.template, order_id=str(purchase_det.divum_order_id),
                            slot=str(start_time) + '-' + str(end_time))
                    else:
                        msg = messages()['billing_done_online'].format(order_id=str(purchase_det.divum_order_id))
                        template_details = WhatsappTemplate.objects.get(key='billing_online')
                        template_msg = messages()['billing_done_online_template'].format(
                            template_id=template_details.template, order_id=str(purchase_det.divum_order_id))
                elif input_values['status'] == 'payment_done':
                    msg = messages()['payment_done'].format(order_id=str(purchase_det.divum_order_id),
                                                            slot=str(start_time) + ' - ' + str(end_time))
                    template_details = WhatsappTemplate.objects.get(key='payment')
                    template_msg = messages()['payment_done_template'].format(
                        template_id=template_details.template, order_id=str(purchase_det.divum_order_id),
                        slot=str(start_time) + ' - ' + str(end_time))
                elif input_values['status'] == 'items_delivered':
                    msg = messages()['items_delivered'].format(order_id=str(purchase_det.divum_order_id))
                    template_details = WhatsappTemplate.objects.get(key='delivered')
                    template_msg = messages()['delivery_done_template'].format(
                        template_id=template_details.template, order_id=str(purchase_det.divum_order_id))
                    try:
                        if len(on_going_order):
                            on_going_template_details = WhatsappTemplate.objects.get(key='on_going_orders')
                            for order in on_going_order:
                                store_det = StoreDetail.objects.get(store_code=order['store_code'])
                                msg = messages()['on_going_orders'].format(
                                    order_id=','.join(map(str, order['order_ids'])),
                                    sm_number=config('customer_care_number'),
                                    store_time=str(store_det.open_time)[:-3] + ' AM - ' + str(
                                        int(str(store_det.close_time)[
                                            :-3].split(':')[0]) - 12) + ':' + str(store_det.close_time)[
                                                                              :-3].split(':')[1] + ' PM')
                                send_sms_to_user(msg, wa_number)
                                on_going_template_msg = messages()['on_going_orders_template'].format(
                                    template_id=on_going_template_details.template,
                                    order_id=','.join(map(str, order['order_ids'])),
                                    sm_number=config('customer_care_number'),
                                    store_time=str(store_det.open_time)[:-3] + ' AM ' + str(
                                        int(str(store_det.close_time)[:-3].split(':')[0]) - 12) + ':' +
                                               str(store_det.close_time)[:-3].split(':')[1] + ' PM')
                                if purchase_det.user_id.whatsapp_consent_accepted:
                                    send_two_way_message_to_user_for_template(
                                        {'template': on_going_template_msg, 'to_user': other_wa_number})
                    except:
                        pass
                send_sms_to_user(msg, wa_number)
                if purchase_det.user_id.whatsapp_consent_accepted:
                    send_two_way_message_to_user_for_template(
                        {'template': template_msg, 'to_user': other_wa_number})
            return response('create', 'success', {}, "Data Saved successfully")
        except Exception as e:
            return response('create', 'failure', {'data': str(e)}, "Error while Saving data!!")


class PriceActionChange(View):
    def get(self, request, purchase_id):
        is_billing_done = OrderStatus.objects.filter(purchase_detail_id=purchase_id, status='billing_done').count()
        if is_billing_done:
            try:
                purchase = PurchaseDetails.objects.get(_id=purchase_id)
                if purchase.sm_initiated_txn == 'refund_initiated':
                    return response('retrieve', 'success', {'type': 'refund', 'amount': None, 'is_initiated': True},
                                    purchase.sm_initiated_txn)
                elif purchase.sm_initiated_txn == 'initiate_new_txn':
                    return response('create', 'success', {'type': 'initiate_new_txn', 'is_initiated': True},
                                    purchase.sm_initiated_txn)
                elif purchase.sm_initiated_txn == 'sent_payment_link' and not request.GET.get('retry', False):
                    return response('create', 'success', {'type': 'sent_payment_link', 'is_initiated': True},
                                    purchase.sm_initiated_txn)
                if purchase.pos_upi_payment_type not in ['cod', 'online_payment']:
                    if purchase.initial_paid_amount > purchase.paid_amount:
                        return response('retrieve', 'success', {'type': 'refund',
                                                                'amount': float(
                                                                    purchase.initial_paid_amount - purchase.paid_amount),
                                                                'is_initiated': False})
                    elif purchase.paid_amount > purchase.initial_paid_amount:
                        return response('retrieve', 'success', {'type': 'initiate_new_txn', 'amount': float(
                            purchase.paid_amount - purchase.initial_paid_amount), 'is_initiated': False})
                elif purchase.pos_upi_payment_type in ['online_payment', 'cod']:
                    return response('retrieve', 'success', {'type': 'initiate_new_txn', 'amount': float(
                        purchase.paid_amount), 'is_initiated': False})
                return response('retrieve', 'failure', {}, '')
            except Exception as e:
                return response('retrieve', 'failure', {}, 'Exception: ' + str(e))
        else:
            return response('retrieve', 'failure', {}, 'Please mark the status as billing done.')


def initiate_refund(purchase_id):
    headers = dict()
    headers['Content-Type'] = 'application/json'
    try:
        logger.debug("BEFORE API CALL")
        resp = requests.post(config('refund_end_point'), json={'purchase_id': str(purchase_id)}, headers=headers)
        logger.debug("AFTER API CALL" + str(resp.json()))
        logger.debug("AFTER API CALL" + str(resp.text))
        if resp.status_code == 200:
            return resp.json(), True
        else:
            return resp.json(), False
    except Exception as e:
        return {'response': {
            'message': str(e)
        }}, False


class InitiateRefund(View):
    def post(self, request, purchase_id):
        logger.debug("INSIDE*******************")
        is_billing_done = OrderStatus.objects.filter(purchase_detail_id=purchase_id, status='billing_done').count()
        if is_billing_done:
            try:
                logger.debug("INSIDE*******************")
                purchase = PurchaseDetails.objects.get(_id=purchase_id)
                if purchase.sm_initiated_txn == 'refund_initiated':
                    return response('create', 'success', {'type': 'refund', 'amount': None, 'is_initiated': True},
                                    purchase.sm_initiated_txn)

                if purchase.pos_upi_payment_type not in ['cod', 'online_payment']:
                    if purchase.initial_paid_amount > purchase.paid_amount:
                        resp, is_success = initiate_refund(purchase_id)
                        if is_success:
                            purchase.sm_initiated_txn = 'refund_initiated'
                            purchase.save()
                            return response('create', 'success', {}, resp['response']['message'])
                        else:
                            return response('create', 'failure', {}, resp['response']['message'])
                return response('create', 'failure', {}, '')
            except:
                return response('create', 'failure', {}, '')
        else:
            return response('create', 'failure', {}, '')


def initiate_txn(purchase_id):
    headers = dict()
    headers['Content-Type'] = 'application/json'
    try:
        logger.debug("BEFORE API CALL")
        resp = requests.post(config('new_txn_end_point'), json={'purchase_id': purchase_id}, headers=headers)
        logger.debug("AFTER API CALL")
        logger.debug("AFTER API CALL" + str(resp.json()))
        if resp.status_code == 200:
            return resp.json(), True
        else:
            return resp.json(), False
    except Exception as e:
        return {'response': {
            'message': str(e)
        }}, False


class InitiateNewTransaction(View):
    def post(self, request, purchase_id):
        is_billing_done = OrderStatus.objects.filter(purchase_detail_id=purchase_id, status='billing_done').count()
        if is_billing_done:
            try:
                logger.debug("INSIDE*******************")
                purchase = PurchaseDetails.objects.get(_id=purchase_id)
                if purchase.pos_upi_payment_type in ['cod',
                                                     'online_payment'] or purchase.paid_amount > purchase.initial_paid_amount:
                    resp, is_success = initiate_txn(purchase_id)
                    if is_success:
                        purchase.sm_initiated_txn = 'sent_payment_link'
                        purchase.save()
                        return response('create', 'success', {}, resp['response']['message'])
                    else:
                        return response('create', 'failure', {}, resp['response']['message'])
                return response('create', 'failure', {}, '')
            except:
                return response('create', 'failure', {}, '')
        else:
            return response('create', 'failure', {}, '')
