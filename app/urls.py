from django.urls import path
from .views import login_view,get_ticket,purchase_ticket

urlpatterns = [
    path('login', login_view, name='login'),
    path('get-ticket', get_ticket, name='get_ticket'),
    path('purchase-ticket', purchase_ticket, name='purchase_ticket'),
    
]