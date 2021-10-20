from common.responses import response
from django.views import View
from orders.models import WhatsAppSession
from orders.models import OrderStatus, Cart, PurchaseDetails, RefundCart, SlotTiming, ProductDetail, UserOnboarding
from authentication.models import Activity, Picker
from datetime import date, datetime, timedelta
from django.db.models import F, Case, When, Q, CharField, Value, BooleanField, Count, IntegerField, Sum
from django.contrib.postgres.aggregates import ArrayAgg
from common.views import user_info_and_user_obj, find_index_from_array, decode_post_request, \
    decode_post_request_with_dict
from orders.payload_validation import UpdateCartPayload, UpdatePurchaseDetailsPayload
import csv
from more.settings import logger


def status_display(status):
    if status == 'order placed':
        return 'Order Placed'
    elif status == 'picking_done':
        return 'Picking Done'
    elif status == 'billing_done':
        return 'Billing Done'
    elif status == 'payment_done':
        return 'Payment Done'
    elif status == 'items_delivered':
        return 'Items Delivered'
    elif status == 'cancelled':
        return 'Cancelled'
    else:
        return status


def status_filter():
    result = {'data': [{
        'key': 'order placed',
        'name': 'Order Placed',
        'is_applied': False
    }, {
        'key': 'picking_done',
        'name': 'Picking Done',
        'is_applied': False
    }, {
        'key': 'billing_done',
        'name': 'Billing Done',
        'is_applied': False
    }, {
        'key': 'payment_done',
        'name': 'Payment Done',
        'is_applied': False
    }, {
        'key': 'items_delivered',
        'name': 'Items Delivered',
        'is_applied': False
    }, {
        'key': 'cancelled',
        'name': 'Cancelled',
        'is_applied': False
    }], 'display': 'Status'}
    return result


def future_date_filter():
    today_date = date.today()
    tomorrow = today_date + timedelta(days=1)
    day_after_tomorrow = today_date + timedelta(days=2)
    next_week_start = today_date + timedelta(days=3)
    next_week_end = today_date + timedelta(days=6)
    return {'data': [{
        'start': tomorrow,
        'end': tomorrow,
        'name': 'Tomorrow',
        'is_applied': False
    }
        #     , {
        #     'start': day_after_tomorrow,
        #     'end': day_after_tomorrow,
        #     'name': 'Day after Tomorrow',
        #     'is_applied': False
        # }, {
        #     'start': next_week_start,
        #     'end': next_week_end,
        #     'name': 'Next Week',
        #     'is_applied': False
        # }
    ], 'display': 'Date'}


def date_filter():
    today_date = date.today()
    tomorrow = today_date + timedelta(days=1)
    yesterday = today_date + timedelta(days=-1)
    day_before_yesterday = today_date + timedelta(days=-2)
    last_week_start = today_date + timedelta(days=-3)
    last_week_end = today_date + timedelta(days=-7)
    return {'data': [{
        'start': today_date,
        'end': today_date,
        'name': 'Today',
        'is_applied': False
    }, {
        'start': tomorrow,
        'end': tomorrow,
        'name': 'Tomorrow',
        'is_applied': False
    }, {
        'start': yesterday,
        'end': yesterday,
        'name': 'Yesterday',
        'is_applied': False
    }, {
        'start': day_before_yesterday,
        'end': day_before_yesterday,
        'name': 'Day Before Yesterday',
        'is_applied': False
    }, {
        'start': last_week_start,
        'end': last_week_end,
        'name': 'Last Week',
        'is_applied': False
    }], 'display': 'Date'}


def past_date_filter():
    today_date = date.today()
    yesterday = today_date + timedelta(days=-1)
    day_before_yesterday = today_date + timedelta(days=-2)
    last_week_start = today_date + timedelta(days=-3)
    last_week_end = today_date + timedelta(days=-7)
    return {'data': [{
        'start': yesterday,
        'end': yesterday,
        'name': 'Yesterday',
        'is_applied': False
    }, {
        'start': day_before_yesterday,
        'end': day_before_yesterday,
        'name': 'Day Before Yesterday',
        'is_applied': False
    }, {
        'start': last_week_start,
        'end': last_week_end,
        'name': 'Last Week',
        'is_applied': False
    }], 'display': 'Date'}


def slot_filter(store):
    slots = list(
        SlotTiming.objects.filter(store_code=store).values('slot_start_time',
                                                           'slot_end_time').distinct())
    result = []
    for item in slots:
        result.append({'_id': '12', 'slot_start_time': item['slot_start_time'],
                       'slot_end_time': item['slot_end_time'], 'is_applied': False})
    return {'data': result, 'display': 'Delivery Slot'}


class CurrentOrders(View):
    def find(self, lst, key1, key2, value1, value2):
        for i, dic in enumerate(lst):
            if (dic[key1] == str(value1) and dic[key2] == str(value2)):
                return i
        return -1

    def find_three(self, lst, key1, key2, key3, value1, value2, value3):
        for i, dic in enumerate(lst):
            if (dic[key1] == str(value1) and dic[key2] == str(value2) and dic[key3] == str(value3)):
                return i
        return -1

    def get(self, request, type):
        try:
            user_info = user_info_and_user_obj(request)
            # Todo Add 5:30 to get orders
            current_date = datetime.now() + timedelta(hours=5, minutes=30)
            today = date.today()
            resp = []
            if type == 'today':
                data_list = list(PurchaseDetails.objects.filter(slot_date=today,
                                                                slot__store_code=user_info['user_details'][
                                                                    'storecode']).exclude(
                    status__in=['added']).values(
                    '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile', 'slot_date',
                    'slot__slot_start_time', 'slot__slot_end_time', 'divum_order_id', 'order_created_at',
                    'is_sudo_order').order_by(
                    '-slot__slot_start_time', '-order_created_at'))
                for obj in data_list:
                    res_index = self.find(resp, 'slot__slot_start_time', 'slot__slot_end_time',
                                          obj['slot__slot_start_time'], obj['slot__slot_end_time'])
                    obj['status'] = status_display(obj['status'])
                    if res_index >= 0:
                        resp[res_index]['orders'].append(obj)
                    else:
                        resp.append({
                            'slot__slot_start_time': str(obj['slot__slot_start_time']),
                            'slot__slot_end_time': str(obj['slot__slot_end_time']),
                            'orders': [obj]
                        })
            elif type == 'up_coming':
                data_list = list(
                    PurchaseDetails.objects.filter(slot_date__gt=today,
                                                   slot__store_code=user_info['user_details']['storecode']).exclude(
                        status__in=['added']).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at', 'is_sudo_order').order_by(
                        '-slot__slot_start_time',
                        '-order_created_at'))
                for obj in data_list:
                    obj['status'] = status_display(obj['status'])
                    date_index = find_index_from_array(resp, 'slot_date', obj['slot_date'])
                    if date_index >= 0:
                        res_index = self.find(resp[date_index]['slot'], 'slot__slot_start_time',
                                              'slot__slot_end_time',
                                              obj['slot__slot_start_time'], obj['slot__slot_end_time'], )
                        if res_index >= 0:
                            resp[date_index]['slot'][res_index]['orders'].append(obj)
                        else:
                            resp[date_index]['slot'] = [{
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            }]
                    else:
                        resp.append({
                            'slot_date': str(obj['slot_date']),
                            'slot': [{
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            }]
                        })
            else:
                resp = list(
                    PurchaseDetails.objects.filter(slot_date__lt=today,
                                                   slot__store_code=user_info['user_details']['storecode']).exclude(
                        status__in=['added']).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at', 'is_sudo_order').order_by(
                        '-slot__slot_start_time',
                        '-order_created_at'))
                for obj in resp:
                    obj['status'] = status_display(obj['status'])
            return response('retrive', 'success', resp, "Data Fetched successfully")
        except Exception as e:
            print('error', e)
            return response('retrive', 'failure', '', "Error while fetching data!!")

    def post(self, request, type):
        try:
            user_info = user_info_and_user_obj(request)
            input_values = decode_post_request_with_dict(request)
            # Todo Add 5:30 to get orders
            current_date = datetime.now() + timedelta(hours=5, minutes=30)
            today = current_date.today()
            logger.debug('11111111111111111')
            resp = []
            is_filter_applied = True
            if type == 'today' or type == 'total_orders':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = [status_filter()]
                filter_array = []
                status_index = find_index_from_array(input_values['filter'], 'display', 'Status')
                for item in input_values['filter'][status_index]['data']:
                    if item['is_applied']:
                        filter_array.append(item['key'])
                if len(filter_array):
                    query = Q(status__in=filter_array)
                else:
                    query = Q()
                logger.debug('22222222222222222222')
                data_list = list(PurchaseDetails.objects.filter(slot_date=today,
                                                                store_code=user_info['user_details'][
                                                                    'storecode']).filter(query).exclude(
                    status__in=['added']).values(
                    '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile', 'slot_date',
                    'slot__slot_start_time', 'slot__slot_end_time', 'divum_order_id', 'order_created_at',
                    'is_sudo_order').order_by(
                    '-slot__slot_start_time', '-order_created_at'))
                logger.debug('33333333333333333333')
                for obj in data_list:
                    res_index = self.find(resp, 'slot__slot_start_time', 'slot__slot_end_time',
                                          obj['slot__slot_start_time'], obj['slot__slot_end_time'])
                    obj['status'] = status_display(obj['status'])
                    if res_index >= 0:
                        resp[res_index]['orders'].append(obj)
                    else:
                        resp.append({
                            'slot__slot_start_time': str(obj['slot__slot_start_time']),
                            'slot__slot_end_time': str(obj['slot__slot_end_time']),
                            'orders': [obj]
                        })
            elif type == 'stuck':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = [status_filter()]
                    input_values['filter'].append(past_date_filter())
                    input_values['filter'].append(slot_filter(user_info['user_details']['storecode']))
                status_filter_array = []
                status_index = find_index_from_array(input_values['filter'], 'display', 'Status')
                for item in input_values['filter'][status_index]['data']:
                    if item['is_applied']:
                        status_filter_array.append(item['key'])
                if len(status_filter_array):
                    status_query = Q(status__in=status_filter_array)
                else:
                    status_query = Q()
                date_index = find_index_from_array(input_values['filter'], 'display', 'Date')
                start_date = ''
                end_date = ''
                for item in input_values['filter'][date_index]['data']:
                    if item['is_applied']:
                        if not start_date:
                            start_date = item['start']
                        elif datetime.strptime(item['start'], '%Y-%m-%d') < datetime.strptime(start_date,
                                                                                              '%Y-%m-%d'):
                            start_date = item['start']
                        if not end_date:
                            end_date = item['end']
                        elif datetime.strptime(item['end'], '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                            end_date = item['end']
                if start_date and end_date:
                    date_query = Q(slot_date__lte=start_date, slot_date__gte=end_date)
                else:
                    date_query = Q()

                slot_index = find_index_from_array(input_values['filter'], 'display', 'Delivery Slot')
                slot_filter_start_array = []
                slot_filter_end_array = []
                for item in input_values['filter'][slot_index]['data']:
                    if item['is_applied']:
                        slot_filter_start_array.append(item['slot_start_time'])
                        slot_filter_end_array.append(item['slot_end_time'])
                if len(slot_filter_start_array):
                    slot_query = Q(slot_id__slot_start_time__in=slot_filter_start_array,
                                   slot_id__slot_end_time__in=slot_filter_end_array, )
                else:
                    slot_query = Q()
                resp = list(
                    PurchaseDetails.objects.filter(
                        slot_date__lt=today,
                        slot__store_code=user_info['user_details']['storecode']).filter(
                        status_query & slot_query & date_query).exclude(
                        status__in=['added', 'items_delivered', 'cancelled']).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at', 'is_sudo_order').order_by(
                        '-slot__slot_start_time',
                        '-order_created_at'))
                for obj in resp:
                    obj['status'] = status_display(obj['status'])
                #     date_index = find_index_from_array(resp, 'slot_date', obj['slot_date'])
                #     if date_index >= 0:
                #         res_index = self.find(resp[date_index]['slot'], 'slot__slot_start_time',
                #                               'slot__slot_end_time',
                #                               obj['slot__slot_start_time'], obj['slot__slot_end_time'], )
                #         if res_index >= 0:
                #             resp[date_index]['slot'][res_index]['orders'].append(obj)
                #         else:
                #             resp[date_index]['slot'].append({
                #                 'slot__slot_start_time': str(obj['slot__slot_start_time']),
                #                 'slot__slot_end_time': str(obj['slot__slot_end_time']),
                #                 'orders': [obj]
                #             })
                #     else:
                #         resp.append({
                #             'slot_date': str(obj['slot_date']),
                #             'slot': [{
                #                 'slot__slot_start_time': str(obj['slot__slot_start_time']),
                #                 'slot__slot_end_time': str(obj['slot__slot_end_time']),
                #                 'orders': [obj]
                #             }]
                #         })
            elif type == 'up_coming':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = [status_filter()]
                    input_values['filter'].append(future_date_filter())
                    input_values['filter'].append(slot_filter(user_info['user_details']['storecode']))
                status_filter_array = []
                status_index = find_index_from_array(input_values['filter'], 'display', 'Status')
                for item in input_values['filter'][status_index]['data']:
                    if item['is_applied']:
                        status_filter_array.append(item['key'])
                if len(status_filter_array):
                    status_query = Q(status__in=status_filter_array)
                else:
                    status_query = Q()
                date_index = find_index_from_array(input_values['filter'], 'display', 'Date')
                start_date = ''
                end_date = ''
                for item in input_values['filter'][date_index]['data']:
                    if item['is_applied']:
                        if not start_date:
                            start_date = item['start']
                        elif datetime.strptime(item['start'], '%Y-%m-%d') < datetime.strptime(start_date,
                                                                                              '%Y-%m-%d'):
                            start_date = item['start']
                        if not end_date:
                            end_date = item['end']
                        elif datetime.strptime(item['end'], '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                            end_date = item['end']
                if start_date and end_date:
                    date_query = Q(slot_date__gte=start_date, slot_date__lte=end_date)
                else:
                    date_query = Q()
                slot_index = find_index_from_array(input_values['filter'], 'display', 'Delivery Slot')
                slot_filter_start_array = []
                slot_filter_end_array = []
                for item in input_values['filter'][slot_index]['data']:
                    if item['is_applied']:
                        slot_filter_start_array.append(item['slot_start_time'])
                        slot_filter_end_array.append(item['slot_end_time'])
                if len(slot_filter_start_array):
                    slot_query = Q(slot_id__slot_start_time__in=slot_filter_start_array,
                                   slot_id__slot_end_time__in=slot_filter_end_array, )
                else:
                    slot_query = Q()
                data_list = list(
                    PurchaseDetails.objects.filter(slot_date__gt=today,
                                                   store_code=user_info['user_details']['storecode']).filter(
                        status_query & slot_query & date_query).exclude(status__in=['added']).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at', 'is_sudo_order').order_by(
                        '-slot__slot_start_time',
                        '-order_created_at'))
                for obj in data_list:
                    obj['status'] = status_display(obj['status'])
                    date_index = find_index_from_array(resp, 'slot_date', obj['slot_date'])
                    if date_index >= 0:
                        res_index = self.find(resp[date_index]['slot'], 'slot__slot_start_time',
                                              'slot__slot_end_time',
                                              obj['slot__slot_start_time'], obj['slot__slot_end_time'], )
                        if res_index >= 0:
                            resp[date_index]['slot'][res_index]['orders'].append(obj)
                        else:
                            resp[date_index]['slot'].append({
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            })
                    else:
                        resp.append({
                            'slot_date': str(obj['slot_date']),
                            'slot': [{
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            }]
                        })
            elif type == 'whatsapp':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = [status_filter()]
                    input_values['filter'].append(date_filter())
                    input_values['filter'].append(slot_filter(user_info['user_details']['storecode']))
                status_filter_array = []
                status_index = find_index_from_array(input_values['filter'], 'display', 'Status')
                for item in input_values['filter'][status_index]['data']:
                    if item['is_applied']:
                        status_filter_array.append(item['key'])
                if len(status_filter_array):
                    status_query = Q(status__in=status_filter_array)
                else:
                    status_query = Q()
                date_index = find_index_from_array(input_values['filter'], 'display', 'Date')
                start_date = ''
                end_date = ''
                for item in input_values['filter'][date_index]['data']:
                    if item['is_applied']:
                        if not start_date:
                            start_date = item['start']
                        elif datetime.strptime(item['start'], '%Y-%m-%d') < datetime.strptime(start_date,
                                                                                              '%Y-%m-%d'):
                            start_date = item['start']
                        if not end_date:
                            end_date = item['end']
                        elif datetime.strptime(item['end'], '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                            end_date = item['end']
                if start_date and end_date:
                    date_query = Q(slot_date__gte=start_date, slot_date__lte=end_date)
                else:
                    date_query = Q()
                slot_index = find_index_from_array(input_values['filter'], 'display', 'Delivery Slot')
                slot_filter_start_array = []
                slot_filter_end_array = []
                for item in input_values['filter'][slot_index]['data']:
                    if item['is_applied']:
                        slot_filter_start_array.append(item['slot_start_time'])
                        slot_filter_end_array.append(item['slot_end_time'])
                if len(slot_filter_start_array):
                    slot_query = Q(slot_id__slot_start_time__in=slot_filter_start_array,
                                   slot_id__slot_end_time__in=slot_filter_end_array, )
                else:
                    slot_query = Q()
                data_list = list(
                    PurchaseDetails.objects.filter(is_sudo_order=True,
                                                   store_code=user_info['user_details']['storecode']).filter(
                        status_query & slot_query & date_query).exclude(status__in=['added']).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at', 'is_sudo_order').order_by(
                        '-slot__slot_start_time',
                        '-order_created_at'))
                for obj in data_list:
                    obj['status'] = status_display(obj['status'])
                    date_index = find_index_from_array(resp, 'slot_date', obj['slot_date'])
                    if date_index >= 0:
                        res_index = self.find(resp[date_index]['slot'], 'slot__slot_start_time',
                                              'slot__slot_end_time',
                                              obj['slot__slot_start_time'], obj['slot__slot_end_time'], )
                        if res_index >= 0:
                            resp[date_index]['slot'][res_index]['orders'].append(obj)
                        else:
                            resp[date_index]['slot'].append({
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            })
                    else:
                        resp.append({
                            'slot_date': str(obj['slot_date']),
                            'slot': [{
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            }]
                        })
            elif type == 'pending_orders':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = []
                data_list = list(PurchaseDetails.objects.filter(slot_date=today,
                                                                store_code=user_info['user_details'][
                                                                    'storecode'], status='order placed').values(
                    '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile', 'slot_date',
                    'slot__slot_start_time', 'slot__slot_end_time', 'divum_order_id', 'order_created_at',
                    'is_sudo_order').order_by(
                    '-slot__slot_start_time', '-order_created_at'))
                for obj in data_list:
                    res_index = self.find(resp, 'slot__slot_start_time', 'slot__slot_end_time',
                                          obj['slot__slot_start_time'], obj['slot__slot_end_time'])
                    obj['status'] = status_display(obj['status'])
                    if res_index >= 0:
                        resp[res_index]['orders'].append(obj)
                    else:
                        resp.append({
                            'slot__slot_start_time': str(obj['slot__slot_start_time']),
                            'slot__slot_end_time': str(obj['slot__slot_end_time']),
                            'orders': [obj]
                        })
            elif type == 'inprogress_orders':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = []
                data_list = list(PurchaseDetails.objects.filter(
                    slot_date=today, store_code=user_info['user_details']['storecode'],
                    status__in=['picking_done', 'billing_done', 'payment_done']).values(
                    '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile', 'slot_date',
                    'slot__slot_start_time', 'slot__slot_end_time', 'divum_order_id', 'order_created_at',
                    'is_sudo_order').order_by(
                    '-slot__slot_start_time', '-order_created_at'))
                for obj in data_list:
                    res_index = self.find(resp, 'slot__slot_start_time', 'slot__slot_end_time',
                                          obj['slot__slot_start_time'], obj['slot__slot_end_time'])
                    obj['status'] = status_display(obj['status'])
                    if res_index >= 0:
                        resp[res_index]['orders'].append(obj)
                    else:
                        resp.append({
                            'slot__slot_start_time': str(obj['slot__slot_start_time']),
                            'slot__slot_end_time': str(obj['slot__slot_end_time']),
                            'orders': [obj]
                        })
            elif type == 'completed_orders':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = []
                data_list = list(PurchaseDetails.objects.filter(
                    slot_date=today, store_code=user_info['user_details']['storecode'],
                    status__in=['items_delivered']).values(
                    '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile', 'slot_date',
                    'slot__slot_start_time', 'slot__slot_end_time', 'divum_order_id', 'order_created_at',
                    'is_sudo_order').order_by(
                    '-slot__slot_start_time', '-order_created_at'))
                for obj in data_list:
                    res_index = self.find(resp, 'slot__slot_start_time', 'slot__slot_end_time',
                                          obj['slot__slot_start_time'], obj['slot__slot_end_time'])
                    obj['status'] = status_display(obj['status'])
                    if res_index >= 0:
                        resp[res_index]['orders'].append(obj)
                    else:
                        resp.append({
                            'slot__slot_start_time': str(obj['slot__slot_start_time']),
                            'slot__slot_end_time': str(obj['slot__slot_end_time']),
                            'orders': [obj]
                        })
            elif type == 'cancelled_orders':
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = []
                data_list = list(PurchaseDetails.objects.filter(
                    slot_date=today, store_code=user_info['user_details']['storecode'],
                    status__in=['cancelled']).values(
                    '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile', 'slot_date',
                    'slot__slot_start_time', 'slot__slot_end_time', 'divum_order_id', 'order_created_at',
                    'is_sudo_order').order_by(
                    '-slot__slot_start_time', '-order_created_at'))
                for obj in data_list:
                    res_index = self.find(resp, 'slot__slot_start_time', 'slot__slot_end_time',
                                          obj['slot__slot_start_time'], obj['slot__slot_end_time'])
                    obj['status'] = status_display(obj['status'])
                    if res_index >= 0:
                        resp[res_index]['orders'].append(obj)
                    else:
                        resp.append({
                            'slot__slot_start_time': str(obj['slot__slot_start_time']),
                            'slot__slot_end_time': str(obj['slot__slot_end_time']),
                            'orders': [obj]
                        })
            else:
                if not ('filter' in input_values and len(input_values['filter'])):
                    is_filter_applied = False
                    input_values['filter'] = [status_filter()]
                    input_values['filter'].append(past_date_filter())
                    input_values['filter'].append(slot_filter(user_info['user_details']['storecode']))
                status_filter_array = []
                status_index = find_index_from_array(input_values['filter'], 'display', 'Status')
                for item in input_values['filter'][status_index]['data']:
                    if item['is_applied']:
                        status_filter_array.append(item['key'])
                if len(status_filter_array):
                    status_query = Q(status__in=status_filter_array)
                else:
                    status_query = Q()

                date_index = find_index_from_array(input_values['filter'], 'display', 'Date')
                start_date = ''
                end_date = ''
                for item in input_values['filter'][date_index]['data']:
                    if item['is_applied']:
                        if not start_date:
                            start_date = item['start']
                        elif datetime.strptime(item['start'], '%Y-%m-%d') < datetime.strptime(start_date,
                                                                                              '%Y-%m-%d'):
                            start_date = item['start']
                        if not end_date:
                            end_date = item['end']
                        elif datetime.strptime(item['end'], '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                            end_date = item['end']
                if start_date and end_date:
                    date_query = Q(slot_date__lte=start_date, slot_date__gte=end_date)
                else:
                    date_query = Q()

                slot_index = find_index_from_array(input_values['filter'], 'display', 'Delivery Slot')
                slot_filter_start_array = []
                slot_filter_end_array = []
                for item in input_values['filter'][slot_index]['data']:
                    if item['is_applied']:
                        slot_filter_start_array.append(item['slot_start_time'])
                        slot_filter_end_array.append(item['slot_end_time'])
                if len(slot_filter_start_array):
                    slot_query = Q(slot_id__slot_start_time__in=slot_filter_start_array,
                                   slot_id__slot_end_time__in=slot_filter_end_array, )
                else:
                    slot_query = Q()
                data_list = list(
                    PurchaseDetails.objects.filter(slot_date__lt=today,
                                                   slot__store_code=user_info['user_details']['storecode']).exclude(
                        status__in=['added']).filter(status_query & slot_query & date_query).values(
                        '_id', 'order_id', 'created_at', 'paid_amount', 'status', 'user_id__mobile',
                        'slot__slot_start_time', 'slot_date',
                        'slot__slot_end_time', 'divum_order_id', 'order_created_at', 'is_sudo_order').order_by(
                        '-slot_date', '-slot__slot_start_time',
                        '-order_created_at'))
                for obj in data_list:
                    obj['status'] = status_display(obj['status'])
                    date_index = find_index_from_array(resp, 'slot_date', obj['slot_date'])
                    if date_index >= 0:
                        res_index = self.find(resp[date_index]['slot'], 'slot__slot_start_time',
                                              'slot__slot_end_time',
                                              obj['slot__slot_start_time'], obj['slot__slot_end_time'], )
                        if res_index >= 0:
                            resp[date_index]['slot'][res_index]['orders'].append(obj)
                        else:
                            resp[date_index]['slot'].append({
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            })
                    else:
                        resp.append({
                            'slot_date': str(obj['slot_date']),
                            'slot': [{
                                'slot__slot_start_time': str(obj['slot__slot_start_time']),
                                'slot__slot_end_time': str(obj['slot__slot_end_time']),
                                'orders': [obj]
                            }]
                        })
            return response('retrive', 'success',
                            {'result': resp, 'filter': input_values['filter'], 'is_filter_applied': is_filter_applied},
                            "Data Fetched successfully")
        except Exception as e:
            print('error', e)
            return response('retrive', 'failure', str(e), "Error while fetching data!!")


class OrderStatusDetailV3(View):
    def get(self, request, purchase_id):
        try:
            status_array = [
                {'status': 'order placed'},
                {'status': 'picking_done'},
                {'status': 'billing_done'},
                {'status': 'payment_done'},
                {'status': 'items_delivered'}
            ]
            res = list(OrderStatus.objects.filter(purchase_detail_id=purchase_id).annotate(
                divum_order_id=F('purchase_detail_id__divum_order___id'), purchase_id=F('purchase_detail_id___id'),
                is_sudo_order=F('purchase_detail_id__is_sudo_order'), item_count=F('purchase_detail_id__item_count'),
                bill_image_url=F('purchase_detail_id__image_url'),
            ).values(
                '_id', 'status', 'created_at', 'purchase_detail_id__delivery_address_id__address_1',
                'purchase_detail_id__delivery_address_id__address_2',
                'purchase_detail_id__delivery_address_id__state_code',
                'purchase_detail_id__delivery_address_id__name', 'purchase_detail_id__delivery_address_id__mobile',
                'purchase_detail_id__mode_of_payment', 'purchase_detail_id__order_id',
                'divum_order_id', 'purchase_detail_id__paid_amount', 'purchase_detail_id__pos_upi_payment_type',
                'purchase_detail_id__pos_upi_payment_mode', 'purchase_detail_id__pos_upi_mobile_number',
                'purchase_id', 'purchase_detail_id__user_id___id', 'is_sudo_order', 'bill_image_url',
                'item_count').order_by(
                'created_at'))
            result = []
            can_update = True
            for item in status_array:
                index = find_index_from_array(res, 'status', item['status'])
                if index >= 0:
                    res[index]['is_updated'] = True
                    res[index]['can_update'] = False
                    res[index]['status'] = status_display(res[index]['status'])
                    result.append(res[index])
                else:
                    result.append({
                        'purchase_detail_id__delivery_address_id__address_1': res[0][
                            'purchase_detail_id__delivery_address_id__address_1'],
                        'purchase_detail_id__delivery_address_id__address_2': res[0][
                            'purchase_detail_id__delivery_address_id__address_2'],
                        'purchase_detail_id__delivery_address_id__state_code': res[0][
                            'purchase_detail_id__delivery_address_id__state_code'],
                        'purchase_detail_id__delivery_address_id__name': res[0][
                            'purchase_detail_id__delivery_address_id__name'],
                        'purchase_detail_id__delivery_address_id__mobile': res[0][
                            'purchase_detail_id__delivery_address_id__mobile'],
                        'purchase_detail_id__mode_of_payment': res[0]['purchase_detail_id__mode_of_payment'],
                        'purchase_detail_id__order_id': res[0]['purchase_detail_id__order_id'],
                        'divum_order_id': res[0]['divum_order_id'],
                        'purchase_detail_id__paid_amount': res[0]['purchase_detail_id__paid_amount'],
                        'purchase_detail_id__pos_upi_payment_type': res[0][
                            'purchase_detail_id__pos_upi_payment_type'],
                        'purchase_detail_id__pos_upi_payment_mode': res[0][
                            'purchase_detail_id__pos_upi_payment_mode'],
                        'purchase_detail_id__pos_upi_mobile_number': res[0][
                            'purchase_detail_id__pos_upi_mobile_number'],
                        'purchase_id': res[0]['purchase_id'],
                        'is_sudo_order': res[0]['is_sudo_order'],
                        'item_count': res[0]['item_count'],
                        'bill_image_url': res[0]['bill_image_url'],
                        'created_at': None,
                        '_id': None,
                        'is_updated': False,
                        'status': status_display(item['status']),
                        'can_update': can_update
                    })
                    can_update = False

            resp = {
                'data': result,
                'session_id': ''
            }
            try:
                time_threshold = datetime.now() - timedelta(hours=12)
                wa_session = WhatsAppSession.objects.filter(purchase_detail_id=purchase_id).annotate(
                    is_active=Case(When(updated_at__gte=time_threshold, then=Value(True)),
                                   default=Value(False),
                                   output_field=BooleanField())).values('_id', 'is_active')
                OrderStatus.objects.get(~Q(status_updated_on='web'), purchase_detail_id_id=purchase_id)
                if len(wa_session):
                    resp['session_id'] = wa_session[0]['_id']
                    resp['is_active_session'] = wa_session[0]['is_active']
            except:
                pass
            return response('retrive', 'success', resp, "Data Fetched successfully")
        except:
            return response('retrive', 'failure', '', "Error while fetching data!!")


class OrderStatusDetailV2(View):
    def get(self, request, purchase_id):
        try:
            status_array = [
                {'status': 'order placed'},
                {'status': 'cancelled'},
                {'status': 'picking_done'},
                {'status': 'billing_done'},
                {'status': 'payment_done'},
                {'status': 'items_delivered'}
            ]
            res = list(OrderStatus.objects.filter(purchase_detail_id=purchase_id).annotate(
                divum_order_id=F('purchase_detail_id__divum_order___id'), purchase_id=F('purchase_detail_id___id'),
                is_sudo_order=F('purchase_detail_id__is_sudo_order'), item_count=F('purchase_detail_id__item_count'),
                bill_image_url=F('purchase_detail_id__image_url'), cancel_reason=F('purchase_detail_id__cancel_reason')
            ).values(
                '_id', 'status', 'created_at', 'purchase_detail_id__delivery_address_id__address_1',
                'purchase_detail_id__delivery_address_id__address_2',
                'purchase_detail_id__delivery_address_id__state_code',
                'purchase_detail_id__delivery_address_id__name', 'purchase_detail_id__delivery_address_id__mobile',
                'purchase_detail_id__mode_of_payment', 'purchase_detail_id__order_id',
                'divum_order_id', 'purchase_detail_id__paid_amount', 'purchase_detail_id__pos_upi_payment_type',
                'purchase_detail_id__pos_upi_payment_mode', 'purchase_detail_id__pos_upi_mobile_number',
                'purchase_id', 'purchase_detail_id__user_id___id', 'is_sudo_order', 'bill_image_url',
                'item_count', 'cancel_reason').order_by(
                'created_at'))
            result = []
            can_update = True
            for item in status_array:
                index = find_index_from_array(res, 'status', item['status'])
                if index >= 0:
                    res[index]['is_updated'] = True
                    res[index]['can_update'] = False
                    res[index]['status'] = status_display(res[index]['status'])
                    result.append(res[index])
                    if item['status'] == 'cancelled':
                        break
                else:
                    if item['status'] == 'cancelled':
                        continue
                    result.append({
                        'purchase_detail_id__delivery_address_id__address_1': res[0][
                            'purchase_detail_id__delivery_address_id__address_1'],
                        'purchase_detail_id__delivery_address_id__address_2': res[0][
                            'purchase_detail_id__delivery_address_id__address_2'],
                        'purchase_detail_id__delivery_address_id__state_code': res[0][
                            'purchase_detail_id__delivery_address_id__state_code'],
                        'purchase_detail_id__delivery_address_id__name': res[0][
                            'purchase_detail_id__delivery_address_id__name'],
                        'purchase_detail_id__delivery_address_id__mobile': res[0][
                            'purchase_detail_id__delivery_address_id__mobile'],
                        'purchase_detail_id__mode_of_payment': res[0]['purchase_detail_id__mode_of_payment'],
                        'purchase_detail_id__order_id': res[0]['purchase_detail_id__order_id'],
                        'divum_order_id': res[0]['divum_order_id'],
                        'purchase_detail_id__paid_amount': res[0]['purchase_detail_id__paid_amount'],
                        'purchase_detail_id__is_sudo_order': res[0]['is_sudo_order'],
                        'purchase_detail_id__pos_upi_payment_type': res[0][
                            'purchase_detail_id__pos_upi_payment_type'],
                        'purchase_detail_id__pos_upi_payment_mode': res[0][
                            'purchase_detail_id__pos_upi_payment_mode'],
                        'purchase_detail_id__pos_upi_mobile_number': res[0][
                            'purchase_detail_id__pos_upi_mobile_number'],
                        'purchase_id': res[0]['purchase_id'],
                        'is_sudo_order': res[0]['is_sudo_order'],
                        'item_count': res[0]['item_count'],
                        'cancel_reason': res[0]['cancel_reason'],
                        'bill_image_url': res[0]['bill_image_url'],
                        'created_at': None,
                        '_id': None,
                        'is_updated': False,
                        'status': status_display(item['status']),
                        'can_update': can_update
                    })
                    can_update = False

            resp = {
                'data': result,
                'session_id': ''
            }
            try:
                time_threshold = datetime.now() - timedelta(hours=24)
                wa_session = WhatsAppSession.objects.filter(purchase_detail_id=purchase_id).annotate(
                    is_active=Case(When(updated_at__gte=time_threshold, then=Value(True)),
                                   default=Value(False),
                                   output_field=BooleanField())).values('_id', 'is_active')
                OrderStatus.objects.get(~Q(status_updated_on='web'), purchase_detail_id_id=purchase_id,
                                        status='order placed')
                if len(wa_session):
                    resp['session_id'] = wa_session[0]['_id']
                    resp['is_active_session'] = wa_session[0]['is_active']
            except:
                pass
            return response('retrive', 'success', resp, "Data Fetched successfully")
        except:
            return response('retrive', 'failure', '', "Error while fetching data!!")


class OrderStatusDetail(View):
    def get(self, request, purchase_id):
        try:
            status_array = [
                {'status': 'order placed'},
                {'status': 'cancelled'},
                {'status': 'picking_done'},
                {'status': 'billing_done'},
                {'status': 'payment_done'},
                {'status': 'items_delivered'}
            ]
            user_info = user_info_and_user_obj(request)
            res = list(OrderStatus.objects.filter(purchase_detail_id=purchase_id).annotate(
                divum_order_id=F('purchase_detail_id__divum_order___id'), purchase_id=F('purchase_detail_id___id'),
                delivery_charges=F('purchase_detail_id__delivery_charges')
            ).values(
                '_id', 'status', 'created_at', 'purchase_detail_id__delivery_address_id__address_1',
                'purchase_detail_id__delivery_address_id__address_2',
                'purchase_detail_id__delivery_address_id__state_code', 'delivery_charges',
                'purchase_detail_id__delivery_address_id__name', 'purchase_detail_id__delivery_address_id__mobile',
                'purchase_detail_id__mode_of_payment', 'purchase_detail_id__order_id',
                'divum_order_id', 'purchase_detail_id__paid_amount', 'purchase_detail_id__pos_upi_payment_type',
                'purchase_detail_id__pos_upi_payment_mode', 'purchase_detail_id__pos_upi_mobile_number',
                'purchase_id', 'purchase_detail_id__user_id___id', 'purchase_detail_id__user_id__mobile',
                'purchase_detail_id__slot_date', 'purchase_detail_id__slot__slot_start_time',
                'purchase_detail_id__slot__slot_end_time', 'purchase_detail_id__is_sudo_order'
            ).order_by(
                'created_at'))
            result = []
            is_chat = False
            count = WhatsAppSession.objects.filter(user___id=res[0]['purchase_detail_id__user_id___id'],
                                                   sm___id=user_info['user_details']['_id']).count()
            if count > 0:
                is_chat = True
            can_update = True
            for item in status_array:
                index = find_index_from_array(res, 'status', item['status'])
                if index >= 0:
                    res[index]['is_updated'] = True
                    res[index]['can_update'] = False
                    res[index]['is_chat_available'] = is_chat
                    res[index]['status'] = status_display(res[index]['status'])
                    result.append(res[index])
                else:
                    result.append({
                        'purchase_detail_id__delivery_address_id__address_1': res[0][
                            'purchase_detail_id__delivery_address_id__address_1'],
                        'purchase_detail_id__delivery_address_id__address_2': res[0][
                            'purchase_detail_id__delivery_address_id__address_2'],
                        'purchase_detail_id__delivery_address_id__state_code': res[0][
                            'purchase_detail_id__delivery_address_id__state_code'],
                        'purchase_detail_id__delivery_address_id__name': res[0][
                            'purchase_detail_id__delivery_address_id__name'],
                        'purchase_detail_id__delivery_address_id__mobile': res[0][
                            'purchase_detail_id__delivery_address_id__mobile'],
                        'purchase_detail_id__mode_of_payment': res[0]['purchase_detail_id__mode_of_payment'],
                        'purchase_detail_id__order_id': res[0]['purchase_detail_id__order_id'],
                        'divum_order_id': res[0]['divum_order_id'],
                        'purchase_detail_id__paid_amount': res[0]['purchase_detail_id__paid_amount'],
                        'purchase_detail_id__is_sudo_order': res[0]['purchase_detail_id__is_sudo_order'],
                        'purchase_detail_id__pos_upi_payment_type': res[0][
                            'purchase_detail_id__pos_upi_payment_type'],
                        'purchase_detail_id__pos_upi_payment_mode': res[0][
                            'purchase_detail_id__pos_upi_payment_mode'],
                        'purchase_detail_id__pos_upi_mobile_number': res[0][
                            'purchase_detail_id__pos_upi_mobile_number'],
                        'purchase_id': res[0]['purchase_id'],
                        'delivery_charges': res[0]['delivery_charges'],
                        'purchase_detail_id__user_id__mobile': res[0]['purchase_detail_id__user_id__mobile'],
                        'purchase_detail_id__slot_date': res[0]['purchase_detail_id__slot_date'],
                        'purchase_detail_id__slot__slot_start_time': res[0][
                            'purchase_detail_id__slot__slot_start_time'],
                        'purchase_detail_id__slot__slot_end_time': res[0][
                            'purchase_detail_id__slot__slot_end_time'],
                        'created_at': None,
                        '_id': None,
                        'is_updated': False,
                        'status': status_display(item['status']),
                        'can_update': can_update,
                        'is_chat_available': is_chat
                    })
                    can_update = False
            return response('retrive', 'success', result, "Data Fetched successfully")
        except Exception as e:
            print("error", e)
            return response('retrive', 'failure', '', "Error while fetching data!!")


class UpdatePurchaseDetail(View):
    def post(self, request):
        try:
            user_info = user_info_and_user_obj(request)
            input_values = decode_post_request(request)
            PurchaseDetails.objects.filter(_id=input_values['purchase_id']).update(image_url=input_values['image_url'],
                                                                                   item_count=input_values[
                                                                                       'item_count'],
                                                                                   paid_amount=input_values[
                                                                                       'total_amount'])
            return response('update', 'success', "Updated Successfully!!")
        except Exception as e:
            print("Error", e)
            return response('update', 'failure', '', "Failed To Update!!")


class ListCartItems(View):
    def get(self, request, purchase_id):
        try:
            page = int(request.GET.get('page', 1))
            skip = (page - 1) * 100
            limit = page * 100
            product_query_set = list(
                Cart.objects.filter(purchase_detail=purchase_id).annotate(
                    product_listing_images=
                    ArrayAgg(Case(
                        When(Q(product_id__productimage__image_url__icontains='front'),
                             then=F('product_id__productimage__image_url'),
                             ),
                        output_field=CharField()),
                    ),
                    is_f_and_v=Case(When(Q(product_id__productspecification__weight='KG'),
                                         then=Value(True), ), default=Value(False), output_field=BooleanField()),
                    userId=F('user_id'),
                    productId=F('product_id'),
                    numberOfItems=F('item_count'),
                    itemStatus=F('status'),
                    specialPrice=F('special_price'),
                    finalPrice=F('final_price'),
                    purchase_id=F('purchase_detail___id'),
                    images=F('product_listing_images')
                ).values(
                    'userId',
                    'productId',
                    'numberOfItems',
                    'itemStatus',
                    'price',
                    'name',
                    'specialPrice',
                    'discount',
                    'units',
                    'images',
                    'finalPrice',
                    'purchase_id',
                    'is_out_of_stock', 'is_edited', 'is_picked', 'is_f_and_v', 'initial_item_count'
                ).order_by('updated_at'))[skip:limit]
            status_details = PurchaseDetails.objects.get(_id=purchase_id)
            can_edit = False
            if status_details.status == 'order placed' or status_details.status == 'picking_done':
                can_edit = True
            return response('create', 'success', {'list': product_query_set, 'can_edit': can_edit},
                            "Fetched Successfully!!")
        except Exception as e:
            print('error', e)
            return response('create', 'failure', e, "File Not Found")


class ListRefundCartItems(View):
    def get(self, request, purchase_id):
        try:
            page = int(request.GET.get('page', 1))
            skip = (page - 1) * 20
            limit = page * 20
            product_query_set = list(
                RefundCart.objects.filter(purchase_detail=purchase_id).annotate(
                    product_listing_images=
                    ArrayAgg(Case(
                        When(Q(product_id__productimage__image_url__icontains='front'),
                             then=F('product_id__productimage__image_url'),
                             ),
                        output_field=CharField()),
                    ),
                    userId=F('user_id'),
                    productId=F('product_id'),
                    numberOfItems=F('item_count'),
                    itemStatus=F('status'),
                    price=F('product_id__price'),
                    name=F('product_id__productspecification__unique_name'),
                    specialPrice=F('product_id__special_price'),
                    finalPrice=F('product_id__special_price') * F('item_count'),
                    discount=F('product_id__discount'),
                    units=F('product_id__productspecification__units'),
                    images=F('product_listing_images')
                ).values(
                    'userId',
                    'productId',
                    'numberOfItems',
                    'itemStatus',
                    'price',
                    'name',
                    'specialPrice',
                    'discount',
                    'units',
                    'images',
                    'finalPrice'
                ).order_by('updated_at'))[skip:limit]
            return response('create', 'success', product_query_set, "Fetched Successfully!!")
        except Exception as e:
            print('error', e)
            return response('create', 'failure', e, "File Not Found")


class DeleteCartItem(View):
    def delete(self, request, product_id, purchase_id):
        try:
            cart_details = Cart.objects.get(product_id___id=product_id, purchase_detail___id=purchase_id)
            PurchaseDetails.objects.filter(_id=purchase_id).update(
                paid_amount=F('paid_amount') - cart_details.final_price
                , mrp=F('mrp') - (cart_details.price * cart_details.item_count),
                discount=F('discount') - (cart_details.discount * cart_details.item_count))
            Cart.objects.filter(product_id___id=product_id, purchase_detail___id=purchase_id).update(
                is_out_of_stock=True, item_count=0.0, final_price=0.0, status='out_of_stock')
            return response('delete', 'success', "Deleted Successfully!!")
        except Exception as e:
            return response('delete', 'failure', e, "Failed To delete!!")


class UpdateCart(View):
    def put(self, request):
        try:
            input_values = decode_post_request(request)
            form = UpdateCartPayload(input_values, False)
            if not form.is_valid():
                return response("update", "failed", form.errors)
            edited_user = 'user_name' in input_values and input_values['user_name'] or ""
            item_unit_value = 1
            cart_details_before = Cart.objects.get(product_id___id=input_values['product_id'],
                                                   purchase_detail___id=input_values['purchase_id'])
            try:
                product_det = ProductDetail.objects.get(_id=input_values['product_id'])
                item_unit_value = product_det.item_unit_value
            except:
                pass
            Cart.objects.filter(product_id___id=input_values['product_id'],
                                purchase_detail___id=input_values['purchase_id']).update(
                item_count=float(input_values['count']),
                item_count_value=float(input_values['count']) * float(item_unit_value),
                is_edited=True, price=input_values['price'],
                final_price=float(input_values['count'] * float(cart_details_before.special_price)),
                edited_user=edited_user
            )
            cart_details_after = Cart.objects.get(product_id___id=input_values['product_id'],
                                                  purchase_detail___id=input_values['purchase_id'])
            final_price = cart_details_after.final_price - cart_details_before.final_price
            mrp = (cart_details_after.item_count * cart_details_after.price) - (
                    cart_details_before.item_count * cart_details_before.price)
            PurchaseDetails.objects.filter(_id=input_values['purchase_id']).update(
                paid_amount=F('paid_amount') + final_price,
                mrp=F('mrp') + mrp)
            return response('update', 'success', "Updated Successfully!!")
        except Exception as e:
            return response('update', 'failure', {'data': str(e)}, "Failed To Update!!")


class UpdateCartV2(View):
    def put(self, request):
        try:
            input_values = decode_post_request(request)
            form = UpdateCartPayload(input_values, False)
            if not form.is_valid():
                return response("update", "failed", form.errors)
            edited_user = 'user_name' in input_values and input_values['user_name'] or ""
            cart_details_before = Cart.objects.get(product_id___id=input_values['product_id'],
                                                   purchase_detail___id=input_values['purchase_id'])
            item_unit_value = 1
            if cart_details_before.product_id:
                try:
                    product_det = ProductDetail.objects.get(_id=cart_details_before.product_id_id)
                    item_unit_value = product_det.item_unit_value
                except:
                    pass
            # if cart_details_before.item_count != input_values['count']:
            Cart.objects.filter(product_id___id=input_values['product_id'],
                                purchase_detail___id=input_values['purchase_id']).update(
                item_count=input_values['count'],
                item_count_value=float(input_values['count']) * float(item_unit_value),
                is_edited=True, special_price=input_values['special_price'],
                discount=((float(cart_details_before.price) - input_values[
                    'special_price']) * 100 / float(cart_details_before.price)),
                final_price=input_values['special_price'] * input_values['count'],
                edited_user=edited_user
            )
            cart_details_after = Cart.objects.get(product_id___id=input_values['product_id'],
                                                  purchase_detail___id=input_values['purchase_id'])
            final_price = cart_details_after.final_price - cart_details_before.final_price
            mrp = (cart_details_after.item_count * cart_details_after.price) - (
                    cart_details_before.item_count * cart_details_before.price)
            # discount = cart_details_after.final_price - cart_details_before.final_price
            # if cart_details_before.item_count > cart_details_after.item_count:
            PurchaseDetails.objects.filter(_id=input_values['purchase_id']).update(
                paid_amount=F('paid_amount') + final_price,
                mrp=F('mrp') + mrp,
                discount=F('mrp') - F('paid_amount'))
            # elif cart_details_before.item_count < cart_details_after.item_count:
            #     PurchaseDetails.objects.filter(_id=input_values['purchase_id']).update(
            #         paid_amount=F('paid_amount') + final_price,
            #         mrp=F('mrp') + mrp,
            #         discount=F('discount') + discount)
            return response('update', 'success', "Updated Successfully!!")
            # else:
            #     return response('update', 'success', "Updated Successfully!!")
        except Exception as e:
            return response('update', 'failure', {'data': str(e)}, "Failed To Update!!")


class UpdatePurchaseDetail(View):
    def post(self, request):
        try:
            user_info = user_info_and_user_obj(request)
            input_values = decode_post_request(request)
            form = UpdatePurchaseDetailsPayload(input_values, False)
            if not form.is_valid():
                return response("create", "failed", form.errors)
            PurchaseDetails.objects.filter(_id=input_values['purchase_id'], is_sudo_order=True).update(
                image_url='image_url' in input_values['image_url'] and input_values['image_url'] or "",
                order_id='order_id' in input_values['order_id'] and input_values['order_id'] or "",
                paid_amount=input_values['total_amount'],
                item_count=input_values['item_count'])
            return response('update', 'success', "Updated Successfully!!")
        except Exception as e:
            print("Error", e)
            return response('update', 'failure', '', "Failed To Update!!")


class Homepage(View):
    def get(self, request, store_code):
        try:
            user_info = user_info_and_user_obj(request)
            print("!!", user_info['user_details'])
            final_resp = {}
            final_resp['manager'] = []
            final_resp['csa_activity'] = []
            final_resp['cashier'] = []
            final_resp['picker'] = []
            users = []
            if user_info['user_details']['designation'].lower() == "dm" or user_info['user_details'][
                'designation'].lower() == "store manager":
                users = UserOnboarding.objects.filter(storecode=user_info['user_details']['storecode'],
                                                      deleted_at=None).values()
            elif user_info['user_details']['designation'].lower() == "csa":
                users = UserOnboarding.objects.filter(designation="csa",
                                                      storecode=user_info['user_details']['storecode'],
                                                      deleted_at=None).values()
            elif user_info['user_details']['designation'].lower() == "cashier":
                users = UserOnboarding.objects.filter(designation="cashier",
                                                      storecode=user_info['user_details']['storecode'],
                                                      deleted_at=None).values()
            for single_user in users:
                store_user_details = {}
                store_user_details['_id'] = single_user['_id']
                store_user_details['name'] = single_user['firstname'] + " " + single_user['lastname']
                store_user_details['designation'] = single_user['designation']
                store_user_details['email'] = single_user['email']
                store_user_details['employeeid'] = single_user['employeeid']
                store_user_details['poornataid'] = single_user['poornataid']
                store_user_details['shift_start_time'] = single_user['shift_start_time']
                store_user_details['shift_end_time'] = single_user['shift_end_time']
                store_user_details['image_url'] = single_user['image_url']
                if single_user['designation'].lower() == "dm" or single_user['designation'].lower() == "store manager":
                    final_resp['manager'].append(store_user_details)
                elif single_user['designation'].lower() == "csa":
                    activity = list(
                        Activity.objects.filter(email=single_user['email'], deleted_at=None).values().order_by(
                            '-updated_at'))
                    store_user_details['activity'] = activity
                    final_resp['csa_activity'].append(store_user_details)
                elif single_user['designation'].lower() == "cashier":
                    activity = list(
                        Activity.objects.filter(email=single_user['email'], deleted_at=None).values().order_by(
                            '-updated_at'))
                    store_user_details['activity'] = activity
                    final_resp['cashier'].append(store_user_details)

                picker_list = Picker.objects.filter(store_code=user_info['user_details']['storecode'],
                                                    deleted_at=None).values()
                for picker in picker_list:
                    picker['date'] = picker['date'].strftime("%d-%b-%Y")
                    final_resp['picker'].append(picker)

            return response('retrive', 'success', final_resp, "Successfully Retrived")
        except Exception as e:
            return response('retrive', 'failure', {'data': str(e)}, "Failed To retrive!!")


class UserCreate(View):
    def post(self, request):
        try:
            input_values = decode_post_request(request)
            UserOnboarding(storecode=input_values['store_code'], firstname=input_values['first_name'],
                           lastname=input_values['last_name'], email=input_values['email'],
                           designation=input_values['designation'],
                           employeeid=input_values['employeeid'], poornataid=input_values['poornataid'],
                           image_url=input_values['image_url'], shift_start_time=input_values['shift_start_time'],
                           shift_end_time=input_values['shift_end_time']).save()
            return response('create', 'success', {}, "Created!!")
        except Exception as e:
            return response('create', 'fail', str(e), "Not Created!!")


class ActivityApi(View):
    def post(self, request):
        try:
            file = request.FILES['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            first_row = 0
            for row in reader:
                if first_row == 0:
                    first_row = 1
                else:
                    Activity(name=row[0], timings=row[1], time=row[6], start_time=row[2], end_time=row[3],
                             status=row[4], email=row[5], date=datetime.strptime(row[7], "%d-%m-%Y")).save()
            return response('create', 'success', {}, "Created!!")
        except Exception as e:
            return response('create', 'fail', str(e), "Not Created!!")

    def get(self, request, email):
        try:
            final_resp = {}
            inprogress = []
            upcoming = []
            completed = []
            activityList = Activity.objects.filter(email=email, deleted_at=None).values()
            for activity in activityList:
                if activity['status'].lower() == "inprogress":
                    inprogress.append(activity)
                elif activity['status'].lower() == "upcoming":
                    upcoming.append(activity)
                elif activity['status'].lower() == "completed":
                    completed.append(activity)
            final_resp['inprogress'] = inprogress
            final_resp['upcoming'] = upcoming
            final_resp['completed'] = completed
            return response('retrive', 'success', final_resp, "Retrived!!")
        except Exception as e:
            return response('retrive', 'fail', str(e), "Not Retrived!!")

    def put(self, request):
        try:
            input_values = decode_post_request(request)
            Activity.objects.filter(_id=input_values['_id']).update(name=input_values['name'],
                                                                    time=input_values["timings"])
            return response('update', 'success', {}, "Updated!!")
        except Exception as e:
            return response('update', 'fail', str(e), "Not Updated!!")


class ActivityApiList(View):

    def get(self, request, store_code):
        try:
            final_resp = []
            userlist = UserOnboarding.objects.filter(storecode=store_code, deleted_at=None).values()
            for user in userlist:
                activity_list = Activity.objects.filter(email=user['email'], deleted_at=None).values()
                for activity in activity_list:
                    if activity['name'] not in final_resp:
                        final_resp.append(activity['name'])
            return response('retrive', 'success', final_resp, "Retrived!!")
        except Exception as e:
            return response('retrive', 'fail', str(e), "Not Retrived!!")


class PickerForecasting(View):
    def post(self, request):
        try:
            file = request.FILES['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            first_row = 0
            for row in reader:
                if first_row == 0:
                    first_row = 1
                else:
                    row[0] = row[0] + " 12:00:00"
                    date_time_obj = datetime.strptime(row[0], '%d-%m-%Y %H:%M:%S')
                    Picker(date=date_time_obj, sop_units=row[1], capacity_units=row[2], percentage=row[3],
                           store_code=row[4]).save()
            return response('create', 'success', {}, "Created!!")
        except Exception as e:
            return response('create', 'fail', str(e), "Not Created!!")

    def get(self, request):
        try:
            final_resp = []
            filter_year = request.GET.get('filter_year')
            filter_month = request.GET.get('filter_month')
            filter_week = request.GET.get('filter_week', None)
            picker_filter = list(
                Picker.objects.filter(date__year=int(filter_year), date__month=int(filter_month)).values())
            for picker in picker_filter:
                if filter_week != None:
                    if int(picker['date'].weekday()) == int(filter_week):
                        picker['date'] = picker['date'].strftime("%d-%b-%Y")
                        final_resp.append(picker)
                else:
                    picker['date'] = picker['date'].strftime("%d-%b-%Y")
                    final_resp.append(picker)

            return response('retrive', 'success', final_resp, "Retrived!!")
        except Exception as e:
            return response('retrive', 'fail', str(e), "Not Retrived!!")


class Cashier(View):
    def get(self, request):
        try:
            final_resp = []
            filter_year = request.GET.get('filter_year')
            filter_month = request.GET.get('filter_month')
            filter_week = request.GET.get('filter_week', None)
            picker_filter = list(
                Activity.objects.filter(date__year=int(filter_year), date__month=int(filter_month)).values())
            for picker in picker_filter:
                if filter_week != None:
                    if int(picker['date'].weekday()) == int(filter_week):
                        picker['date'] = picker['date'].strftime("%d-%b-%Y")
                        final_resp.append(picker)
                else:
                    picker['date'] = picker['date'].strftime("%d-%b-%Y")
                    final_resp.append(picker)

            return response('retrive', 'success', final_resp, "Retrived!!")
        except Exception as e:
            return response('retrive', 'fail', str(e), "Not Retrived!!")


class PauseorResume(View):

    def put(self, request, activity_id):
        try:
            final_resp = []
            activity = Activity.objects.filter(_id=activity_id, deleted_at=None).values()
            if activity[0]['time'] == "pause":
                Activity.objects.filter(_id=activity_id, deleted_at=None).update(time=datetime.now())
            else:
                Activity.objects.filter(_id=activity_id, deleted_at=None).update(time="pause")
            return response('update', 'success', {}, "Updated!!")
        except Exception as e:
            return response('retrive', 'fail', str(e), "Not Retrived!!")


class OrderSummary(View):
    def get(self, request):
        try:
            user_info = user_info_and_user_obj(request)
            current_date = datetime.now() + timedelta(hours=5, minutes=30)
            today = current_date.today()
            data = list(PurchaseDetails.objects.filter(
                slot_date=today, store_code=user_info['user_details']['storecode']).exclude(
                status__in=['added']).values('store_code').annotate(
                total_orders=Sum(Case(When(~Q(_id=None), then=1), output_field=IntegerField())),
                pending_orders=Sum(
                    Case(When(status='order placed', then=1), output_field=IntegerField())),
                inprogress_orders=Sum(
                    Case(When(status__in=['picking_done', 'billing_done', 'payment_done'], then=1),
                         output_field=IntegerField())),
                completed_orders=Sum(
                    Case(When(status='items_delivered', then=1), output_field=IntegerField())),
                cancelled_orders=Sum(
                    Case(When(status='cancelled', then=1), output_field=IntegerField())),
            ).values('total_orders', 'pending_orders', 'inprogress_orders', 'completed_orders',
                     'cancelled_orders'))
            return response('retrieve', 'success', {'data': data}, "Updated Successfully!!")
        except Exception as e:
            return response('retrieve', 'failure', str(e), "Failed To Fetch!!")
