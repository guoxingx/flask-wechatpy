
from flask import request, redirect, url_for

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
@component.component_user_login(redirect_endpoint='wechat.mpindex')
def mpindex(appid):
    """
    application index of wechat mp.
    """
    return '''
    <h4>Hi, openid:{}</h4>
    '''.format(request.wechat_msg.get('openid'))


@wechat.route('/mp_custom/<appid>/index')
@component.component_user_login(redirect_endpoint='mp_custom_index')
def mp_custom_index(appid):

    # 保存用户在客户公众号的信息
    save_user_info()

    # 进行第二次跳转
    return redirect(url_for('mp_base_index'))


@wechat.route('/mp_base')
@component.component_user_login(redirect_endpoint='mpindex')
def mp_base_index(appid='mp_base_appid'):

    # 保存用户在mp_base的信息，并与客户公众号的信息进行关联。
    save_and_relate_user_info()

    # 返回页面
    return '''
    <h4>I see you.</h4>
    '''


def save_user_info(**kw):
    pass


def save_and_relate_user_info():
    pass
