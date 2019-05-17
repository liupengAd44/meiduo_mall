from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view()),  # 支付路由
    url(r'^payment/status/$', views.PaymentSuccessView.as_view()),  # 支付成功会掉路由
]
