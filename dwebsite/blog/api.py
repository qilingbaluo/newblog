from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User, Group, Permission, ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # django的分页器
from blog.models import Article, Userinfo, Lanmu, Pinglun,Favourite,Like,PayOrder
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import requests
import datetime
import base64
import json


hostUrl = 'https://www.wangblog.club/'


# 鉴权
@api_view(['POST'])
def dweb_checkPerm(request):
    # print(request.POST)
    token = request.POST['token']
    content_type = request.POST['contentType']
    permissions = json.loads(request.POST['permissions'])

    # print(token)
    # print(content_type)
    # print(permissions[0])
    user_token = Token.objects.filter(key=token)
    if user_token:
        user = user_token[0].user
        print(user)
        for p in permissions:
            app_str = content_type.split('_')[0]
            print(app_str)
            model_str = content_type.split('_')[1]
            print(model_str)
            print(content_type)
            perm_str = app_str + '.' + p + '_'+model_str
            print(perm_str)
            check = user.has_perm(perm_str)
            # print(check)
            if check == False:
                return Response('noperm')
    else:
        return Response('nologin')

    return Response('ok')


# 登录
@api_view(['POST'])
def dweb_login(request):
    username = request.POST['username']
    password = request.POST['password']
# 登录逻辑
    user = User.objects.filter(username=username)
    if user:
        checkPwd = check_password(password, user[0].password)
        if checkPwd:
            userinfo = Userinfo.objects.get_or_create(belong=user[0])
            userinfo = Userinfo.objects.get(belong=user[0])
            token = Token.objects.get_or_create(user=user[0])
            token = Token.objects.get(user=user[0])
        else:
            return Response('pwderr')
    else:
        return Response('none')

    userinfo_data = {
        'token': token.key,
        'nickName': userinfo.nickName,
        'headImg': userinfo.headImg,
    }
    return Response(userinfo_data)

# 注册


@api_view(['POST'])
def dweb_register(request):
    username = request.POST['username']
    password = request.POST['password']
    password2 = request.POST['password2']
# 注册逻辑
    user = User.objects.filter(username=username)
    if user:
        return Response('repeat')
    else:
        new_password = make_password(password, username)
        newUser = User(username=username, password=new_password)
        newUser.save()

    token = Token.objects.get_or_create(user=newUser)
    token = Token.objects.get(user=newUser)
    userinfo = Userinfo.objects.get_or_create(belong=newUser)
    userinfo = Userinfo.objects.get(belong=newUser)
    userinfo_data = {
        'token': token.key,
        'nickName': userinfo.nickName,
        'headImg': userinfo.headImg,
    }

    return Response(userinfo_data)


# 自动登录
@api_view(['POST'])
def dweb_autoLogin(request):
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)
    if user_token:
        userinfo = Userinfo.objects.get(belong=user_token[0].user)
        userinfo_data = {
            'token': token,
            'nickName': userinfo.nickName,
            'headImg': userinfo.headImg
        }
        return Response(userinfo_data)
    else:
        return Response('tokenTimeout')

# 登出


@api_view(['POST'])
def dweb_logout(request):
    token = request.POST['token']
    user_token = Token.objects.get(key=token)
    user_token.delete()
    return Response('logout')

# 文章查看


@api_view(['GET'])
def articleData(request):
    article_id = request.GET['article_id']
    article = Article.objects.get(id=article_id)
    article_data = {
        "title": article.title,
        "cover": article.cover,
        "content": article.content,
        "describe": article.describe,
        "nickName": article.belong.username,
        "lanmu": "",
        "pre_id": 0,
        "next_id": 0,
    }
    pre_data = Article.objects.filter(id__lt=article_id)
    if pre_data:
        article_data["pre_id"] = pre_data.last().id
    # print(pre_data)
    next_data = Article.objects.filter(id__gt=article_id)
    if next_data:
        article_data["next_id"] = next_data.first().id
    # print(next_data)
    if article.belong_lanmu:
        article_data["lanmu"] = article.belong_lanmu.name
    return Response(article_data)


# 文章发布
@api_view(['POST', 'PUT'])
def add_article(request):
    if request.method == "PUT":
        token = request.POST['token']
        permList = [
            'blog.change_article',
        ]
        checkUser = userLoginAndPerm(token, permList)
        # print(checkUser)
        if checkUser != 'perm_pass':
            return Response(checkUser)

        lanmu_id = request.POST['lanmu_id']
        article_id = request.POST['article_id']

        lanmu = Lanmu.objects.get(id=lanmu_id)
        article = Article.objects.get(id=article_id)
        article.belong_lanmu = lanmu
        article.save()

        return Response('ok')

    title = request.POST['title']
    describe = request.POST['describe']
    cover = request.POST['cover']
    content = request.POST['content']
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)
    if len(user_token) == 0:
        return Response('nologin')
    if len(title) == 0:
        return Response('notitle')

    # 保存文章
    new_article = Article(title=title)
    new_article.save()

    # 解析富文本html文章
    soup = BeautifulSoup(content, 'html.parser')

    imgList = soup.find_all('img')
    # print(imgList)
    for img in range(0, len(imgList)):
        src = imgList[img]['src']
        # print(imgList[img]['src'])
        # 判断图片是远程还是本地
        if 'http://' in src or 'https://' in src:
            # print('远程图片')
            # 请求远程图片
            image = requests.get(src)
            # 转化为二进制
            image_data = Image.open(BytesIO(image.content))
            # print(image_data)
            # 设定文件名称
            # image_name = 时间 + 文章id + 图片位标
            image_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'-' + \
                str(new_article.id)+'-' + str(img)
            image_data.save("upload/" + image_name + ".png")
            new_src = hostUrl + "upload/" + image_name + ".png"
            # print(new_src)
            content = content.replace(src, new_src)
            # 封面设定
            if cover == src:
                cover = new_src
        else:
            # print('本地图片')
            image_data = base64.b64decode(src.split(',')[1])
            image_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '-' + str(new_article.id) + \
                '-' + str(img) + '.' + \
                src.split(',')[0].split('/')[1].split(';')[0]
            # print(image_name)
            image_url = os.path.join('upload', image_name).replace('\\', '/')
            with open(image_url, 'wb') as f:
                f.write(image_data)
            # print(image_url)
            new_src = hostUrl + image_url
            content = content.replace(src, new_src)
            # 封面设定
            if cover == src:
                cover = new_src

    new_article.content = content
    new_article.describe = describe
    new_article.cover = cover
    new_article.belong = user_token[0].user
    new_article.save()
    return Response('ok')


# 文章分页数据列表
@api_view(['GET'])
def articleList(request):
    page = request.GET['page']
    pageSize = request.GET['pageSize']
    lanmu = request.GET['lanmu']

    if lanmu == 'all':
        articles = Article.objects.all()
    elif lanmu == 'nobelong':
        articles = Article.objects.filter(belong_lanmu=None)
    else:
        articles = Article.objects.filter(belong_lanmu__name=lanmu)

    total = len(articles)
    paginator = Paginator(articles, pageSize)
    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)
    # print(articles)
    articles_data = []
    for a in articles:
        a_item = {
            'title': a.title,
            'cover': a.cover,
            'nickName': '',
            'id': a.id,
        }
        article_user = a.belong
        userinfo = Userinfo.objects.filter(belong=article_user)
        if userinfo[0].nickName:
            a_item['nickName'] = userinfo[0].nickName
        else:
            a_item['nickName'] = article_user.username
        articles_data.append(a_item)

    return Response({'data': articles_data, 'total': total})

    # 删除文章


@api_view(['DELETE'])
def deleteArticle(request):
    article_id = request.POST['id']
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)

    user = user_token[0].user
    user_perm = user.has_perm("blog.delete_article")
    print('文章删除权限')
    # print(user_perm)
    if user_perm == False:
        return Response('noperm')
    if len(user_token) == 0:
        return Response('onlogin')
    # print(article_id)
    article = Article.objects.get(id=article_id)
    article.delete()
    return Response('ok')

# 用户组管理


@api_view(['PUT', 'GET', 'POST', 'DELETE'])
def dweb_group(request):

    # 获取用户组列表
    if request.method == "GET":
        groups = Group.objects.all()
        group_data = []
        for g in groups:
            g_item = {
                "name": g.name
            }
            group_data.append(g_item)
        return Response(group_data)

    # 删除用户组
    if request.method == "DELETE":
        token = request.POST['token']
        permList = [
            'auth.add_user',
            'auth.delete_user',
            'auth.change_user',
            'auth.view_user',
        ]
        checkUser = userLoginAndPerm(token, permList)
        # print(checkUser)
        if checkUser != 'perm_pass':
            return Response(checkUser)

        name = request.POST['name']
        group = Group.objects.get(name=name)
        group.delete()
        return Response('ok')

    # 分配用户组
    if request.method == "POST":
        token = request.POST['token']
        permList = [
            'auth.add_user',
            'auth.delete_user',
            'auth.change_user',
            'auth.view_user',
        ]
        checkUser = userLoginAndPerm(token, permList)
        if checkUser != 'perm_pass':
            return Response(checkUser)

        group_name = request.POST['group']
        userlist_name = json.loads(request.POST['userlist'])

        group = Group.objects.get(name=group_name)

        for username in userlist_name:
            user = User.objects.get(username=username)
            # user.groups.add(group)
            group.user_set.add(user)
        return Response('ok')

    # 新建用户组
    if request.method == "PUT":
        token = request.POST['token']
        permList = [
            'auth.add_user',
            'auth.delete_user',
            'auth.change_user',
            'auth.view_user',
        ]
        checkUser = userLoginAndPerm(token, permList)
        # print(checkUser)
        if checkUser != 'perm_pass':
            return Response(checkUser)

        new_name = request.POST['new_group']
        perm_list = json.loads(request.POST['perm_list'])

        new_group = Group.objects.filter(name=new_name)
        if new_group:
            return Response('same name')
        new_group = Group.objects.create(name=new_name)

        for perm in perm_list:
            app_str = perm['content_type'].split('_')[0]
            model_str = perm['content_type'].split('_')[1]

            print(app_str)
            print(model_str)

            contentType = ContentType.objects.get(
                app_label=app_str, model=model_str)
            print(contentType)
            for method in perm['perm_methods']:
                print(method)
                codename = method + '_' + model_str
                permission = Permission.objects.get(
                    content_type=contentType, codename=codename)
                new_group.permissions.add(permission)
        return Response('ok')


# 检查用户登录与权限
def userLoginAndPerm(token, permList):
    user_token = Token.objects.filter(key=token)
    if user_token:
        user = user_token[0].user
        for perm_str in permList:
            perm_user = user.has_perm(perm_str)
            if perm_user:
                return 'perm_pass'
            else:
                return 'noperm'
    else:
        return 'nologin'

# 用户列表


@api_view(['GET'])
def dweb_userlist(request):
    user_list = User.objects.all()
    user_list_data = []
    for user in user_list:
        user_item = {
            "name": user.username
        }
        user_list_data.append(user_item)
    return Response(user_list_data)

# 栏目管理


@api_view(['PUT', 'GET', 'POST', 'DELETE'])
def dweb_lanmu(request):
    if request.method == "DELETE":
        token = request.POST['token']
        permList = [
            'blog.delete_lanmu',
        ]
        checkUser = userLoginAndPerm(token, permList)
        # print(checkUser)
        if checkUser != 'perm_pass':
            return Response(checkUser)
        lanmu_id = request.POST['id']

        lanmu = Lanmu.objects.get(id=lanmu_id)
        lanmu.delete()
        return Response('ok')

    if request.method == "GET":
        lanmu = Lanmu.objects.filter(belong=None)

        lanmu_data = loopGetLanmu(lanmu)
        return Response(lanmu_data)
    if request.method == "PUT":
        token = request.POST['token']
        permList = [
            'blog.add_lanmu',
            'blog.delete_lanmu',
            'blog.change_lanmu',
            'blog.view_lanmu',
        ]
        checkUser = userLoginAndPerm(token, permList)
        # print(checkUser)
        if checkUser != 'perm_pass':
            return Response(checkUser)

        lanmu_tree = json.loads(request.POST['lanmu_tree'])
        print(lanmu_tree)
        loopSaveLanmu(lanmu_tree, None)
    return Response('ok')

# 循环获取栏目数据


def loopGetLanmu(lanmu_list):
    lanmu_data = []
    for lanmu in lanmu_list:
        lanmu_item = {
            "id": lanmu.id,
            "label": lanmu.name,
            "children": [],
            "article_num": len(lanmu.article_lanmu.all())
        }
        children = lanmu.lanmu_children.all()
        print(lanmu)
        print(children)
        if children:
            children_data = loopGetLanmu(children)
            for c in children_data:
                lanmu_item['children'].append(c)
        lanmu_data.append(lanmu_item)
    return lanmu_data


# 循环保存栏目结构
def loopSaveLanmu(tree_data, parent_id):
    parent_lanmu = Lanmu.objects.filter(id=parent_id)
    if parent_lanmu:
        for tree in tree_data:
            saved_lanmu = Lanmu.objects.filter(id=tree['id'])
            if saved_lanmu:
                saved_lanmu[0].belong = parent_lanmu[0]
                saved_lanmu[0].save()
                if len(tree['children']) > 0:
                    loopSaveLanmu(tree['children'], saved_lanmu[0].id)
            else:
                new_lanmu = Lanmu(name=tree['label'], belong=parent_lanmu[0])
                new_lanmu.save()
                if len(tree['children']) > 0:
                    loopSaveLanmu(tree['children'], new_lanmu.id)
    else:

        for tree in tree_data:
            saved_lanmu = Lanmu.objects.filter(id=tree['id'])
            if saved_lanmu:
                saved_lanmu[0].belong = None
                saved_lanmu[0].save()
                loopSaveLanmu(tree['children'], saved_lanmu[0].id)
            else:
                new_lanmu = Lanmu(name=tree['label'])
                new_lanmu.save()
                if len(tree['children']) > 0:
                    loopSaveLanmu(tree['children'], new_lanmu.id)
    return Response('ok')

# 评论


@api_view(['GET', 'POST'])
def dwebpinglun(request):
    if request.method == "GET":
        article_id = request.GET['article_id']
        pagesize  = request.GET['pagesize']
        page = request.GET['page']
        article = Article.objects.get(id=article_id)
        pingluns = Pinglun.objects.filter(belong=article)[::-1]

        total = len(pingluns)
        paginator = Paginator(pingluns, pagesize)

        try:
            pingluns = paginator.page(page)
        except PageNotAnInteger:
            pingluns = paginator.page(1)
        except EmptyPage:
            pingluns = paginator.page(paginator.num_pages)

        pinglun_data = []
        for pinglun in pingluns:
            pinglun_item = {
                "nickName":pinglun.belong_user.username,
                "text":pinglun.text
            }
            pinglun_data.append(pinglun_item)
        return Response({"data":pinglun_data,"total":total})

    if request.method == "POST":
        token = request.POST['token']
        permList = [
            'blog.view_article',
        ]
        checkUser = userLoginAndPerm(token, permList)
        # print(checkUser)
        if checkUser != 'perm_pass':
            return Response(checkUser)

        article_id = request.POST['article_id']
        text = request.POST['text']

        article = Article.objects.get(id=article_id)
        user = Token.objects.get(key=token).user

        new_pinglun = Pinglun(belong_user=user, belong=article, text=text)
        new_pinglun.save()
    return Response('ok')

@api_view(['POST'])
def userArticleInfo(request):
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)
    if len(user_token) == 0:
        return Response('nologin')

    article_id = request.POST['article_id']
    article = Article.objects.get(id=article_id)
    user =user_token[0].user

    user_article_info = {
        "like" : False,
        "favor" : False,
        "dashang" : False
    }
    liked = Like.objects.filter(belong=article,belong_user=user)
    if liked:
        user_article_info['like']=True
    
    favored = Favourite.objects.filter(belong=article,belong_user=user)
    if favored:
        user_article_info['favor']=True

    order_list = PayOrder.objects.filter(belong=article,belong_user=user)
    for order in order_list:
        if order.status == True:
            user_article_info['dashang'] = True


    return Response(user_article_info)

# 点赞
@api_view(['POST'])
def articleLike(request):
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)    
    if len(user_token) == 0:
        return Response('nologin')

    article_id = request.POST['article_id']
    article = Article.objects.get(id=article_id)

    liked = Like.objects.filter(belong=article,belong_user=user_token[0].user)    
    if liked:
        liked[0].delete()
        return Response('ok')
    else:
        new_like = Like(belong=article,belong_user=user_token[0].user)
        new_like.save()
        return Response('ok')




# 收藏
@api_view(['POST'])
def articleFavor(request):
    token = request.POST['token']

    user_token = Token.objects.filter(key=token)    
    if len(user_token) == 0:
        return Response('nologin')
    
    article_id = request.POST['article_id'] 
    article = Article.objects.get(id=article_id)

    favored = Favourite.objects.filter(belong=article,belong_user=user_token[0].user)    

    if favored:
        favored[0].delete()
        return Response('ok')
    else:
        new_favor = Favourite(belong=article,belong_user=user_token[0].user)
        new_favor.save()
        return Response('ok')