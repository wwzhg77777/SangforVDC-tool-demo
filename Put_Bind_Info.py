#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Date :   2023-03-14
# @Name :   wendr

#
# Copyright (c) 2022 wendirong.top, Inc. All Rights Reserved
#
# Licensed under the PSF License;
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
#
# Https://docs.python.org/zh-cn/3/license.html#psf-license
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
# 提交数据到VDC, 调用OpenAPI进行交互式操作
# 版本更迭以UpdateTime和Version为准
#
import ctypes
import os
import readline
import time

import win32gui

import GetOpenAPI
from LoopFunc import LoopFunc

# from rich import print as rprint

kernel32 = ctypes.WinDLL('kernel32')
hWnd = kernel32.GetConsoleWindow()
win32gui.ShowWindow(hWnd, 3)
win32gui.SetWindowText(hWnd, GetOpenAPI.PROGRAMNAME)
isDebugger = False


def outputCopyright():
    print('-*- coding: utf-8 -*-\n')
    print('Copyright (c) 2022 wendirong.top, Inc. All Rights Reserved')
    print('Licensed under the PSF License;')
    print('you may not use this file except in compliance with the License. You may obtain a copy of the License at\n')
    print('Https://docs.python.org/zh-cn/3/license.html#psf-license\n')
    print('Unless required by applicable law or agreed to in writing,')
    print('software distributed under the License is distributed on an "AS IS" BASIS,')
    print('WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.')
    print('See the License for the specific language governing permissions and limitations under the License.\n')
    print('提交数据到VDC, 调用OpenAPI进行交互式操作')
    print('版本更迭以UpdateTime和Version为准\n')
    print('Avatar : %s' % GetOpenAPI.AVATAR)
    print('E-mail : %s' % GetOpenAPI.EMAIL)
    print('CreateTime : %s' % GetOpenAPI.CREATETIME)
    print('UpdateTime : %s' % GetOpenAPI.UPDATETIME)
    print('DeviceVersion : %s' % GetOpenAPI.DEVICEVERSION)
    print('ApiVersion : %s' % GetOpenAPI.APIVERSION)
    print('#\n#\n#')


def getrolesDict():
    # 获取role_id, role_name, role_desc, role_enable
    #
    rolesDict = {}
    # str: {'role_id': int, 'role_name': str, 'role_desc': str, 'role_enable': int }
    # { 角色name : { 角色id, 角色name, 角色desc, 角色enable } }
    print('正在读取角色列表...')
    base_roles = GetOpenAPI.OpenAPITools.ret_error(myapi, 6)
    _totalCount = int(base_roles[1]['data']['total_count'])
    for v0 in base_roles[1]['data']['list']:
        ret_rolesId = GetOpenAPI.OpenAPITools.ret_error(myapi, 7, v0['id'])
        print('正在读取角色: {} '.format(v0['name']).ljust(59 - len(str(v0['name'])), '-'), '耗时: %s s' % str(ret_rolesId[2]))
        rolesDict[v0['name']] = ret_rolesId[1]['data']
        rolesDict[v0['name']]['enable'] = v0['enable']
    print('读取角色列表完成, 角色总数:%s' % _totalCount)
    return (rolesDict, _totalCount)


def getresourcesDict(rolesDict_: dict):
    # 获取rc_id, rc_grp_id
    #
    resourcesDict = {}
    # {str: {'id': int, 'name': str, 'grp_id': int, 'grp_name': str}}
    # { 资源name : { 资源id, 资源name, 资源组id, 资源组name } }
    resourcesGroup = GetOpenAPI.OpenAPITools.ret_error(myapi, 1)
    tmp_res_list = []
    tmp_res_group_info = {item0['name']: int(item0['id']) for item0 in resourcesGroup[1]['data']}
    print('正在读取资源组...')
    for k0, v0 in tmp_res_group_info.items():
        if isDebugger and k0 == '广州花都区域':
            break
        ret_res_list = GetOpenAPI.OpenAPITools.ret_error(myapi, 4, v0)
        print('正在读取资源组: {} '.format(k0).ljust(58 - len(str(k0)), '-'), '耗时: %s s' % str(ret_res_list[2]))
        tmp_res_list.append((ret_res_list, k0))  # 资源id    in tuple[1].data.resources[].id
    for item1 in tmp_res_list:
        for item2 in item1[0][1]['data']['resources']:
            _rc_name = item2['name']
            resourcesDict[_rc_name] = item2
            for v0 in rolesDict_.values():
                if ',' in v0['rc_ids'] and str(item2['id']) in v0['rc_ids'].split(','):
                    resourcesDict[_rc_name]['role_name'] = v0['name']
                    break
                elif str(item2['id']) == str(v0['rc_ids']):
                    resourcesDict[_rc_name]['role_name'] = v0['name']
                    break
                else:
                    resourcesDict[_rc_name]['role_name'] = -1
    print('读取资源组完成, 资源组总数:{0}, 资源总数:{1}'.format(len(resourcesGroup[1]['data']), len(resourcesDict.keys())))
    return (resourcesDict, len(resourcesGroup[1]['data']), len(resourcesDict.keys()))


def getresourceServers(resourcesDict_: dict):
    # 获取vm_id, vm_name, 对应vm的rc_id, rc_name
    #
    resourceServers = {}
    # {str: {'vm_id': int, 'vm_name': str, 'rc_id': int, 'rc_name': str}}
    # { 虚拟机name : { 虚拟机id, 虚拟机name, 资源id, 资源name } }
    _vmCount = 0
    print('正在读取虚拟机列表...')
    for v0 in resourcesDict_.values():
        tmp_res_ser = GetOpenAPI.OpenAPITools.ret_error(myapi, 2, v0)
        print('正在读取资源: {} 的虚拟机 '.format(v0['name']).ljust(55 - len(str(v0['name'])), '-'), '耗时: %s s' % str(tmp_res_ser[2]))
        _totalCount = int(tmp_res_ser[1]['data']['totalCount'])
        _vmCount += _totalCount
        if int(tmp_res_ser[0]) == 200 and _totalCount > 500:
            tmp_res_ser = myapi.get_resource_servers([v0['id'], 1, _totalCount + 1, 1])
        for item0 in tmp_res_ser[1]['data']['data']:  # 虚拟机name in tuple[1].data.data[].vm_name
            _rs_vm_name = (item0['vm_name']).split('_')[0] if len((item0['vm_name']).split('_')) >= 2 else item0['vm_name']
            resourceServers[_rs_vm_name] = item0
            resourceServers[_rs_vm_name]['vm_name_user'] = item0['vm_name']
            resourceServers[_rs_vm_name]['vm_name'] = _rs_vm_name
    print('读取虚拟机列表完成, 虚拟机总数:%s' % str(_vmCount))
    return (resourceServers, _vmCount)


def getusersList():
    # 获取user_id, user_name
    #
    usersList = {}
    # {str: int}
    # { 用户name : 用户id }
    print('正在读取用户列表...')
    tmp_users = GetOpenAPI.OpenAPITools.ret_error(myapi, 3)
    _totalCount = int(tmp_users[1]['data']['total_count'])
    if int(tmp_users[0]) == 200 and _totalCount > 200:
        for _page in range(_totalCount // 200 + 1):
            if isDebugger and _page == 2:
                break
            ret_users = GetOpenAPI.OpenAPITools.ret_error(myapi, 5, _page)
            print('正在读取用户 {0} - {1} '.format(_page * 200 + 1, (_page + 1) * 200).ljust(60, '-'), '耗时: %s s' % str(ret_users[2]))
            for item in ret_users[1]['data']['list']:
                usersList[item['name']] = item
    print('读取用户列表完成, 用户总数:%s' % str(_totalCount))
    return (usersList, _totalCount)


if __name__ == '__main__':
    # try:
    outputCopyright()
    time.sleep(2)
    myapi = GetOpenAPI.GetOpenAPI('https://test.vdc.xxx', 'user', 'password')

    starttime = time.time()

    _getrolesDict = getrolesDict()
    myapi.rolesDict, myapi.rolesCount = _getrolesDict[0], _getrolesDict[1]

    _getresDict = getresourcesDict(myapi.rolesDict)
    myapi.resourcesDict, myapi.resourcesCount = _getresDict[0], _getresDict[2]

    _getresServers = getresourceServers(myapi.resourcesDict)
    myapi.resourceVMDict, myapi.resourceVMCount = _getresServers[0], _getresServers[1]

    _getusersList = getusersList()
    myapi.usersDict, myapi.usersCount = _getusersList[0], _getusersList[1]

    myapi.update_VDCInfo_for_source()
    myapi.update_repairInfo()
    myapi.update_writeJson(-1)
    print('\n{wl_}完成读取数据源, 总耗时:{s_}秒{w_}'.format(s_=str(int(time.time() - starttime)),
                                                 wl_='-' * int(os.get_terminal_size()[0] / 2 - 30),
                                                 w_='-' * int(os.get_terminal_size()[0] / 2 - 10)))
    print('#\n#\n#\n加载数据源...')
    for i in range(5):
        print(5 - i)
        time.sleep(1)

    myloopfunc = LoopFunc(myapi)
    myloopfunc.loop_get_vdc_source()
    readline.parse_and_bind('tab:complete')
    readline.set_completer(myloopfunc.completer_tab)
    myloopfunc.loop_func()
    # except Exception as err:
    #     print('Program Error as err:', err)
    #     input('输入任意键按回车即退出...')
