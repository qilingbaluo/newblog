from alipay.aop.api.AlipayClientConfig import AlipayClientConfig #客户端配置
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient #默认客户端类
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel #网络支付模型
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest #网络支付请求数据
from alipay.aop.api.domain.SettleInfo import SettleInfo
from alipay.aop.api.util.SignatureUtils import verify_with_rsa #解密

from dwebsite import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from blog.models import Article,PayOrder
import datetime
import random




@api_view(['POST'])
def getAlipayUrl(request):
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)    
    if len(user_token) == 0:
        return Response('nologin')

    user = user_token[0].user
    article_id = request.POST['article_id']
    article = Article.objects.get(id=article_id)

    nowtime = datetime.datetime.now()
    new_payorder = PayOrder(belong=article,belong_user=user)
    new_payorder.order = str(nowtime.year) + str(random.randrange(10000000,99999999))
    # print(new_payorder.order)
    new_payorder.price = '9.9'
    # new_payorder.save()


    alipay_client_config = AlipayClientConfig()
    alipay_client_config.server_url = settings.ALIPAY_URL
    alipay_client_config.app_id = settings.ALIPAY_APPID
    alipay_client_config.app_private_key = settings.APP_PRIVATE_KEY
    alipay_client_config.alipay_public_key = settings.ALIPAY_PUBLIC_KEY



    client = DefaultAlipayClient(alipay_client_config=alipay_client_config)
    model = AlipayTradePagePayModel()
    model.out_trade_no = new_payorder.order
    model.total_amount = new_payorder.price
    model.subject = "打赏订单:"+new_payorder.order+'/'+new_payorder.price+'元'
    model.product_code = 'FAST_INSTANT_TRADE_PAY'
    model.timeout_express = '5m'


    # 发送请求
    pay_request = AlipayTradePagePayRequest(biz_model=model)
    pay_request.notify_url = settings.ALIPAY_NOTIFY_URL
    pay_request.return_url = settings.ALITAY_RETURN_URL
    response = client.page_execute(pay_request,http_method='GET')
    print(response)

    pay_link = response
    return Response({'pay_link':pay_link})