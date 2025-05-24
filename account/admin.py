from django.contrib import admin
from account.models import ExchangeProposal, Ad, Category
admin.site.register(Ad)
admin.site.register(ExchangeProposal)
admin.site.register(Category)