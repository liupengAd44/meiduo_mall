from django.db import models
from meiduo_mall.utils.models import BaseModel

# Create your models here.

class OAuthGithub(BaseModel):

    # 与'users.User'关联，并创建外键   on_delete=models.CASCADE  默认的选项，级联删除，你无需显性指定它。
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')


    # openid = models.CharField(max_length=64, verbose_name='openid')

    class Meta:
        db_table = 'tb_oauth_github'
        verbose_name = 'Github用户数据'
        verbose_name_plural = verbose_name
