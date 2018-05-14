
from flask import request, url_for

from .. import component
from . import wechat


@wechat.route('/component/call')
@component.component_authcall('wechat.component_authcallback')
def component_authcall():
    """
    component authorization for wechat mp.
    """
    url = request.wechat_msg.get('component_authcall_url')
    return '''
    <a href="{}">{}</a>
    '''.format(url, url)


@wechat.route('/component/callback')
@component.component_authcallback()
def component_authcallback():
    return '''
    <h4>Authorization Success.</h4>
    '''


@wechat.route('/component/notify', methods=['GET', 'POST'])
@component.component_notify()
def compcallback():
    """
    receive component ticket and unauthorization message.
    """
    return 'success'


@wechat.route('/mp/<appid>/notify', methods=['GET', 'POST'])
@component.component_mp_notify()
def mpcallback(appid):
    """
    receive authorized mp notify.

    return with wechat.news()/text()/image()/...
    """
    content = request.wechat_msg.get('component_mp_content')
    client = request.wechat_msg.get('component_client')

    if content.lower() == 'index':
        return component.news(
            title='Index Of Application.',
            description='click to visit our site.',
            image='http://ac-n8vegisj.clouddn.com/b09f095e305b85683878.JPG',
            url=request.url_root[:-1] + url_for('wechat.mpindex', appid=client.appid)
        )

    return component.text("'{}'. --powered by flask-wechat.".format(content))


@wechat.route('/mp/<appid>/index')
@component.get_user()
def mpindex(appid):
    """
    application index of wechat mp.
    """
    return '''
    <h4>Hi, openid:{}</h4>
    '''.format(request.wechat_msg.get('openid'))
