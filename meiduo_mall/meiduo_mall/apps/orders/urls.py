from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^orders/settlement/$', views.OrdersView.as_view()),  # 订单界面
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),  # 订单提交
    url(r'^orders/success/$', views.OrderSuccessView.as_view()),  # 成功下单
    url(r'^orders/comment/$', views.OrderCommentView.as_view()),  # 订单评价
    url(r'^comments/(?P<sku_id>\d+)/$', views.GoodsCommentView.as_view()),  # 商品详情评价
]