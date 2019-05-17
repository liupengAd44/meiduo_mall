from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^carts/$', views.CartsView.as_view()),  # 购物车页面
    url(r'^carts/selection/$', views.CartsSelectView.as_view()),  # 购物车全选
    url(r'^carts/simple/', views.CartsSimple.as_view()),  # 迷你购物车窗口
]
