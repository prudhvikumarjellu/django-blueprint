from django import forms


class UpdateStatusPayload(forms.Form):
    status = forms.CharField()
    purchase_id = forms.CharField()


class PickupPayload(forms.Form):
    is_picked = forms.BooleanField()
    purchase_id = forms.CharField()
    product_id = forms.CharField()


class UpdateCartPayload(forms.Form):
    count = forms.FloatField()
    purchase_id = forms.CharField()
    product_id = forms.CharField()
    user_name = forms.CharField(required=False)
    price = forms.FloatField()


class UpdatePurchaseDetailsPayload(forms.Form):
    item_count = forms.IntegerField()
    image_url = forms.CharField(required=False)
    order_id = forms.CharField(required=False)
    purchase_id = forms.CharField()
    total_amount = forms.DecimalField()


class CancelPayload(forms.Form):
    purchase_id = forms.CharField()
    reason = forms.CharField()
