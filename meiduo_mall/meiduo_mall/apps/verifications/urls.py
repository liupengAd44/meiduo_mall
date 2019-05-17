from django.conf.urls import url
from . import views

urlpatterns = [
    # 图片验证码的Vue路由配置，API
    # this.image_code_url = this.host + "/image_codes/" + this.uuid + "/"
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.VerificationCodeView.as_view()),  # 生成图形验证码

    # 短息验证码的Vue路由配置，API
    # var url = this.host + '/sms_codes/' + this.mobile + '/?image_code=' + this.image_code + '&uuid=' + this.uuid
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),# 发送短信验证码
]