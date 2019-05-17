from django.shortcuts import render
from django import http

from alipay import AliPay  # 支付宝API
import os

from meiduo_mall.utils.views import LoginRequiredView
from orders.models import OrderInfo
from django.conf import settings
from meiduo_mall.utils.response_code import RETCODE
from .models import Payment

class PaymentView(LoginRequiredView):
    def get(self, request, order_id):
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=request.user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('参数有误')

        # 创建AliPay 对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'keys/app_private_key.pem'),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 调用它的方法api_alipay_trade_page_pay得到支付链接后面的查询参数部分
        order_string = alipay.api_alipay_trade_page_pay(
            subject='美多商城%s' % order_id,
            out_trade_no=order_id,
            total_amount=str(order.total_amount),  # 要注意转换类型
            return_url=settings.ALIPAY_RETURN_URL
        )

        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'alipay_url': alipay_url})


class PaymentSuccessView(LoginRequiredView):
    def get(self, request):
        # 获取回调的数据，提取参数
        query_dict = request.GET
        data = query_dict.dict()
        signature = data.pop('sign')


        # http://www.meiduo.site:8000/payment/status/
        # ?charset=utf-8&
        # out_trade_no=20190513172141000000001&
        # method=alipay.trade.page.pay.return&
        # total_amount=13008.00&
        # sign=ymOxBpB9OSAeDzr%2BfDI%2FS8oXgqSJCepQrR95tGoN8ijyYeEYLyvqYQ22MC7gSWClBBGouBKwVWSYI3W2y6ttGdDOPXERN%2BHdB4y%2B5pcvBNnlK6TCw8OrpYFvPhvuLoTJaZCd0sf27J8GKGS5%2F5Q3fECCwCMi5e4Zvl7sCSnMckmG8KHfuSo7rBH53e4VCvM3AtP8mzMxlaK%2F5DHaAkmxhqajaxjrTG%2FgOtPs5%2BleTcACbL%2BEDMui5j3K2JnnpH3GtReAKfgnrYWQqgB4IZz6LvcOqDbLYL6zEaDcvdcipK4SaD6iwBCeDh03mszyh1NiKEnzBOszNHZT9BDJ8bDpuQ%3D%3D&
        # trade_no=2019051422001455201000016542&
        # auth_app_id=2016092900625050&
        # version=1.0&
        # app_id=2016092900625050&
        # sign_type=RSA2&seller_id=2088102177828156&
        # timestamp=2019-05-14+16%3A24%3A43

        # 创建AliPay 对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'keys/app_private_key.pem'),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 使用alipay验证参数
        result = alipay.verify(data, signature)

        if result:
            # 交易单号
            order_id = data.get('out_trade_no')
            trade_id = data.get('trade_no')

            try:
                Payment.objects.get(order_id=order_id, trade_id=trade_id)
            except Payment.DoesNotExist:
                Payment.objects.create(order_id=order_id, trade_id=trade_id)

            # 修改订单状态
            OrderInfo.objects.filter(user=request.user, order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])\
                .update(status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
            return render(request, 'pay_success.html', {'trade_id': trade_id})
        else:
            return http.HttpResponseForbidden('非法请求')

        # 支付账号：ojrirh6915@sandbox.com

