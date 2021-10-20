from django.conf.urls import url
from orders.order_details import CurrentOrders, OrderStatusDetail, ListCartItems, ListRefundCartItems, DeleteCartItem, \
    UpdateCart, OrderStatusDetailV2, UpdateCartV2, OrderStatusDetailV3, UpdatePurchaseDetail, Homepage, ActivityApi, \
    UserCreate, PauseorResume, ActivityApiList, PickerForecasting, Cashier, OrderSummary
from orders.views import UpdateStatus, PickItem, PriceActionChange, InitiateRefund, InitiateNewTransaction
from orders.search import Search
from orders.cancel_order import CancelOrder, CancelOrderReasonList

urlpatterns = [
    url(r'^orders/(?P<type>.*)$', CurrentOrders.as_view(), name="Orders List"),
    url(r'^update_purchase_details$', UpdatePurchaseDetail.as_view(), name="Update Purchase Details"),
    url(r'^order_status/(?P<purchase_id>.*)$', OrderStatusDetail.as_view(), name="Order Details"),
    url(r'^order_status_v2/(?P<purchase_id>.*)$', OrderStatusDetailV2.as_view(), name="Order Details"),
    url(r'^order_status_v3/(?P<purchase_id>.*)$', OrderStatusDetailV3.as_view(), name="Order Details"),
    url(r'^items_list/(?P<purchase_id>.*)$', ListCartItems.as_view(), name="Items List"),
    url(r'^refund_items_list/(?P<purchase_id>.*)$', ListRefundCartItems.as_view(),
        name="Refund Items List"),
    url(r'^delete_item/(?P<product_id>.*)/(?P<purchase_id>.*)$', DeleteCartItem.as_view(),
        name="Delete Cart Item"),
    url(r'^pick_item', PickItem.as_view(), name="Pick Item"),
    url(r'^update_cart$', UpdateCart.as_view(), name="Update Cart Item"),
    url(r'^update_cart_v2$', UpdateCartV2.as_view(), name="Update Cart Item with price changes"),
    url(r'^update_status$', UpdateStatus.as_view(), name="Update Order Status"),
    url(r'^search/(?P<order_id>.*)$', Search.as_view(), name="Search Order"),
    url(r'^update_purchase_details$', UpdatePurchaseDetail.as_view(), name="Update Purchase Details"),
    url(r'^cancel_order_reasons$', CancelOrderReasonList.as_view(), name="Cancel Order Reasons"),
    url(r'^cancel_order$', CancelOrder.as_view(), name="Cancel Order"),
    url(r'^homepage/(?P<store_code>.*)', Homepage.as_view(), name="Homepage"),
    url(r'^activity$', ActivityApi.as_view(), name="Activity"),
    url(r'^activity_list/(?P<email>.*)$', ActivityApi.as_view(), name="Activities of Particular user"),
    url(r'^activity_list_store/(?P<store_code>.*)$', ActivityApiList.as_view(), name="Activities of store"),
    url(r'^create_user$', UserCreate.as_view(), name="UserCreate"),
    url(r'^item_action_change/(?P<purchase_id>.*)$', PriceActionChange.as_view(),
        name="Check whether refund/new Txn to initiate."),
    url(r'^refund_initiate/(?P<purchase_id>.*)$', InitiateRefund.as_view(), name="initiate refund."),
    url(r'^picker', PickerForecasting.as_view(), name="picker forecsting"),
    url(r'^cashier', Cashier.as_view(), name="Cashier"),
    url(r'^pause/(?P<activity_id>.*)$', PauseorResume.as_view(), name="pause"),
    url(r'^new_txn_initiate/(?P<purchase_id>.*)$', InitiateNewTransaction.as_view(), name="initiate refund."),
    url(r'^order_summary$', OrderSummary.as_view(), name="Order Summary"),
]
