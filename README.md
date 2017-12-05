
# flask-wechatpy

wechat component operations using wechatpy and flask.

## 运行demo

1. 在微信开发平台 https://open.weixin.qq.com 设置参数。app要部署在有备案域名的后台。

2. 在 `example_config.py` 设置好对应参数。

3. 安装依赖 pip install -r requirements.txt。

4. 运行demo.py

5. 准备一个公众号。

6. 访问用 `@wechat.component_authcall(router_func_name)` 装饰的路由进行公众号授权。这里是 `/component/call`

7. 绑定成功后，进入公众号输入文本 **index**。


## 功能

1. 微信开H放平台的授权和验证

2. 公众号授权给开放平台

3. 授权公众号的用户消息和授权
