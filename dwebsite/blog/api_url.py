from django.urls import path
from blog import api,payapi

urlpatterns = [
    # 文章发布
    path('add-article/',api.add_article),
    # 文章查看
    path('article-data/',api.articleData),
    # 用户管理
        # 登录
    path('dweb-login/',api.dweb_login),
        # 注册
    path('dweb-register/',api.dweb_register),
    # 自动登录
    path('auto-login/',api.dweb_autoLogin),
    # 登出
    path('dweb-logout/',api.dweb_logout),
    # 文章列表
    path('article-list/',api.articleList),
    # 文章删除
    path('delete-article/',api.deleteArticle),
    # 鉴权
    path('dweb-checkperm/',api.dweb_checkPerm),
    # 用户列表
    path('dweb-userlist/',api.dweb_userlist),
    # 用户组
    path('dweb-group/',api.dweb_group),
    # 栏目管理
    path('dweb-lanmu/',api.dweb_lanmu),
    # 文章评论
    path('pinglun/',api.dwebpinglun),
    # 文章用户交互 
    path('user-article-info/',api.userArticleInfo),
    # 点赞
    path('article-like/',api.articleLike),
    # 收藏
    path('article-favor/',api.articleFavor),
    # 支付功能
    path('get-alipay-url/',payapi.getAlipayUrl)
]