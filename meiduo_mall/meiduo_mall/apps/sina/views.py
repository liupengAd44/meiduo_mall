from django.shortcuts import render,redirect
from django.views import View
from django import http
from django.conf import settings

from .models import OAuthSinaUser
from .sinaweibopy3 import APIClient
from meiduo_mall.utils.response_code import RETCODE
# Create your views here.



class SinaOAuthView(View):
    def get(self, request):

        oauth = APIClient(app_key=settings.SINA_APP_KEY,
                          app_secret=settings.SINA_SECRET,
                          redirect_uri=settings.SINA_CALLBACK)
        login_url = oauth.get_authorize_url()

        return http.HttpResponseRedirect(login_url)


class SinaOAuthCallbackView(View):
    """微博登录后回调处理"""

    def get(self, request):

        # 获取查询字符串中的code
        code = request.GET.get('code')
        state = request.GET.get('state', '/')


        # 创建QQ登录SDK对象
        oauth = APIClient(app_key=settings.SINA_APP_KEY,
                          app_secret=settings.SINA_SECRET,
                          redirect_uri=settings.SINA_CALLBACK
                        )
        access_token = oauth.request_access_token(code)
        print(access_token)

        # try:
            # 调用SDK中的get_access_token(code) 得到access_token
            # access_token = oauth.request_access_token(code)
            # 调用SDK中的get_openid(access_token) 得到openid
    #         openid = oauth.get_open_id(access_token)
    #     except Exception as e:
    #         logger.error(e)
    #         return http.JsonResponse({'code': RETCODE.SERVERERR, 'errmsg': 'QQ服务器不可用'})
    #
    #     # 在OAuthQQUser表中查询openid
    #     try:
    #         oauth_model = OAuthQQUser.objects.get(openid=openid)
    #     except OAuthQQUser.DoesNotExist:
    #         # 如果在OAuthQQUser表中没有查询到openid, 说明没绑定
    #         openid = DataSerializer.generate_data_signature(openid)  # 对openid进行加密传入前段
    #         # 创建一个新的美多用户和QQ的openid绑定
    #         return render(request, 'oauth_callback.html', {'openid': openid})
    #     else:
    #         # 如果在OAuthQQUser表中查询到openid,说明是已绑定过美多用户的QQ号
    #         user = oauth_model.user
    #         login(request, user)
    #         # 直接登录成功:  状态操持,
    #         response = redirect(state)
    #         response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
    #         return response
    #
    #
    # def post(self, request):
    #     # 获取QQ回调的绑定用户页面的表单数据
    #     openid = request.POST.get('openid')  # QQ登录后回调产生的openid唯一值
    #     password = request.POST.get('password')
    #     mobile = request.POST.get('mobile')
    #     sms_code = request.POST.get('sms_code')
    #
    #     if not all([openid, password, mobile]):
    #         return http.HttpResponseForbidden("缺少必传参数")
    #     if not match(r'^[\w]{8,20}$', password):
    #         return http.HttpResponseForbidden('请输入8-20位的密码')
    #     if not match(r'^1[3-9]\d{9}', mobile):
    #         return http.HttpResponseForbidden('请输入正确的手机号码')
    #
    #     redis_conn = get_redis_connection('verify_code')
    #     sms_code_server = redis_conn.get('sms_%s' % mobile)
    #     if sms_code_server is None or sms_code_server.decode() != sms_code:
    #         return http.HttpResponseForbidden('短信验证码有误')
    #
    #     openid = DataSerializer.check_data_signature(openid)
    #     if openid is None:
    #         return http.HttpResponseForbidden('openid已过期')
    #
    #     try:
    #         user = User.objects.get(mobile=mobile)  # 判断绑定的用户是否存在
    #     except User.DoesNotExist:  # 没有则创建，此时的用户名为手机号
    #         user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
    #     else:  # 如果有则检查密码
    #         if user.check_password(password) is False:
    #             return http.HttpResponseForbidden('账号或密码错误')
    #
    #     # 创建QQ表的用户信息
    #     OAuthQQUser.objects.create(user=user, openid=openid)
    #
    #     # 重定向
    #     login(request, user)  # 保持状态
    #     response = redirect(request.GET.get('state'))  # 不能反解析，因为之前记录了从哪来
    #     response.set_cookie('username', user.username, max_age=global_settings.SESSION_COOKIE_AGE)  # SESSION_COOKIE_AGE全局的cookie到期时间
    #     merge_carts(request, user, response)
    #     return response