from goods.models import GoodsChannel

def get_categories():
    categories = {}
    goods_channel_qs = GoodsChannel.objects.order_by('group_id', 'sequence')  # 将顶级频道信息按组和顺序进行排序
    for channel in goods_channel_qs:
        group_id = channel.group_id  # 遍历获得组id  共计11组

        # 判断组id是否存在
        if group_id not in categories:  # 如果组id不存在则创建新组
            categories[group_id] = {'channels': [], 'cat_subs': []}  # 按组id当键
        cat1 = channel.category  # 获取商品种类，一类
        cat1.url = channel.url
        categories[group_id]['channels'].append(cat1)  # 将一类商品名添加至组id

        # cat2_qs = cat1.subs.all()  # 获取当前一组下面的所有二级数据
        # for cat2 in cat2_qs:  # 遍历二级数据查询集
        #     cat3_qs = cat2.subs.all()  # 获取当前二级下面的所有三级 得到三级查询集
        #     cat2.cat_subs = cat3_qs  # 把二级下面的所有三级绑定给cat2对象的cat_subs属性
        #     categories[group_id]['cat_subs'].append(cat2)

        # 获取当前一组下面的所有二级数据
        for cat2 in cat1.subs.all():  # 遍历二级数据查询集
            cat3_qs = cat2.subs.all()  # 获取当前二级下面的所有三级 得到三级查询集
            cat2.cat_subs = cat3_qs  # 把二级下面的所有三级绑定给cat2对象的cat_subs属性
            categories[group_id]['cat_subs'].append(cat2)


    return categories