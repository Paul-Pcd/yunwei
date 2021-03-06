# coding:utf-8

from ..Global import *
import os
import time
import random
import json
import os

import urllib
import urllib2

from ..core.ssh import Host, Pk_path
from ..core.bf import xBF

from ..models import fileobj, hosts, hostgroup, scripts

# script,SavePath='/var/tmp/',timeout=30,sudo=1,title=True,Daemon=False,shell='',pk_path=Pk_path):


def BFShell(func, hostobjs, Concurrency, shellarrtuple):
    p = xBF(None, [], bfn=Concurrency, printret=False,)
    for o in hostobjs:
        Func = getattr(o, func)
        p.append(Func, shellarrtuple)
    p.start()
    return p.dict()


def GetCmdRet(func, HostsId, group, Concurrency, timeout, shellarrtuple=(), Json=False):
    '''
    返回结果
    '''
    Random = int(time.time() * 100)
    Hostgroupselect = hostgroup.GetHostGroup()
    stime = time.time()
    HostObjs = hosts.GetHostObjs(HostsId, group)
    if not HostObjs:
        return HttpResponse(u'No [%s] IP!' % group)
    hostobjs = []
    for o in HostObjs:
        HostObj = Host(o.ip, o.port, o.user, o.password, o.sshtype, timeout)
        hostobjs.append(HostObj)
    retd = BFShell(func, hostobjs, Concurrency, shellarrtuple)
    if Json:
        return json.dumps(retd)
    table = {u'Ret_%s' %
             Random: ['alias', 'user@ip', 'group', 'usetime', 'response']}
    alias = {u'Ret_%s' % Random: [u'别名', u'用户IP地址', u'主机组', u'用时', u'执行结果']}
    thcss = ["width:80px", "width:100px",
             "width:80px", 'width:30px', ""]  # 列的样式
    T = Table(table, alias, thcss)
    from hosts import HostAttr
    HostAttrURL = MakeURL(HostAttr)
    for i, o in enumerate(HostObjs):
        ii = i + 1
        if retd.has_key(ii):
            r = retd[ii]
            s = r[1].replace('<', r'&lt;').replace('>', r'&gt;')
            s = '<font size="2" color="black">%s</font>' % s if r[
                0] == 0 else '<font size="2" color="#FF0000">%s</font>' % s
            s = s.replace('\n', '<br>')
            t = r[2]
        else:
            s = 'lost process!'
            t = 'None'
        HostAttrAjax = MakeAjaxButton(
            'a', HostAttrURL + u'?hid=%s&ip=%s' % (o.id, o.ip), o.alias, 'load', Random)
        td = [HostAttrAjax, o.ip, o.group, t, s]
        T.row_add(o.id, td, [])
    T.done()
    Hostgroupselect = hostgroup.GetHostGroup()
    etime = time.time()
    Message = u'用时: %.1f 秒' % (etime - stime)
    # button=[['a','']]
    return render_to_response('GetCmdRet.html', locals())


def GetResults(request):
    '''
    ajaxj获取返回结果
    '''
    address = GetPost(request, ['address'])
    print address
    if address:
        q = SharedProcess(address, address).Q()
        try:
            r = q.get_nowait()
        except:
            pass
        return HttpResponse(json.dumps(r))
    return HttpResponse('None')


def Publickey(request):
    '''
    RSA公钥管理
    '''
    Random = int(time.time() * 100)
    ajaxurl = request.path_info
    group, action, Selects, overwrite = GetPost(
        request, ['group', 'action', 'checkbox', 'overwrite'], [2])
    if action == "updatepublickey":
        HostsId = [x.split('__')[-1] for x in Selects if x]
        if not HostsId:
            return HttpResponse("No Hosts!")
        else:
            _overwrite = True if overwrite == '1' else False
            return GetCmdRet('SetPublicKey', HostsId, group, 50, 10, (_overwrite,))
    elif action == "updateprivatekey":
        PrivatekeyText = request.POST.get('privatekey', '')
        pass
    button = [
        [u'分发公钥', MakeURL(Publickey) + '?action=updatepublickey', 'load', u'分发公钥', 'center', ]]
    return render_to_response('Publickey.html', locals())


def RunScript(request, data=None):
    '''
    运行脚本
    '''
    if request.POST.get('script', ''):
        return Interface(request)
    from .scripts import ScriptUL
    Hostgroupselect = hostgroup.GetHostGroup()
    Random = int(time.time() * 100)
    scriptul = ScriptUL(Random)
    InterfaceURL = MakeURL(RunScript)
    return render_to_response('RunScript.html', locals())


def RunCmd(request, data=None):  # 运行命令
    '''
    执行命令
    '''
    if request.POST.get('CMD', ''):
        return Interface(request)
    Hostgroupselect = hostgroup.GetHostGroup()
    Random = int(time.time() * 100)
    InterfaceURL = MakeURL(RunCmd)
    return render_to_response('RunCmd.html', locals())


def Interface(request):
    '''
    控制接口
    '''
    # 必要的参数
    Hid, Ip, HostsId, Group, CMD, Script, TimeOut, Concurrency, SshTitle, Scripttype, Daemon, Retjson = GetPost(
        request,
        ['hid', 'ip', 'checkbox', 'SelectHostGroup', 'CMD', 'script', 'cmdtimeout', 'concurrency', 'sshtitle', 'scripttype', 'daemon', 'retjson'], [2])
    if request.method == "POST":
        Concurrency = Concurrency or 0
        TimeOut = TimeOut or 30
        #SshTitle=False if SshTitle=="0" else True
        SshTitle = True if SshTitle == "1" else False
        Daemon = True if Daemon == "1" else False
        HostsId = HostsId if isinstance(HostsId, list) else [HostsId]
        HostsId = [x.split('__')[-1]
                   for x in HostsId if x] if not Hid else [Hid]
        if not HostsId and not Group:
            return HttpResponse("No Hosts!")
        if CMD:
            return HttpResponse(GetCmdRet('RunCMD', HostsId, Group, Concurrency, TimeOut, (SshTitle, CMD)), Retjson)
        elif Script:
            ScriptAbsPath = scripts.GetScriptPath(Script, TmpScript=True)
            return HttpResponse(GetCmdRet('RunScript', HostsId, Group, Concurrency, TimeOut, (SshTitle, ScriptAbsPath, '', Daemon, Scripttype), Retjson))
    return HttpResponse('error!')
