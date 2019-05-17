from django.shortcuts import render
from django.conf import settings
from users.models import User
from django import http
from django.contrib.auth import authenticate, login
from django.urls import reverse

import urllib, json

from .models import OAuthGithub



# Create your views here.

GITHUB_CLIENTID = settings.GITHUB_CLIENTID
GITHUB_CLIENTSECRET = settings.GITHUB_CLIENTSECRET
GITHUB_CALLBACK = settings.GITHUB_CALLBACK
GITHUB_AUTHORIZE_URL = settings.GITHUB_AUTHORIZE_URL


def _get_refer_url(request):
    refer_url = request.META.get('HTTP_REFER',
    '/')
    host = request.META['HTTP_HOST']
    if refer_url.startswith('http') and host not in refer_url:
        refer_url = '/index'
    return refer_url

# 第一步: 请求github第三方登录
def githhub_login(request):
    data = {
        'client_id': GITHUB_CLIENTID,
        'client_secret': GITHUB_CLIENTSECRET,
        'redirect_uri': GITHUB_CALLBACK,
        'state': _get_refer_url(request),
    }
    github_auth_url = '%s?%s' % (GITHUB_AUTHORIZE_URL,urllib.parse.urlencode(data))
    print('git_hub_auth_url',github_auth_url)
    return http.HttpResponseRedirect(github_auth_url)

# github认证处理
def github_auth(request):
    template_html = 'account/login.html'


    if 'code' not in request.GET:
        return render(request,template_html)

    code = request.GET.get('code')

    # 第二步
    # 将得到的code，通过下面的url请求得到access_token
    url = 'https://github.com/login/oauth/access_token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': GITHUB_CLIENTID,
        'client_secret': GITHUB_CLIENTSECRET,
        'code': code,
        'redirect_uri': GITHUB_CALLBACK,
    }

    data = urllib.parse.urlencode(data)

    # 请求参数需要bytes类型
    binary_data = data.encode('utf-8')
    print('data:', data)

    # 设置请求返回的数据类型
    headers={'Accept': 'application/json'}
    req = urllib.request.Request(url, binary_data,headers)
    print('req:', req)
    response = urllib.request.urlopen(req)

    # json是str类型的，将bytes转成str
    result = response.decode('ascii')
    result = json.loads(result)
    access_token = result['access_token']
    # print('access_token:', access_token)

    url = 'https://api.github.com/user?access_token=%s'% (access_token)
    response = urllib.request.urlopen(url)
    html = response.read()
    html = html.decode('ascii')
    data = json.loads(html)
    username = data['name']
    # print('username:', username)
    password = '111111'

    # 如果不存在username，则创建
    try:
        user1 = User.objects.get(username=username)
    except:
        user2 = User.objects.create_user(username=username,
        password=password)
        user2.save()
        profile = OAuthGithub.objects.create(user=user2)
        profile.save()

    # 登陆认证
    user = authenticate(username=username,
    password=password)
    login(request, user)
    return http.HttpResponseRedirect(reverse('index'))