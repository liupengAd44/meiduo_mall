# 应用users 配置子路由
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register'),   # 注册页面路由配置

    # username的Vue路由配置，API
    # this.host + '/usernames/' + this.username + '/count/'
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),

    # mobile的Vue路由配置，API
    # mobiles/' + this.mobile + '/count/
    url(r'^mobiles/(?P<mobile>1[3456789]\d{9})/count/', views.MobileCountView.as_view()),

    # 登录简介的路由配置
    url(r'^login/$', views.LoginView.as_view(), name='login'),

    # 用户中心信息的路由配置
    url(r'^info/$', views.UserCenterInfoView.as_view(), name='info'),

    # 登出的路由配置
    url(r'^logout/$', views.LogoutView.as_view()),

    # 设置邮箱的路由配置  emails/
    url(r'^emails/$', views.EmailActivationView.as_view()),

    # 激活邮箱的路由配置
    url(r'^emails/verification/$', views.VerificationEmail.as_view()),

    # 用户地址信息的路由配置
    url(r'^addresses/$', views.UserAddressInfoView.as_view(), name='address'),

    # 用户地址创建的路由配置
    url(r'^addresses/create/$', views.CreateAddressView.as_view()),
    # 用户收货地址修改和删除
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 用户设置默认地址
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    # 修改用户地址标题
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateTitleAddressView.as_view()),
    # 修改用户密码
    url(r'^password/$', views.ChangePasswordView.as_view()),
    # 浏览记录
    url(r'^browse_histories/$', views.UserBrowseHistory.as_view()),
    # 全部订单
    url(r'^orders/info/(?P<page_num>\d+)/$', views.UserOrderInfoView.as_view())
]
