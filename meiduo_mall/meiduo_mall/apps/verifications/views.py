from django.shortcuts import render
from PIL import Image,ImageDraw,ImageFont  # 图形验证码制作
from django.utils.six import BytesIO  # 内存操作
from django import http
from django.views import View  # 继承View,创建类视图
from django_redis import get_redis_connection  # 将限时数据存入redis数据库
from random import randrange, randint  # 画图形验证及短信随机数
from logging import getLogger

from . import constants  # 导入自定义设置文件(redis数据有效时间)
# Create your views here.


logger = getLogger('django')

class VerificationCodeView(View):
    """图片验证"""

    def get(self, request, uuid):
        # 定义变量，用于画The length, width and height of the background
        bgcolor = (randrange(20, 100), randrange(20, 100), 255)  # RGB
        width = 100
        height = 25
        # 创建画画对象
        im = Image.new('RGB',(width, height), bgcolor)
        # 创建画笔对象
        draw = ImageDraw.Draw(im)
        # 调用画笔的point()函数绘制噪点
        for i in range(0,100):
            xy = (randrange(0,width), randrange(0,height))
            fill = (randrange(0, 255), 255, randrange(0, 255))
            draw.point(xy, fill=fill)
        # 定义验证码的备选值
        str1 = "abcdefghijklmnopqrstwvuxyz0123456789ABCDEFGHIJKLMNOPQRSTWVUXYZ"
        # 随机选取4个值作为验证码
        rand_str = ''
        for i in range(0, 4):
            rand_str += str1[randrange(0, len(str1))]


        # 构造字体对象,ubuntu的字体路径为/usr/share/fonts/truetype/freefont
        font = ImageFont.truetype('FreeMono.ttf', 23)
        fontcolor = (255, randrange(0, 255), randrange(0, 255))
        # 开始画验证码
        draw.text((5,2), rand_str[0], font=font, fill=fontcolor)
        draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
        draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
        draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)

        # 释放画笔
        del draw
        # 存入session，用于做进一步验证
        # request.session['verifycode'] = rand_str
        # 内存文件操作
        buf = BytesIO()
        # 将图片保存在内存中,文件类型为png
        im.save(buf, 'png')

        # 使用redis存储零时前段uuid，有效时间，值
        redis_conn = get_redis_connection('verify_code')  # 根据dev里的redis配置
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, rand_str)

        # 将内存中的图片数据返回给客户端，MIME类型为图片png
        return http.HttpResponse(buf.getvalue(), content_type='image/png')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, request, mobile):
        # 导入自定义的状态码
        from meiduo_mall.utils.response_code import RETCODE
        from celery_tasks.sms.tasks import send_sms_code

        """
        :param mobile: 要接收短信验证码的手号
        """

        # sms_flag变量 表示标记该手机号已发短信验证码
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('sms_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '获取短信请求过于频繁'})
        # 获取前段路由传来的image/uuid数据
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        if all([image_code_client, uuid]) is False:  # 看参数是否传齐全
            return  http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        # 获取redis数据库的图片信息，与用户传进来的数据比对
        image_code_server = redis_conn.get('img_%s' % uuid)  # # 根据uuid作为key 获取到redis中当前用户的图形验证值
        redis_conn.delete('img_%s' % uuid)  # 此时数据已用变量保存， 删除图形验证码，让它只能用一次，防止刷
        if image_code_server is None or image_code_client.lower() != image_code_server.decode().lower():
            return  http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码错误'})

        # 随机生成验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)  # 在终端输出，方便测试


        # 创建redis管道对象
        pl = redis_conn.pipeline()  # 创建管道，多发多收，redis优化
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)  # 短信验证码存储进redis
        pl.setex('sms_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)  # 标记用户已发送短信验证码
        pl.execute()  # 执行管道里的redis语句

        send_sms_code.delay(mobile,sms_code)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送成功'})