from django.contrib import admin

from payment.models import Account, Subscription

# Register your models here.
admin.site.register(Account)
admin.site.register(Subscription)
