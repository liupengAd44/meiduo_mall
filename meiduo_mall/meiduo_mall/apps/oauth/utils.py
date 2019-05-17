from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


class DataSerializer(object):
    @staticmethod
    def generate_data_signature(openid):
        """生成数据签名(加密)"""
        # Parame:secret_key, expires_in = None
        serializer = Serializer(settings.SECRET_KEY, expires_in=300)
        data = {'openid': openid}  # 把数据包装成字典
        openid_sign = serializer.dumps(data)  # 加密后返回的数据是bytes类型
        return openid_sign.decode()

    @staticmethod
    def check_data_signature(openid_sign):
        """签证数据签名"""

        serializer = Serializer(settings.SECRET_KEY, expires_in=300)
        try:
            data = serializer.loads(openid_sign)
        except BadData:
            return None
        else:
            return data.get('openid')