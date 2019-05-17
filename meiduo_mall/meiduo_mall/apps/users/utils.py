from django.contrib.auth.backends import ModelBackend
from django.conf import settings, global_settings


from re import match
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData

from .models import User



# 识别账号是用户名还是手机号
def get_user_by_account(account):
    try:
        if match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:  # get 查询单一结果，如果不存在会抛出模型类.DoesNotExist异常
        return None  # 因下面要么有数据要么就是None
    else:
        return user


# 重写authenticate认证的方法，添加mobile和username当用户名
class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        # 校验密码是否正确
        if user and user.check_password(password):  # 小技巧，判断的先后顺序
            return user


class EmailSerializer(object):
    """邮箱信息加密与解密"""
    @staticmethod
    def generate_email_signature(user):
        # 将用户id和email信息进行加密
        serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600 * 24)
        data = {'user_id': user.id, 'email': user.email}
        serializer_url = serializer.dumps(data).decode()
        # 拼接路由
        email_serializer_url = settings.EMAIL_VERIFY_URL + "?token=" + serializer_url

        return email_serializer_url


    @staticmethod
    def check_email_signature(data_serializer):
        serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600 * 24)
        try:
            data = serializer.loads(data_serializer)
        except BadData:
            return None
        else:
            email = data.get('email')
            user_id = data.get('user_id')
            try:
                user = User.objects.get(email=email, id=user_id)
            except User.DoesNotExist:
                return None
            return user


