<template>
    <div>
        <BreadMenu :page_name="article_data.title" :lanmu="article_data.lanmu"></BreadMenu>
        <!-- 文章内容 -->
        <el-row>
            <el-col :Xs="24" :lg="16">
                <div class="body dweb">
                    <div class="header">
                        {{ article_data.title }}
                    </div>
                </div>
                <div class="body dweb">
                    <div class="dweb">
                        {{ article_data.describe }}
                    </div>
                </div>
                <div class="body dweb">
                    <div class="article-content" v-html="article_data.content">
                    </div>
                    <div class="clear">
                    </div>
                </div>
                <div class="body dweb">
                    <el-button v-if="article_data.pre_id==0" @click="toOtherPage(article_data.pre_id)" type="info"
                        plain>上一篇</el-button>
                    <el-button v-else @click="toOtherPage(article_data.pre_id)" type="success" plain>上一篇</el-button>
                    <el-button v-if="article_data.next_id==0" @click="toOtherPage(article_data.next_id)" type="info"
                        plain>下一篇</el-button>
                    <el-button v-else @click="toOtherPage(article_data.next_id)" type="success" plain>下一篇</el-button>
                </div>
            </el-col>
            <el-col :xs="24" :lg="8">
                <div class="body dweb">
                    <el-image :src="article_data.cover" :fit="'cover'">

                    </el-image>
                    <div class="body dweb like-btn">
                        <!-- 点赞收藏打赏 -->
                        <el-row>
                            <!-- 点赞 -->
                            <el-col :span="8">
                                <i v-if="user_article_info.like" class="iconfont icon-dianzan" style="color: #fc5959;"
                                    @click="toLike()"></i>
                                <i v-else class="iconfont icon-dianzan" @click="toLike()"></i>
                            </el-col>
                            <!-- 收藏 -->
                            <el-col :span="8">
                                <i v-if="user_article_info.favor" class="iconfont icon-shoucang" style="color: #ffc815;"
                                    @click="toFavor()"></i>
                                <i v-else class="iconfont icon-shoucang" @click="toFavor()"></i>
                            </el-col>
                            <!-- 打赏 -->
                            <el-col :span="8">
                                <i @click="toDashang()" v-if="user_article_info.dashang" class="iconfont icon-dashang"
                                    style="color: #ffc815;"></i>
                                <i @click="toDashang()" v-else class="iconfont icon-dashang"></i>
                            </el-col>
                        </el-row>
                    </div>
                    <!-- 评论列表 -->
                    <div class="body dweb">
                        <div v-for="(item,index) in pinglun_data" :key="index" class="body dweb pinglun-item">
                            {{ item.nickName }} 说
                            <el-divider></el-divider>
                            {{ item.text }}
                        </div>
                    </div>
                    <!-- 分页器 -->
                    <div class="dweb" style="margin-top: 7px;">
                        <el-pagination small :pager-count="5" background layout="prev, pager, next"
                            :total="pinglu_total" :page-size="pinglun_pageSize" @current-change="pinglun_currentChange">
                        </el-pagination>
                    </div>
                    <!-- 评论 -->
                    <div class="body dweb">
                        <el-input type="textarea" :maxlength="120" :rows="2" placeholder="请输入内容" v-model="new_pinglun">
                        </el-input>
                        <el-button @click="saveNewPinglun()" type="success">发表评论</el-button>
                    </div>
                    <div>
                        <a id="payLink" href="https://www.alipay.com/" target="_blank"></a>
                    </div>
                </div>
            </el-col>
        </el-row>
    </div>
</template>

<script>
    import BreadMenu from '../components/BreadMenu'
    import axios from 'axios'
    import Qs from 'qs'
    export default {
        data() {
            return {
                article_id: this.$route.query.id,
                article_data: {},
                // 评论
                new_pinglun: "",
                pinglu_total: 100,
                pinglun_pageSize: 4,
                pinglun_data: [],
                user_article_info: {},
            }
        },
        components: {
            BreadMenu
        },
        watch: {
            $route(to) {
                this.article_id = to.query.id
                this.getArticleData(to.query.id)
                this.getAllPinglun(1, this.pinglun_pageSize)
                this.getUserArticleInfo()
            }
        },
        mounted() {
            this.getArticleData(this.article_id)
            this.getAllPinglun(1, this.pinglun_pageSize)
            this.getUserArticleInfo()
        },
        methods: {
            // 点赞
            toLike() {
                axios({
                    url: "https://www.wangblog.club/api/article-like/",
                    method: "post",
                    data: Qs.stringify({
                        token: this.$store.getters.isnotUserlogin,
                        article_id: this.article_id,
                    }),
                }).then((res) => {
                    if (res.data == 'nologin') {
                        alert('请登录')
                        return
                    }
                    if (res.data == "ok") {
                        this.getUserArticleInfo()
                    }

                })
            },
            // 收藏
            toFavor() {
                axios({
                    url: "https://www.wangblog.club/api/article-favor/",
                    method: "post",
                    data: Qs.stringify({
                        token: this.$store.getters.isnotUserlogin,
                        article_id: this.article_id,
                    }),
                }).then((res) => {
                    if (res.data == 'nologin') {
                        alert('请登录')
                        return
                    }
                    if (res.data == "ok") {
                        this.getUserArticleInfo()
                    }
                })
            },
            // 打赏
            toDashang() {
                axios({
                    method: 'post',
                    url: "https://www.wangblog.club/api/get-alipay-url/",
                    data: Qs.stringify({
                        token: this.$store.getters.isnotUserlogin,
                        article_id: this.article_id
                    })
                }).then((res) => {
                    let link = document.getElementById('payLink')
                    link.herf = res.data.pay_link
                    link.click()
                    if (confirm('支付完成了吗？')) {
                        console.log('ok')
                    }
                })

            },
            // 获取互动信息
            getUserArticleInfo() {
                let token = this.$store.getters.isnotUserlogin;
                if (token) {
                    axios({
                        url: "https://www.wangblog.club/api/user-article-info/",
                        method: "post",
                        data: Qs.stringify({
                            token: token,
                            article_id: this.article_id,
                        }),
                    }).then((res) => {
                        console.log(res.data)
                        this.user_article_info = res.data;
                    });
                }
            },
            // 获取评论数据
            getAllPinglun(page, pagesize) {
                axios({
                    method: 'get',
                    url: "https://www.wangblog.club/api/pinglun/",
                    params: {
                        page,
                        pagesize,
                        article_id: this.article_id,

                    }
                }).then((res) => {
                    this.pinglun_data = res.data.data
                    // console.log(res.data.data)
                    this.pinglu_total = res.data.total
                })
            },
            // 发表评论
            saveNewPinglun() {
                if (this.new_pinglun.length == 0) {
                    alert('请输入评论')
                    return
                }
                axios({
                    method: 'post',
                    url: "https://www.wangblog.club/api/pinglun/",
                    data: Qs.stringify({
                        token: this.$store.getters.isnotUserlogin,
                        article_id: this.article_id,
                        text: this.new_pinglun
                    })
                }).then((res) => {
                    console.log(res)
                    if (res.data == 'onlogin') {
                        alert('用户登录信息错误')
                        return;
                    }
                    if (res.data == 'noperm') {
                        alert('权限不足')
                        return
                    }
                    if (res.data == 'ok') {
                        this.getAllPinglun(1, this.pinglun_pageSize)
                    }
                })
            },
            // 评论翻页
            pinglun_currentChange(page) {
                this.getAllPinglun(page, this.pinglun_pageSize);
            },
            // 跳转文章上一页下一页
            toOtherPage(id) {
                if (id == 0) {
                    alert('没有了')
                    return
                }
                this.$router.push({ path: '/article', query: { id: id } })
            },
            // 查看文章
            getArticleData(id) {
                console.log(id)
                axios({
                    method: 'get',
                    url: "https://www.wangblog.club/api/article-data",
                    //使用get方法时用params
                    params: {
                        article_id: id
                    }
                }).then((res) => {
                    // console.log(res.data)
                    this.article_data = res.data

                })
            }
        },
    }
</script>
<style scoped>
    .body.dweb {
        padding: 10px 10px;
    }

    .body.dweb .dweb {
        padding: 10px 10px;
        color: #ffffff;
        font-size: 14px;
        font-style: italic;
    }

    .like-btn {
        text-align: center;

    }

    .like-btn i {
        font-size: 30px;
        cursor: pointer;
    }

    .body.dweb .pinglun-item {
        color: #ffffff;
        font-size: 20px;
    }
</style>