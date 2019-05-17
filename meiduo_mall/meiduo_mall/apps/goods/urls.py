from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),  # 第三级sku商品的展示
    url(r'^hot/(?P<category_id>\d+)/$', views.SKUSalesView.as_view()),   # 销量展示
    url(r'^detail/(?P<sku_id>\d+)/$', views.GoodsDetailView.as_view()),  # 商品详情

    url(r'^detail/visit/(?P<category_id>\d+)/$', views.DetailVisitView.as_view()),  # 商品类别每日访问量统计

]