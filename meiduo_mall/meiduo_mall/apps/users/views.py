from django.shortcuts import render, redirect  # 使用django提供的渲染,重定向页面，
from django.views import View  # 使用类视图
from django import http # 使用http的相应
from django.urls import reverse  # 域名反解析,切记reverse不是在shortcut里面
from django.contrib.auth import login, logout  # django提供了状态保持与退出登录
from django_redis import get_redis_connection  # 链接redis数据库
from django.contrib.auth import authenticate  # django提供的验证方法，已经重写，添加手机认证
from django.conf import global_settings  # 全局配置
from django.contrib.auth.mixins import LoginRequiredMixin  # django提供的类视图拓展类
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from logging import getLogger  # log日志
from pymysql import DatabaseError  # API中定义了一些数据库操作的错误及异常，和数据库有关的错误发生时触发
from re import match  # 使用正则对POST请求数据进行校验
import json
from .utils import EmailSerializer
from goods.models import SKU
from orders.models import OrderGoods,OrderInfo
"""
定义的扩展父类名称通常以Mixin结尾
使用面向对象多继承的特性，可以通过定义父类（作为扩展类），
    在父类中定义想要向类视图补充的方法，类视图继承这些扩展父类，便可实现代码复用
"""

from .models import User, Address  # 导入自定义User模型，校验后保存
from meiduo_mall.utils.response_code import RETCODE  # 自定义状态码
from meiduo_mall.utils.views import LoginRequiredView  # 自定义的拓展类mixin
from carts.utils import merge_carts

# Create your views here.

logger = getLogger('django')  # 创建日志输出对象



class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        """
        实现用户注册
        :param request: 请求对象
        :return: 注册结果
        """
        # 从注册页面获取表单数据，在后端进行校验
        """
            用户名：username
            密码：password
            确认密码：password2
            手机号码：mobile
            图片验证码：image_code
            短信验证码：sms_code
            是否同意协议：allow
            """
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        # image_code = request.POST.get('image_code')
        sms_code = request.POST.get('sms_code')
        # all内置函数，判断给定的可迭代参数 iterable 中的所有元素是否都为 TRUE
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 正则匹配用户名
        if not match(r'^[\w-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 正则匹配密码
        if not match(r'^[\w]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否相同
        if password2 != password:
            return http.HttpResponseForbidden('两次密码不一致')
        # 正则匹配是否有效手机号
        if not match(r'^1[3-9]\d{9}', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 确认用户是否同意协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        # 短信验证
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if sms_code_server is None or sms_code != sms_code_server.decode().lower():
            return http.HttpResponseForbidden('短信验证码有误')




        try:
            # User模型提供了创建用户的方法
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError as e:
            # 将数据库宕机的错误，输出至log日志中
            logger.error(e)
            # 将错误用模板变量放在前段
            return redirect(request, 'register.html', {'register_errmsg': '注册失败'})

        # 状态保持
        # login(request, user=username)  # 此写法仅保存用户名
        login(request, user)  # 储存用id到session中记录状态保持

        response = redirect('/')
        response.set_cookie('username', user.username, max_age=global_settings.SESSION_COOKIE_AGE)
        return response



class UsernameCountView(View):
    """判断用户名是否已注册"""

    # 根据API，接收username，进行校验
    def get(self, request, username):
        print(username)

        # 查询当前用户名的个数要么0要么1 1代表重复
        count = User.objects.filter(username=username).count()
        print(count)

        # 将数据返回给axios，后面两个参数是一个规范
        return http.JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})



class MobileCountView(View):
    """判断手机号是否已注册"""
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})



class LoginView(View):
    """用户登录的类视图"""
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):

        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        if all([username, password]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        # 校验
        # user = User.objects.get(username=username)
        # user.check_password(password)
        # if re.match(r'^1[3-9]\d{9}$', username):
        #     User.USERNAME_FIELD = 'mobile'

        user = authenticate(username=username, password=password)  # 如果账号密码为真将对象返回,否则False
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        login(request, user)  # 状态保持
        if remembered != 'on':  # 如果用户没有勾选记住账户密码
            request.session.set_expiry(0)  # 将session的过期时间设为0
        # if remembered != 'on':  # 没有勾选记住登录
        #     settings.SESSION_COOKIE_AGE = 0  # 修改Django的SESSION缓存时长

        # 从定向，设置cookie
        # 提取前端用查询参数传入的next参数: 记录用户从哪里去到login界面
        response = redirect(request.GET.get('next', '/'))  # 获取路由的参数，避免未登录就可以进入用户信息界面
        response.set_cookie('username', user.username, max_age=global_settings.SESSION_COOKIE_AGE)
        merge_carts(request, user, response)
        return response


class UserCenterInfoView(LoginRequiredMixin, View):
    """用户信息的类视图"""
    # 拓展类，根据mro算法继承，django提供了LoginRequiredMixin方法
    def get(self, request):
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }


        return render(request, 'user_center_info.html', context=context)


class LogoutView(View):
    """退出登录的类视图"""
    def get(self, request):
        logout(request)  # django提供的退出登录

        # 退出后重定向至首页，并创建对象，调用清除cookie的方法
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')
        return response


class EmailActivationView(LoginRequiredView):
    """验证email的类视图"""
    def put(self, request):
        # 前段发送的put请求
        js_dict = json.loads(request.body.decode())

        email = js_dict.get('email')

        if email is None or not match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('email有误')

        # 将邮箱存储进数据库
        user = request.user
        user.email = email
        user.save()

        # 对路由附带用户信息参数进行加密

        email_url = EmailSerializer.generate_email_signature(user)

        # 异步发送邮件
        from celery_tasks.smtp.tasks import send_smtp
        # 'http://www.meiduo.site:8000/emails/verification/?token=2'
        send_smtp.delay(email, email_url)  # 发送邮件时请求了该路由

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class VerificationEmail(View):
    """激活邮箱的类视图"""
    def get(self, request):
        token = request.GET.get('token')
        user = EmailSerializer.check_email_signature(token)

        if not user:
            return http.HttpResponseForbidden('邮箱验证码已失效')

        # 无需获取对象信息，generate_email_signature进去时就是一个user对象
        user.email_active = True
        user.save()

        return redirect('/info/')


class UserAddressInfoView(LoginRequiredView):
    """用户收货地址"""

    def get(self, request):
        """提供用户收货地址界面"""
        # 获取当前用户的所有收货地址
        user = request.user
        # address = user.addresses.filter(is_deleted=False)  # 获取当前用户的所有收货地址
        address_qs = Address.objects.filter(is_deleted=False, user=user)  # 获取当前用户的所有收货地址

        address_list = []
        for address in address_qs:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': address.province.name,
                'city_id': address.city_id,
                'city': address.city.name,
                'district_id': address.district_id,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email,
            }
            address_list.append(address_dict)

        context = {
            'addresses': address_list,
            'default_address_id': user.default_address_id
        }
        return render(request, 'user_center_site.html', context)


class CreateAddressView(LoginRequiredView):
    def post(self, request):
        user = request.user
        # 判断用户的收货地址数据,如果超过20个提前响应
        count = Address.objects.filter(user=user, is_deleted=False).count()
        # count = user.addresses.count()
        if count >= 20:
            return http.HttpResponseForbidden('用户收货地址上限')
        # 接收请求数据
        json_dict = json.loads(request.body.decode())
        """
            title: '',
            receiver: '',
            province_id: '',
            city_id: '',
            district_id: '',
            place: '',
            mobile: '',
            tel: '',
            email: '',
        """
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        try:
            address = Address.objects.create(
                user=user,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            if user.default_address is None:
                user.default_address = address
                user.save()
        except Exception:
            return http.HttpResponseForbidden('新增地址出差')

            # 把新增的地址数据响应回去
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    def put(self,request, address_id):
        try:
            Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要修改的地址不存在')

        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')
        # 修改update
        Address.objects.filter(id=address_id).update(
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        address = Address.objects.get(id=address_id)  # 要重新查询一次新数据
        # 把新增的地址数据响应回去
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})
        # 响应

    def delete(self, request, address_id):
        """对收货地址逻辑删除"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要删除的地址不存在')

        address.is_deleted = True
        # address.delete()
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DefaultAddressView(LoginRequiredView):
    """设置默认地址"""

    def put(self, request, address_id):
        """实现默认地址"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要修改的地址不存在')

        user = request.user
        user.default_address = address
        user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class UpdateTitleAddressView(LoginRequiredView):
    """修改用户收货地址标题"""
    def put(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要修改的地址不存在')

        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        address.title = title
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class ChangePasswordView(LoginRequiredView):
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        # 接收参数
        old_password = request.POST.get('old_pwd')
        password = request.POST.get('new_pwd')
        password2 = request.POST.get('new_cpwd')

        # 校验
        if all([old_password, password, password2]) is False:
            return http.HttpResponseForbidden("缺少必传参数")

        user = request.user
        if user.check_password(old_password) is False:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})

        if not match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改密码
        user.set_password(password)
        user.save()

        # 响应重定向到登录界面
        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')

        return response


class UserBrowseHistory(View):
    """用户商品浏览记录"""

    def post(self, request):

        # 判断当前用户是否登录
        user = request.user
        if not user.is_authenticated:
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})

        # 获取请求体中的sku_id
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 校验sku_id
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()

        key = 'history_%s' % user.id
        # 先去重
        pl.lrem(key, 0, sku_id)

        # 存储到列表的开头
        pl.lpush(key, sku_id)

        # 截取前5个
        pl.ltrim(key, 0, 4)
        # 执行管道
        pl.execute()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """浏览记录查询"""

        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        sku_id_list = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        # 获取当前登录用户的浏览记录列表数据 [sku_id1, sku_id2]

        # 通过sku_id查询sku,再将sku模型转换成字典
        # sku_qs = SKU.objects.filter(id__in=sku_id_list)  [b'3', b'2', b'5'] [2, 3, 5]
        skus = []  # 用来装每一个sku字典
        for sku_id in sku_id_list:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            }
            skus.append(sku_dict)
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class UserOrderInfoView(LoginRequiredView):

    def get(self, request, page_num):

        user = request.user
        # 查询当前登录用户的所有订单
        order_qs = OrderInfo.objects.filter(user=user).order_by('-create_time')
        for order_model in order_qs:

            # 给每个订单多定义两个属性, 订单支付方式中文名字, 订单状态中文名字
            order_model.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order_model.pay_method - 1][1]
            order_model.status_name = OrderInfo.ORDER_STATUS_CHOICES[order_model.status - 1][1]
            # 再给订单模型对象定义sku_list属性,用它来包装订单中的所有商品
            order_model.sku_list = []

            # 获取订单中的所有商品
            order_good_qs = order_model.skus.all()
            # 遍历订单中所有商品查询集
            for good_model in order_good_qs:
                sku = good_model.sku  # 获取到订单商品所对应的sku
                sku.count = good_model.count  # 绑定它买了几件
                sku.amount = sku.price * sku.count  # 给sku绑定一个小计总额
                # 把sku添加到订单sku_list列表中
                order_model.sku_list.append(sku)

        # 创建分页器对订单数据进行分页
        # 创建分页对象
        paginator = Paginator(order_qs, 2)
        # 获取指定页的所有数据
        page_orders = paginator.page(page_num)
        # 获取总页数
        total_page = paginator.num_pages

        context = {
            'page_orders': page_orders,  # 当前这一页要显示的所有订单数据
            'page_num': page_num,  # 当前是第几页
            'total_page': total_page  # 总页数
        }
        return render(request, 'user_center_order.html', context)


