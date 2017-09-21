#!/usr/bin/env python
# encoding: utf-8


from flask import request
from flask_wechatpy.component import Component

from app import app

try:
    app.config.from_object('wechat_config')
except ImportError:
    app.config.from_object('example_config')

# wechat
wechat = Component(app=app)


# what's that...
app.config['DEBUG'] = True
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route('/component/call')
@wechat.component_authcall('component_authcallback')
def component_authcall():
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
    return 'success'


@app.route('/mp/<appid>/notify', methods=['GET', 'POST'])
@wechat.component_mp_notify()
def mpcallback(appid):
    message = request.wechat_msg.get('component_mp_notify')
    return 'I got your "{}". --powered by wechatpydemo.'.format(message)


if __name__ == '__main__':
    app.run()
