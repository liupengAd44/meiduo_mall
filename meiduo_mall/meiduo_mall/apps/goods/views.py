from django.shortcuts import render
from django.views import View
from django.core.paginator import Paginator  # Django提供的分页器
from django import http
from django.utils import timezone

from .models import GoodsCategory,SKU,GoodsVisitCount
from .utils import get_breadcrumb
from contents.utils import get_categories
from meiduo_mall.utils.response_code import RETCODE


class ListView(View):
    """商品展示"""
    def get(self, request, category_id, page_num):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('商品页面不存在')

        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'
        else:
            sort_field = 'create_time'


        sku_qs = category.sku_set.filter(is_launched=True).order_by(sort_field)

        # 创建分页对象
        paginator = Paginator(sku_qs, 5)  # Paginator(要进行分页的所有数据, 每页显示多少条数据)
        page_skus = paginator.page(page_num)  # 获取指定界面的sku数据
        total_page = paginator.num_pages  # 获取当前的总页数 paginator提供num_pages总页数方法



        # 渲染页面
        context = {
            'categories': get_categories(),  # 频道分类
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航
            'sort': sort_field,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request, 'list.html', context)



class SKUSalesView(View):
    """商品热销"""
    def get(self, request, category_id):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('商品未找到')

        # 获取当前三级类别下面销量最高的前两个sku
        skus_qs = category.sku_set.filter(is_launched=True).order_by('-sales')[0:2]

        hot_skus = []  # 包装两个热销商品字典
        for sku in skus_qs:
            hot_skus.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class GoodsDetailView(View):
    def get(self, request, sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')
        category = sku.category  # 获取sku商品类别
        spu = sku.spu  # 获取spu


        # 获取当前商品的sku规格id
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_spec_list = list()
        for current_sku_spec in current_sku_spec_qs:
            current_sku_spec_list.append(current_sku_spec.option_id)

        # 创建规格容器,获取全部sku规格id，并赋值sku的选项id
        skus_all = spu.sku_set.all()
        sku_spec_dict = dict()
        for skus in skus_all:
            sku_qs = skus.specs.order_by('spec_id')
            sku_spec_list = list()
            for sku_spec in sku_qs:
                sku_spec_list.append(sku_spec.option_id)
            sku_spec_dict[tuple(sku_spec_list)] = skus.id


        spu_specs_all_qs = spu.specs.order_by('id')  # 获得全部spu规格的查询集
        for index, spu_specs in enumerate(spu_specs_all_qs):
            spu_options_all_qs = spu_specs.options.all()  # 获得全部spu的选项查询集
            copy_spec = current_sku_spec_list[:]  # 复制一份当前sku规格的选项

            spu_specs.spec_options = spu_options_all_qs  # ※核心※ 把规格下的所有选项绑定到规格对象的spec_options属性上

            for spu_option in spu_options_all_qs:
                copy_spec[index] = spu_option.id  # 将spu的选项id赋值给复制的[index]
                spu_option.sku_id = sku_spec_dict.get(tuple(copy_spec))  # 给每个选项对象绑定下他sku_id属性






        context = {
            'categories': get_categories(),  # 商品分类展示
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航
            'sku': sku,
            'spu': spu,
            'category': category,
            'spec_qs': spu_specs_all_qs

        }
        return render(request, 'detail.html', context)


class DetailVisitView(View):
    """商品类别每日访问量统计"""

    def post(self, request, category_id):

        try:
            # 校验category_id 是否真实存在
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('商品类别不存在')

        # 获取当前日期
        today_date = timezone.localdate()
        try:

            # 查询当前类别今天没有没统计过  # 注意不要写成data了
            count_data = GoodsVisitCount.objects.get(category=category, date=today_date)
        except GoodsVisitCount.DoesNotExist:
            # 如果当前类别今天是第一次来统计,就创建一个新记录,并给它指定是统计那一个类别
            count_data = GoodsVisitCount(
                category=category

            )

        count_data.count += 1  # 累加浏览量
        count_data.save()


        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': "ok"})