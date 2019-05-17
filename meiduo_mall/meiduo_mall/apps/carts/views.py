from django.shortcuts import render
from django.views import View
from django import http
from django_redis import get_redis_connection

import pickle, base64, json

from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE

class CartsView(View):
    """购物车页面"""
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden('必传参数不全')

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')

        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        if user.is_authenticated:  # 登录状态
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)

            pl.execute()
        else:  # 匿名状态
            carts = request.COOKIES.get('carts')

            if carts:
                carts_dict = pickle.loads(base64.b64decode(carts.encode()))
            else:
                carts_dict = dict()

            if sku_id in carts_dict:
                origin_count = carts_dict[sku_id]['count']
                count += origin_count

            carts_dict[sku_id] = {'count': count, 'selected': selected}
            carts_str = base64.b64encode(pickle.dumps(carts_dict)).decode()
            response.set_cookie('carts', carts_str)
        return response

    def get(self, request):
        user = request.user

        if user.is_authenticated:  # 登录用户
            redis_conn = get_redis_connection('carts')
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            redis_selected = redis_conn.smembers('selected_%s' % user.id)
            carts_dict = dict()
            for sku_id, count in redis_carts.items():
                carts_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected,
                }

        else:  # 匿名用户
            carts_str = request.COOKIES.get('carts')
            # 判断有没有cookie购物车数据
            if carts_str:
                # 将字符串转换成字典
                carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))
            else:
                return render(request, 'cart.html')

        sku_qs = SKU.objects.filter(id__in=carts_dict.keys())

        cart_skus = list()
        for sku in sku_qs:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': str(sku.price),
                'default_image_url': sku.default_image.url,
                'count': carts_dict[sku.id]['count'],
                'selected': str(carts_dict[sku.id]['selected']),
                'amount': str(int(sku.price) * carts_dict[sku.id]['count']),
            }
            cart_skus.append(sku_dict)

        context = {
            'cart_skus': cart_skus
        }
        return render(request, 'cart.html', context)

    def put(self, request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden('必传参数不全')

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')

        user = request.user
        cart_sku = {
            'id': sku.id,
            'name': sku.name,
            'price': sku.price,
            'default_image_url': sku.default_image.url,
            'count': int(count),
            'selected': selected,
            'amount': sku.price*int(count)

        }
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})

        if user.is_authenticated:  # 登录状态
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)

            pl.execute()
        else:  # 匿名状态
            carts = request.COOKIES.get('carts')

            if carts:
                carts_dict = pickle.loads(base64.b64decode(carts.encode()))
            else:
                carts_dict = dict()

            if sku_id in carts_dict:
                origin_count = carts_dict[sku_id]['count']
                count += origin_count

            carts_dict[sku_id] = {'count': count, 'selected': selected}
            carts_str = base64.b64encode(pickle.dumps(carts_dict)).decode()
            response.set_cookie('carts', carts_str)
        return response

    def delete(self, request):
        # 接收sku_id
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku不存在')

        # 判断是否登录
        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        if user.is_authenticated:
            # 登录操作redis数据
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            # 创建管道
            pl = redis_conn.pipeline()

            # 删除hash中的sku_id及count
            pl.hdel('carts_%s' % user.id, sku_id)
            # 删除set集合中的勾选
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

        else:
            # 未登录操作cookie数据
            # 获取cookie数据
            cart_str = request.COOKIES.get('carts')

            # 判断cookie是否获取到
            if cart_str:
                # 把字符串转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 没有获取cookie数据 直接返回
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': 'cookie没有获取到'})
            # 判断当前要删除的sku_id在字典中是否存在
            if sku_id in cart_dict:
                # del cart_dict[sku_id]
                del cart_dict[sku_id]

            if len(cart_dict.keys()) == 0:  # 如果cookie中的购物车数据已经删除完了
                response.delete_cookie('carts')  # 删除cookie

            # 将字典转换成字符串
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 设置cookie
            response.set_cookie('carts', cart_str)
        # 响应
        return response


class CartsSelectView(View):
    """购物车全选"""
    def put(self, request):
        # 获取前端的选项框
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')
        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('参数有误')

        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        if user.is_authenticated:
            # 正常用户数据在Redis
            redis_conn = get_redis_connection('carts')
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            if selected:
                redis_conn.sadd('selected_%s' % user.id, *redis_carts.keys())
            else:
                redis_conn.delete('selected_%s' % user.id)
        else:
            # 匿名用户在COOKIE里
            # 获取cookie数据carts，并解码
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                carts_dict = pickle.loads(base64.b64decode(cookie_carts.encode()))
            else:
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': 'cookie里缺少数据'})

            for sku_id in carts_dict:
                carts_dict[sku_id]['selected'] = selected
            carts = base64.b64encode(pickle.dumps(carts_dict)).decode()
            response.set_cookie('carts', carts)
        return response


class CartsSimple(View):
    """购物车mini窗口"""
    def get(self, request):
        user = request.user

        if user.is_authenticated:  # 登录用户
            redis_conn = get_redis_connection('carts')
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            redis_selected = redis_conn.smembers('selected_%s' % user.id)
            carts_dict = dict()
            for sku_id, count in redis_carts.items():
                carts_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected,
                }

        else:  # 匿名用户
            carts_str = request.COOKIES.get('carts')
            # 判断有没有cookie购物车数据
            if carts_str:
                # 将字符串转换成字典
                carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))
            else:
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '购物车没有数据'})

        sku_qs = SKU.objects.filter(id__in=carts_dict.keys())

        cart_skus = list()
        for sku in sku_qs:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': str(sku.price),
                'default_image_url': sku.default_image.url,
                'count': carts_dict[sku.id]['count'],
            }
            cart_skus.append(sku_dict)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})

