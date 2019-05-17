import pickle, base64
from django_redis import get_redis_connection


def merge_carts(request, user, response):
    # 获取COOKIE值
    carts_str = request.COOKIES.get('carts')
    if carts_str is None:
        return
    carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))

    # 合并至Redis中
    redis_conn = get_redis_connection('carts')
    redis_pl = redis_conn.pipeline()
    for sku_id, sku_dict in carts_dict.items():
        redis_pl.hset('carts_%s' % user.id, sku_id, sku_dict['count'])
        redis_pl.sadd('selected_%s' % user.id, sku_id) if sku_dict['selected'] else redis_pl.srem('selected_%s' % user.id, sku_id)
    redis_pl.execute()
    # 合并后删除COOKIES
    response.delete_cookie('carts')
