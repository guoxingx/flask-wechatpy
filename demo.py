# coding: utf-8

from flask import Flask, request, url_for
from flask_wechatpy.component import Component

app = Flask(__name__)

app.config.from_object('wechat_config')

# wechat
wechat = Component(app=app)


# what's that...
app.config['DEBUG'] = True
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route('/component/call')
@wechat.component_authcall('component_authcallback')
def component_authcall():
    """
    component authorization for wechat mp.
    """
    url = request.wechat_msg.get('component_authcall_url')
    return '''
    <a href="{}">{}</a>
    '''.format(url, url)


@app.route('/component/callback')
@wechat.component_authcallback()
def component_authcallback():
    return '''
    <h4>Authorization Success.</h4>
    '''


@app.route('/component/notify', methods=['GET', 'POST'])
@wechat.component_notify()
def compcallback():
    """
    receive component ticket and unauthorization message.
    """
    return 'success'


@app.route('/mp/<appid>/notify', methods=['GET', 'POST'])
@wechat.component_mp_notify()
def mpcallback(appid):
    """
    receive authorized mp notify.

    return with wechat.news()/text()/image()/...
    """
    content = request.wechat_msg.get('component_mp_content')
    client = request.wechat_msg.get('component_client')

    if content.lower() == 'index':
        return wechat.news(
            title='Index Of Application.',
            description='click to visit our site.',
            image='http://ac-n8vegisj.clouddn.com/b09f095e305b85683878.JPG',
            url=request.url_root[:-1] + url_for('mpindex', appid=client.appid)
        )

    return wechat.text('I got your "{}". --powered by flask-wechat.'.format(content))


@app.route('/mp/<appid>/index')
@wechat.get_user()
def mpindex(appid):
    """
    application index of wechat mp.
    """
    return '''
    <h4>Hi, openid:{}</h4>
    '''.format(request.wechat_msg.get('openid'))


if __name__ == '__main__':
    app.run(debug=True)
