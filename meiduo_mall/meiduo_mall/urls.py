"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^search/', include('haystack.urls', namespace='search')),  # 检索搜索
    # url(r'^accounts/', include('allauth.urls', namespace='allauth')),  # 定义认证登录
    url(r'^', include('users.urls', namespace='users')),  # 用户
    url(r'^', include('contents.urls', namespace='contents')),  # 内容
    url(r'^', include('verifications.urls', namespace='verifications')),  # 验证
    url(r'^', include('oauth.urls', namespace='oauth')),  # 授权
    url(r'^', include('areas.urls', namespace='areas')),  # 省市区
    url(r'^', include('goods.urls', namespace='goods')),  # 商品
    url(r'^', include('carts.urls', namespace='carts')),  # 购物车
    url(r'^', include('orders.urls', namespace='orders')),  # 订单
    url(r'^', include('payment.urls', namespace='payment')),  # 支付
    url(r'^', include('example.urls', namespace='example')),  # 很笨的机器人
    url(r'^', include('github.urls', namespace='github')),  # github第三登录
    url(r'^', include('sina.urls', namespace='sina')),  # 微博第三方登录

]
