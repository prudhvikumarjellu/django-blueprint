from django.contrib.gis.db import models
from authentication.models import UserAddress, User, UserOnboarding
import uuid


# Create your models here.
class StoreCategory(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    store_code = models.BigIntegerField(blank=False, null=False)
    category = models.CharField(max_length=100, blank=False, null=False)  # category for the particular store
    image_url = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    # language_code = models.CharField(max_length=5, default='en')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "store_category"


class StoreSubCategory(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    store_category = models.ForeignKey(StoreCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "store_subcategory"


class ProductDetail(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    store_code = models.BigIntegerField(blank=False, null=False)
    sku = models.BigIntegerField(blank=False, null=False)
    price = models.DecimalField(max_digits=20, decimal_places=10, blank=False, null=False)
    special_price = models.DecimalField(max_digits=20, decimal_places=10, blank=False, null=False)
    discount = models.CharField(max_length=6, blank=False, null=False)
    inventory = models.DecimalField(max_digits=20, decimal_places=10, blank=False, null=False)
    last_updated = models.CharField(max_length=20, blank=False, null=False)
    plano_loc = models.CharField(max_length=20, blank=False, null=False)
    for_you = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    ros = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    item_unit_value = models.DecimalField(max_digits=10, decimal_places=5, default=1.0)

    class Meta:
        db_table = "product_detail"


class ProductSpecification(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(ProductDetail, on_delete=models.CASCADE, verbose_name='product_specification')
    unique_name = models.CharField(max_length=100, blank=False, null=False)
    units = models.CharField(max_length=80, default=None)
    name = models.CharField(max_length=100, blank=False, null=False)
    category = models.ForeignKey(StoreCategory, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(StoreSubCategory, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=False, null=False)
    short_description = models.CharField(max_length=100, blank=False, null=False)
    weight = models.CharField(max_length=10, blank=False, null=False)
    # language_code = models.CharField(max_length=5, default='en')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "product_specification"


class ProductImage(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(ProductDetail, on_delete=models.CASCADE, verbose_name='product_image')
    image_url = models.TextField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "product_image"


class SlotTiming(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    store_code = models.BigIntegerField(blank=False, null=False, db_index=True)
    slot_start_time = models.TimeField(blank=False, null=False)
    slot_end_time = models.TimeField(blank=False, null=False)
    capacity_in_slot = models.IntegerField(default=0)
    week_day = models.IntegerField(default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "slot_timings"


class PurchaseDetailsOrderId(models.Model):
    _id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'purchase_details_order_id'


class PurchaseDetails(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)  #
    delivery_address_id = models.ForeignKey(UserAddress, on_delete=models.CASCADE, blank=True, null=True)  ##
    divum_order = models.ForeignKey(PurchaseDetailsOrderId, on_delete=models.CASCADE, blank=True, null=True,
                                    default=None)  #
    status = models.CharField(max_length=50, default='added',
                              help_text='order placed,picking_done,billing_done,payment_done,items_delivered')
    payment_status = models.CharField(max_length=50, default="pending")
    mode_of_payment = models.CharField(max_length=50, default=None, blank=True, null=True)
    bank_ref_number = models.CharField(max_length=30, default=None, blank=True, null=True)
    refund_request_id = models.CharField(max_length=30, default=None, blank=True, null=True)
    delivery_type = models.CharField(max_length=50, default=None, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, default=None, blank=True, null=True)
    order_id = models.CharField(max_length=50, default=None, blank=True, null=True)
    slot = models.ForeignKey(SlotTiming, on_delete=models.CASCADE, blank=True, null=True)
    slot_date = models.DateField(blank=True, null=True)
    mrp = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True, help_text='Total MRP')
    discount = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True, help_text='Total Discount')
    delivery_charges = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True, default=0)
    paid_amount = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True,
                                      help_text='Total Amount payable')  #
    initial_paid_amount = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True,
                                              help_text='Total Amount payable')
    sm_initiated_txn = models.CharField(max_length=30, blank=True, null=True, help_text='refund,new_tnx')
    refund_amount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    transaction_fee = models.DecimalField(max_digits=20, decimal_places=10, default=0.0)
    pos_upi_payment_type = models.CharField(max_length=15, blank=True, null=True,
                                            help_text='cod,phone_pe,amazon_pay,paytm')
    pos_upi_payment_mode = models.CharField(max_length=15, blank=True, null=True,
                                            help_text='credit/debit/cash')
    pos_upi_mobile_number = models.CharField(max_length=13, blank=True, null=True, )
    store_code = models.BigIntegerField(blank=True, null=True, default=None)  #
    order_created_at = models.DateTimeField(default=None, blank=True, null=True)
    is_sudo_order = models.BooleanField(blank=True, null=True, default=False)
    image_url = models.TextField(blank=True, null=True)
    item_count = models.IntegerField(blank=True, null=True, default=None)
    is_cancelled = models.BooleanField(default=False, blank=True, null=True)
    cancel_reason = models.CharField(max_length=200, blank=True, null=True, default=None)
    order_created_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'purchase_details'


class Cart(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    product_id = models.ForeignKey(ProductDetail, on_delete=models.CASCADE, blank=True, null=True)
    item_count = models.DecimalField(max_digits=20, decimal_places=10, blank=False, null=False)
    item_count_value = models.DecimalField(max_digits=20, decimal_places=10, default=1.0,
                                           help_text='This is for pos order listing API')
    initial_item_count = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True, default=0.0)
    price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    special_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    final_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    cgst = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    sgst = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    discount = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    units = models.CharField(max_length=80, default=None, blank=True, null=True)
    status = models.CharField(max_length=50, default='added')
    name = models.TextField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    sku = models.BigIntegerField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_out_of_stock = models.BooleanField(default=False, blank=True, null=True)
    is_edited = models.BooleanField(default=False, blank=True, null=True)
    is_picked = models.BooleanField(default=False, blank=True, null=True)
    is_cancelled = models.BooleanField(default=False, blank=True, null=True)
    purchase_detail = models.ForeignKey(PurchaseDetails, on_delete=models.CASCADE, blank=True, null=True)
    edited_user = models.CharField(max_length=100, default=None, blank=True, null=True)

    class Meta:
        db_table = 'cart'


class RefundCart(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    product_id = models.ForeignKey(ProductDetail, on_delete=models.CASCADE)
    item_count = models.DecimalField(max_digits=20, decimal_places=10, blank=False, null=False)
    price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    special_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    final_price = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    cgst = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    sgst = models.DecimalField(max_digits=20, decimal_places=10, default=None, blank=True, null=True)
    discount = models.CharField(max_length=6, default=None, blank=True, null=True)
    units = models.CharField(max_length=80, default=None, blank=True, null=True)
    status = models.CharField(max_length=50, default='refund')
    name = models.TextField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    sku = models.BigIntegerField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    purchase_detail = models.ForeignKey(PurchaseDetails, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'refund_cart'


class OrderStatus(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    purchase_detail_id = models.ForeignKey(PurchaseDetails, on_delete=models.CASCADE, blank=False, null=False)
    status = models.CharField(max_length=50, blank=False, null=False)
    status_updated_on = models.CharField(max_length=10, blank=True, null=True, default='web', help_text='web/sm/pos')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'order_status'


class WhatsAppSession(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    wa_number = models.CharField(max_length=15, blank=False, null=False)
    store_code = models.BigIntegerField(blank=True, null=True)
    stage = models.CharField(max_length=50, default='session_started')
    is_active_session = models.BooleanField(default=True)
    is_suggestion_enabled = models.BooleanField(default=False)
    session_end_time = models.DateTimeField(blank=True, null=True)
    is_sm_notified = models.BooleanField(default=False)
    is_address_added = models.BooleanField(default=False)

    is_cart_freezed = models.BooleanField(default=False)
    is_requested_quantity = models.BooleanField(default=False)
    item_no_choice = models.CharField(max_length=15, default=None, blank=True, null=True)
    item_name_for_suggestions = models.CharField(max_length=50, default=None, blank=True, null=True)
    next_suggestion_value = models.IntegerField(default=0)
    item_total_count = models.IntegerField(default=0)
    cart_choice = models.CharField(max_length=20, default='view')
    is_opted_for_whatsapp_ordering = models.BooleanField(default=False)
    is_opted_for_whatsapp_surpriseme_ordering = models.BooleanField(default=False)

    is_store_registration = models.BooleanField(default=False)

    payment_mode = models.CharField(max_length=20, default=None, blank=True, null=True)
    payment_tool = models.CharField(max_length=20, default=None, blank=True, null=True)
    adding_items_start_time = models.DateTimeField(blank=True, null=True)
    adding_items_end_time = models.DateTimeField(blank=True, null=True)
    pincode = models.BigIntegerField(blank=True, null=True)
    available_stores = models.BigIntegerField(blank=True, null=True)
    sm = models.ForeignKey(UserOnboarding, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    is_moengage_updated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    purchase_detail = models.ForeignKey(PurchaseDetails, on_delete=models.CASCADE, blank=True, null=True, default=None)
    order_type = models.CharField(max_length=20, default=None, blank=True, null=True, help_text='chat,suggestions')

    class Meta:
        db_table = 'whats_app_session'


class CancelOrderReason(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reason = models.TextField(max_length=200, blank=True, null=True, default=None)
    type = models.TextField(max_length=50, default='web', help_text='web,sm')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'cancel_order_reason'


class WhatsAppSession(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    wa_number = models.CharField(max_length=15, blank=False, null=False)
    store_code = models.BigIntegerField(blank=True, null=True)
    stage = models.CharField(max_length=50, default='session_started')
    is_active_session = models.BooleanField(default=True)
    is_suggestion_enabled = models.BooleanField(default=False)
    session_end_time = models.DateTimeField(blank=True, null=True)
    is_sm_notified = models.BooleanField(default=False)
    is_address_added = models.BooleanField(default=False)

    is_cart_freezed = models.BooleanField(default=False)
    is_requested_quantity = models.BooleanField(default=False)
    item_no_choice = models.CharField(max_length=15, default=None, blank=True, null=True)
    item_name_for_suggestions = models.CharField(max_length=50, default=None, blank=True, null=True)
    next_suggestion_value = models.IntegerField(default=0)
    item_total_count = models.IntegerField(default=0)
    cart_choice = models.CharField(max_length=20, default='view')
    is_opted_for_whatsapp_ordering = models.BooleanField(default=False)
    is_opted_for_whatsapp_surpriseme_ordering = models.BooleanField(default=False)

    is_store_registration = models.BooleanField(default=False)

    payment_mode = models.CharField(max_length=20, default=None, blank=True, null=True)
    payment_tool = models.CharField(max_length=20, default=None, blank=True, null=True)
    adding_items_start_time = models.DateTimeField(blank=True, null=True)
    adding_items_end_time = models.DateTimeField(blank=True, null=True)
    pincode = models.BigIntegerField(blank=True, null=True)
    available_stores = models.BigIntegerField(blank=True, null=True)
    sm = models.ForeignKey(UserOnboarding, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    is_moengage_updated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    purchase_detail = models.ForeignKey(PurchaseDetails, on_delete=models.CASCADE, blank=True, null=True, default=None)
    order_type = models.CharField(max_length=20, default=None, blank=True, null=True, help_text='chat,suggestions')

    class Meta:
        db_table = 'whats_app_session'


class WhatsappTemplate(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    key = models.CharField(max_length=30, blank=False, null=False)
    template = models.CharField(max_length=20, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'whatsapp_template'
