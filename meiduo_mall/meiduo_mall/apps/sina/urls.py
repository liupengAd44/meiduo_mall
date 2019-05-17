from django.conf.urls import url
from . import views

urlpatterns = [
    url('^oauth/weibo/login/', views.SinaOAuthView.as_view()),  # 微博授权页面
    url('^weibo_callback/$', views.SinaOAuthCallbackView.as_view()),  # 微博回调页面
]


