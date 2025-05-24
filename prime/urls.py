"""
URL configuration for prime project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from account import views as account_views 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.ad_list, name='ad_list'), # ВАЩЕ include НАДА НО ТАК КАК ПРОЕКТ МЕЛКИЙ ТАК ТОЖЕ МОЖНО
    path('<str:id>/', account_views.ad_detail, name='ad_detail'),
    path('ad/<str:ad_receiver_id>/create-trade/', account_views.create_trade, name='create_trade'),
    path('proposal/<int:proposal_id>/accept/', account_views.accept_proposal, name='accept_proposal'),
    path('proposal/<int:proposal_id>/reject/', account_views.reject_proposal, name='reject_proposal'),
    path('edit/<str:id>/', account_views.edit, name='edit'),
    path('delete/<str:id>/', account_views.delete, name='delete'),
    path('offers/<str:id>/', account_views.offers, name='offers'),
    path('ad/create/', account_views.create, name='create')
]
