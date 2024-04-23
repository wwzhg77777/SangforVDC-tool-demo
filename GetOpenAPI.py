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
import json
import os
import sys
import threading
import time

import requests
import urllib3

AVATAR = 'wwzhg77777'
EMAIL = 'ww1372247148@163.com'
CREATETIME = '2022-02-24'
UPDATETIME = '2022-03-26'
DEVICEVERSION = 'VDC 5.4.11'
APIVERSION = '0.1.6'
PROGRAMNAME = 'DesktopCloud扳手🔧'
STATIC_PASSWORD = '♂♀☺♪♫◙♂♀'

lock = threading.Lock()
# 提供给进程锁定内存
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GetOpenAPI:
    '''
    访问VDC5411的APIs接口数据
    APIs:
    get_authTokens              : 获取tokens认证密钥
    get_resourcesGroup          : 获取所有资源组
    get_resources_list          : 获取独享桌面资源
    get_resource_servers        : 获取指定资源下所有虚拟机接口
    get_userGroups              : 获取用户组列表
    get_users                   : 获取用户列表
    get_usersId                 : 获取指定用户配置
    get_bind_users_servers      : 查询用户关联的虚拟机列表
    get_servers_bind_users_list : 获取虚拟机可关联用户
    get_roles                   : 获取所有角色
    get_rolesId                 : 获取指定角色
    put_rolesId                 : 编辑角色
    put_usersId                 : 编辑用户
    put_servers_bind_users      : 虚拟机关联用户(单个)

    '''

    # Public var
    #
    programFullDir: str  # 写入程序文件的上级路径
    programFullPath: str  # 写入程序文件的最终路径
    programSourceFilePath: str  # 程序生成的source文件存放路径
    checkFilePath: str  # 程序生成的check文件存放路径
    readMeFile: str  # Readme.md文件路径
    writeDate: int  # 以10位时间戳命名的文件夹路径
    jsonHeaders = {'Content-Type': 'application/json', 'Connection': 'close'}
    vdcSource = {}
    # 存储VDC数据源
    resourcesDict: dict
    # 存储资源对应的id、组id    { 资源name : { 资源id, 资源name, 资源组id } }       str: {'id': int, 'name': str, 'grp_id': int }
    resourceVMDict: dict
    # 存储虚拟机对应的id、资源id    { 虚拟机name : { 虚拟机id, 虚拟机name, 资源id, 资源name } }     str: {'vm_id': int, 'vm_name': str, 'rc_id': int, 'rc_name': str }
    usersDict: dict
    # 存储用户对应的id、名称    { 用户name : 用户id }   { str: int }
    rolesDict: dict
    # 存储角色对应的id、名称、描述、启用状态  { 角色name : { 角色id, 角色name, 角色desc, 角色enable } }       str: {'role_id': int, 'role_name': str, 'role_desc': str, 'role_enable': int }
    resourcesCount: int
    # 资源总数
    resourceVMCount: int
    # 虚拟机总数
    usersCount: int
    # 用户总数
    rolesCount: int
    # 角色总数
    bindCount: int
    # 统计: LDAP里已分配虚拟机的用户
    noBindRoleFile = '用户未关联角色'
    noBindRoleDict = {}
    # 统计: 关联了虚拟机但未关联角色的用户列表 (VDC数据源)
    idleVMFile = '闲置虚拟机列表'
    idleVMDict = {}
    # 统计: 闲置的虚拟机列表 (VDC数据源)
    lossVmUserFile = '用户可能丢失虚拟机关联'
    lossVMUserDict = {}
    # 统计: 曾经关联过虚拟机的用户列表 (VDC数据源)
    userBindMultVMFile = '用户关联多个资源的虚拟机'
    userBindMultVMDict = {}
    # 统计: 用户关联了多个虚拟机 或 用户曾经关联过多个虚拟机 (VDC数据源)

    # Private var
    #
    __url: str
    # 访问VDC的api接口的url
    __name: str
    # 传参登录VDC的name
    __password: str
    # 传参登录VDC的password
    __auth_token: str

    # 初始api接口自动存档的tokens认证密钥
    def __init__(self, url_: str, name_: str, password_: str):
        '''
        构造函数:
        Load    :   csvfile, url, name, password
        初始化api接口调用对象, 输入虚拟机信息的CSV文件绝对路径
        AuthLoad    :  [所属资源]     [关联用户]      [虚拟机名称]
                           ⬇⬇               ⬇⬇             ⬇⬇
        AutoSet     :  [rc_name]        [user_name]     [vm_name]
        '''
        self.write_base_path()
        self.__url = url_
        self.__name = name_
        self.__password = password_
        print('\n正在读取VDC的OpenAPI状态...')
        self.__auth_token = self.get_authTokens()[1]['data']['token']['auth_token']
        print('\nOpenAPI已授权, 当前接入用户: %s' % self.__name)
        print('#\n#\n#')

    def write_readme(self):
        with open(self.readMeFile, 'w', encoding='utf-8') as readme:
            readme.write('-*- coding: utf-8 -*-\n')
            readme.write('Copyright (c) 2022 wendirong.top, Inc. All Rights Reserved\n')
            readme.write('Licensed under the PSF License;\n')
            readme.write('you may not use this file except in compliance with the License. You may obtain a copy of the License at\n\n')
            readme.write('Https://docs.python.org/zh-cn/3/license.html#psf-license\n\n')
            readme.write('Unless required by applicable law or agreed to in writing,\n')
            readme.write('software distributed under the License is distributed on an "AS IS" BASIS,\n')
            readme.write('WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n')
            readme.write('See the License for the specific language governing permissions and limitations under the License.\n\n')
            readme.write('提交数据到VDC, 调用OpenAPI进行交互式操作\n')
            readme.write('版本更迭以UpdateTime和Version为准\n\n')
            readme.write('Avatar : %s\n' % AVATAR)
            readme.write('E-mail : %s\n' % EMAIL)
            readme.write('CreateTime : %s\n' % CREATETIME)
            readme.write('UpdateTime : %s\n' % UPDATETIME)
            readme.write('DeviceVersion : %s\n' % DEVICEVERSION)
            readme.write('ApiVersion : %s\n' % APIVERSION)
            readme.write('#\n#\n')
            readme.write("For '%s'" % PROGRAMNAME)

    def write_base_path(self):
        '''
        写入log和csv的文件夹, 以当前时间戳为文件夹名称(10位)
        '''
        self.writeDate = time.strftime("%Y-%m-%d %H", time.localtime(time.time()))
        self.programFullDir = os.path.join(os.getcwd(), os.path.splitext(os.path.basename(sys.argv[0]))[0])
        self.programFullPath = OpenAPITools.loop_dir(os.path.join(self.programFullDir, '%s.NODE.1' % str(self.writeDate)))
        self.programSourceFilePath = os.path.join(self.programFullPath, 'SourceFiles')
        self.checkFilePath = os.path.join(self.programFullPath, 'CheckInfoFiles')
        self.readMeFile = os.path.join(self.programFullPath, 'Readme.md')
        print('程序执行目录: %s' % os.getcwd())
        if not os.path.exists(self.programFullDir):
            os.mkdir(self.programFullDir)
        print('\n执行创建目录: %s' % self.programFullPath)
        print('\n执行创建目录: %s' % self.programSourceFilePath)
        print('\n执行创建目录: %s' % self.checkFilePath)
        print('\n执行创建Readme.md文件: %s' % self.readMeFile)
        os.mkdir(self.programFullPath)
        os.mkdir(self.programSourceFilePath)
        os.mkdir(self.checkFilePath)
        self.write_readme()

    def get_authTokens(self, uri_: str = '/v1/auth/tokens'):
        '''
        api     : 获取tokens认证密钥
        url     : POST /v1/auth/tokens
        Load    : uri, self.name, self.password
        return  : (status_code:int, json:dict, onetime:time)
        notes   : Auth_Token    in json.data.token.auth_token
        '''
        result = ''
        _body = {'auth': {'name': self.__name, 'password': self.__password}}
        _headers = GetOpenAPI.jsonHeaders
        try:
            _sT = time.time()
            result = requests.post(url=self.__url + uri_, json=_body, headers=_headers, verify=False)
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT)

    def set_headers(self):
        '''
        补齐headers参数的Auth-Token字段
        返回 json + tokens 的headers请求头
        '''
        result = GetOpenAPI.jsonHeaders
        self.__auth_token = self.get_authTokens()[1]['data']['token']['auth_token']
        result['Auth-Token'] = self.__auth_token
        return result

    def get_vm_info_count(self):
        '''
        获取资源、虚拟机、用户、角色的总数
        '''
        return (self.resourcesCount, self.resourceVMCount, self.usersCount, self.rolesCount)

    def get_vdcSource(self):
        '''
        获取VDC系统上的数据源:
        [
            {
                'rc_name': str,
                'rc_id': int,
                'user_name': str,
                'user_id': int,
                'vm_name': str,
                'vm_id': int,
                'role_names':str,
                ...
            }
            ...
        ]
        '''
        return self.vdcSource

    def get_resourcesGroup(self, uri_: str = '/v1/resources_group'):
        '''
        api     : 获取所有资源组
        url     : GET /v1/resources_group
        Load    : auth_token, uri
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 资源组id  in json.data[].id
        notes   : 资源组name  in json.data[].name
        '''
        result = ''
        _params = ''
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_resources_list(self, args_: int, uri_: str = '/v1/resources/list/'):
        '''
        api     : 获取独享桌面资源
        url     : GET /v1/resources/list/:group_id
        Load    : auth_token, uri + args:[group_id(path)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 资源id    in json.data.resources[].id
        notes   : 资源name    in json.data.resources[].name
        '''
        result = ''
        _params = ''
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_ + str(args_), params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_ + str(args_), params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_resource_servers(self, args_: list, uri_: str = '/v1/resource/servers'):
        '''
        api     : 获取指定资源下所有虚拟机接口
        url     : GET /v1/resource/servers?rcid=&page=&page_size=&status=
        Load    : auth_token, uri + args:[rcid(int), page(int), page_size(int), status(int)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 虚拟机id      in json.data.data[]._id
        notes   : 虚拟机name    in json.data.data[].vm_name
        notes   : 所属资源id    in json.data.data[].rc_id
        notes   : 所属资源name  in json.data.data[].rc_name
        notes   : 关联用户名    in json.data.data[].apply_user
        '''
        result = ''
        _params = {'rcid': int(args_[0]), 'page': int(args_[1]), 'page_size': int(args_[2]), 'status': int(args_[3])}
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_userGroups(self, args_: list, uri_: str = '/v1/user_groups'):
        '''
        api     : 获取用户组列表
        url     : GET /v1/user_groups?group_id=&page_size=&page=
        Load    : auth_token, uri + args:[group_id(int), page(int), page_size(int)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : group_id=-100为一级用户组
        notes   : 用户组id      in json.data.list[].id
        notes   : 用户组name    in json.data.list[].name
        notes   : 所属用户组id  in json.data.list[].group_id
        '''
        result = ''
        _params = {'group_id': int(args_[0]), 'page': int(args_[1]), 'page_size': int(args_[2])}
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_users(self, args_: list, uri_: str = '/v1/users'):
        '''
        api     : 获取用户列表
        url     : GET /v1/users?group_id=&page_size=&page=
        Load    : auth_token, uri + args:[group_id(int), page(int), page_size(int,max:200)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : group_id=-100为一级用户组
        notes   : 用户id            in json.data.list[].id
        notes   : 用户name          in json.data.list[].name
        notes   : 所属用户组id      in json.data.list[].group_id
        notes   : 关联的角色名name  in json.data.list[].role_names
        notes   : 是否启用          in json.data.list[].enable
        notes   : 过期时间          in json.data.list[].expire
        '''
        try:
            if int(args_[2]) > 200:
                return (401, 'page_size exceed 200')
        except Exception as e:
            return (402, e)
        result = ''
        _params = {'group_id': int(args_[0]), 'page': int(args_[1]), 'page_size': int(args_[2])}
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (403, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_usersId(self, args_, uri_: str = '/v1/users/'):
        '''
        api     : 获取指定用户配置
        url     : GET /v1/users/:user_id
        Load    : auth_token, uri + args:[user_id(path)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : group_id=-100为一级用户组
        notes   : 用户id            in json.data.id
        notes   : 用户name          in json.data.name
        notes   : 用户note          in json.data.note
        notes   : 所属用户组id      in json.data.group_id
        notes   : 关联的角色列表    in json.data.roles
        notes   : 是否启用          in json.data.enable
        notes   : 过期时间          in json.data.expire
        '''
        result = ''
        _params = ''
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_ + str(args_), params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_ + str(args_), params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (403, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_bind_users_servers(self, args_: list, uri_: str = '/v1/bind_users/servers'):
        '''
        api     : 查询用户关联的虚拟机列表
        url     : GET /v1/bind_users/servers?user_name=
        Load    : auth_token, uri + args:[user_name(str)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 虚拟机id      in json.data[].vm_id
        notes   : 虚拟机name    in json.data[].vm_name
        '''
        result = ''
        _params = {'user_name': str(args_[0])}
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_servers_bind_users_list(self, args_: list, uri_: str = '/v1/servers/bind_users/list'):
        '''
        api     : 获取虚拟机可关联用户
        url     : GET /v1/servers/bind_users/list?rcid=&group_id=&page=&page_size=
        Load    : auth_token, uri + args:[rcid(int), group_id(int), page(int), page_size(int)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 用户id      in json.data.data[]._id
        notes   : 用户name    in json.data.data[].name
        '''
        result = ''
        print('args_:', args_)
        _params = {'rcid': int(args_[0]), 'group_id': int(args_[1]), 'page': int(args_[2]), 'page_size': int(args_[3])}
        print('_params:', _params)
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_roles(self, args_: list, uri_: str = '/v1/roles'):
        '''
        api     : 获取所有角色
        url     : GET /v1/roles?page=&page_size=
        Load    : auth_token, uri + args:[page(int), page_size(int)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 角色id      in json.data.list[].id
        notes   : 角色name    in json.data.list[].name
        notes   : 角色描述    in json.data.list[].desc
        notes   : 是否启用    in json.data.list[].enable
        notes   : 角色总数    in json.data.total_count
        '''
        result = ''
        _params = {'page': int(args_[0]), 'page_size': int(args_[1])}
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_, params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_, params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def get_rolesId(self, args_, uri_: str = '/v1/roles/'):
        '''
        api     : 获取指定角色
        url     : GET /v1/roles/:roleId
        Load    : auth_token, uri + args:[roleId(path)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 角色id      in json.data.id
        notes   : 角色name    in json.data.name
        notes   : 角色描述    in json.data.desc
        notes   : 关联用户id    in json.data.relation_uids
        notes   : 关联区域id    in json.data.area_id
        notes   : 关联资源id    in json.data.rc_ids
        '''
        result = ''
        _params = ''
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.get(url=self.__url + uri_ + str(args_), params=_params, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.get(url=self.__url + uri_ + str(args_), params=_params, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def put_rolesId(self, args_: list, uri_: str = '/v1/roles/'):
        '''
        api     : 编辑角色
        url     : PUT /v1/roles/:roleId
        Load    : auth_token, uri + args:[roleId(path), name(str), desc(str), area_id(int), relation_uids(str), enable(int), rc_ids(str)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 判断json.error_code值是否"0"
        notes   : 判断json.error_message值是否"Operation succeeded."来决定关联成功与否
        '''
        result = ''
        _body = {'name': args_[1], 'desc': args_[2], 'area_id': int(args_[3]), 'relation_uids': args_[4], 'enable': int(args_[5]), 'rc_ids': args_[6]}
        _istoken = ''
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.put(url=self.__url + uri_ + str(args_[0]), json=_body, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.put(url=self.__url + uri_ + str(args_[0]), json=_body, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def put_usersId(self, args_: list, uri_: str = '/v1/users/'):
        '''
        api     : 编辑用户
        url     : PUT /v1/roles/:user_id
        Load    : auth_token, uri + args:[user_id(path), action(str), name(str), note(str), password(str), phone(str), group_id(int), enable(str), area_id{int),
                                    b_inherit_auth(int), b_inherit_grpolicy(int), grpolicy_id(int), role_ids(str), is_never_expire(int), expire(int)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 判断json.error_code值是否"0"
        notes   : 判断json.error_message值是否"Update user successfully. "来决定关联成功与否
        '''
        result = ''
        _body = {
            'action': str(args_[1]),
            'name': str(args_[2]),
            'note': str(args_[3]),
            'password': str(args_[4]),
            'phone': str(args_[5]),
            'group_id': int(args_[6]),
            'enable': str(args_[7]),
            'area_id': int(args_[8]),
            'b_inherit_auth': int(args_[9]),
            'b_inherit_grpolicy': int(args_[10]),
            'grpolicy_id': int(args_[11]),
            'role_ids': str(args_[12]),
            'is_never_expire': int(args_[13]),
            'expire': int(args_[14])
        }
        _istoken = ''
        print('args_:', args_)
        print('\n')
        print('_body:', _body)
        return
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.put(url=self.__url + uri_ + str(args_[0]), json=_body, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.put(url=self.__url + uri_ + str(args_[0]), json=_body, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def put_servers_bind_users(self, args_: list, uri_: str = '/v1/servers/bind_users'):
        '''
        api     : 虚拟机关联用户（单个）
        url     : PUT /v1/servers/bind_users
        Load    : auth_token, uri + args:[rcid(int), vmid(int), type(str), user_id(int), user_name(str), flag(int)]
        return  : (status_code:int, json:dict, onetime:time, istoken:bool)
        notes   : 判断json.error_code值是否"0"
        notes   : 判断json.error_message值是否"Operation succeeded."来决定关联成功与否
        '''
        result = ''
        if args_[5] == 1:
            _body = {'rcid': int(args_[0]), 'vmid': int(args_[1]), 'type': str(args_[2]), 'user_id': int(args_[3])}
        elif args_[5] == 0:
            _body = {'rcid': int(args_[0]), 'vmid': int(args_[1]), 'type': str(args_[2]), 'user_name': str(args_[4])}
        _istoken = ''
        print('args_:', args_)
        print('\n')
        print('_body:', _body)
        return
        try:
            _sT = time.time()
            tmp_headers = self.jsonHeaders
            tmp_headers['Auth-Token'] = self.__auth_token
            result = requests.put(url=self.__url + uri_, json=_body, headers=tmp_headers, verify=False)
            result_json = result.json()
            _istoken = 1
            if (result_json['error_code'] == 1101 and result_json['error_message'] == '[AUTH_TOKEN_INVALID]'):
                _headers = self.set_headers()
                result = requests.put(url=self.__url + uri_, json=_body, headers=_headers, verify=False)
                _istoken = 0
        except Exception as e:
            return (400, e)
        _oT = OpenAPITools.custom_random(str(time.time() - _sT), 3, 1)
        return (result.status_code, result.json(), _oT, _istoken)

    def update_VDCInfo_for_source(self):
        '''
        从本地数据源去更新VDC数据源
        '''
        self.vdcSource.clear()
        _resources_keys = self.resourcesDict.keys()
        _users_keys = self.usersDict.keys()
        for v0 in self.resourceVMDict.values():  # VDC数据 : rc_name, user_name, vm_name
            _rc_note = self.resourcesDict[v0['rc_name']]['note'] if v0['rc_name'] in _resources_keys else -1
            _rc_grp_id = int(self.resourcesDict[v0['rc_name']]['grp_id']) if v0['rc_name'] in _resources_keys else -1
            _rc_role_name = self.resourcesDict[v0['rc_name']]['role_name'] if v0['rc_name'] in _resources_keys else -1
            _user_id = int(self.usersDict[v0['apply_user']]['id']) if v0['apply_user'] in _users_keys else -1
            _user_note = self.usersDict[v0['apply_user']]['note'] if v0['apply_user'] in _users_keys else -1
            _user_phone = self.usersDict[v0['apply_user']]['phone'] if v0['apply_user'] in _users_keys else -1
            _user_group_id = int(self.usersDict[v0['apply_user']]['group_id']) if v0['apply_user'] in _users_keys else -1
            _user_area_name = self.usersDict[v0['apply_user']]['area_name'] if v0['apply_user'] in _users_keys else -1
            _user_grpolicy = self.usersDict[v0['apply_user']]['grpolicy'] if v0['apply_user'] in _users_keys else -1
            _user_role_names = self.usersDict[v0['apply_user']]['role_names'] if v0['apply_user'] in _users_keys else -1
            _user_enable = int(self.usersDict[v0['apply_user']]['enable']) if v0['apply_user'] in _users_keys else -1
            _user_expire = int(self.usersDict[v0['apply_user']]['expire']) if v0['apply_user'] in _users_keys else -1
            _user_last_login_time = int(self.usersDict[v0['apply_user']]['last_login_time']) if v0['apply_user'] in _users_keys else -1

            _role_names = self.usersDict[v0['apply_user']]['role_names'] if v0['apply_user'] in _users_keys else -1
            _role_ids = ''
            _role_desc = []
            _role_relation_uids = []
            _role_area_id = []
            _role_rc_ids = []
            if _role_names != -1:
                if ',' in _role_names:
                    _role_names_len = len(_role_names.split(','))
                    for item in _role_names.split(','):
                        _role_ids += str(self.rolesDict[item]['id']) if item == _role_names.split(',')[_role_names_len -
                                                                                                       1] else str(self.rolesDict[item]['id']) + ','
                    for v1 in _role_names.split(','):
                        _role_desc.append(self.rolesDict[v1]['desc'])
                        _role_relation_uids.append(self.rolesDict[v1]['relation_uids'])
                        _role_area_id.append(self.rolesDict[v1]['area_id'])
                        _role_rc_ids.append(self.rolesDict[v1]['rc_ids'])
                elif _role_names != '':
                    _role_ids = str(self.rolesDict[_role_names]['id']) if _role_names in self.rolesDict.keys() else -2
            elif _role_names == -1:
                _role_ids = -1

            self.vdcSource[v0['vm_name']] = {
                'rc_id': int(v0['rc_id']),
                'rc_name': v0['rc_name'],
                'rc_note': _rc_note,
                'rc_grp_id': _rc_grp_id,
                'rc_role_name': _rc_role_name,
                'user_id': _user_id,
                'user_note': _user_note,
                'user_phone': _user_phone,
                'user_name': v0['apply_user'],
                'user_group_id': _user_group_id,
                'user_area_name': _user_area_name,
                'user_grpolicy': _user_grpolicy,
                'user_role_names': _user_role_names,
                'user_enable': _user_enable,
                'user_expire': _user_expire,
                'user_last_login_time': _user_last_login_time,
                'vm_id': int(v0['_id']),
                'vm_name': v0['vm_name'],
                'vm_name_user': v0['vm_name_user'],
                'vm_rc_id': int(v0['rc_id']),
                'vm_rc_name': v0['rc_name'],
                'vm_apply_user': v0['apply_user'],
                'vm_apply_user_status': v0['apply_user_status'],
                'vm_agent_version': v0['agent_version'],
                'vm_last_login': v0['last_login'],
                'vm_is_used': v0['is_used'],
                'vm_user_desc': v0['user_desc'],
                'vm_group_policy_id': v0['group_policy_id'],
                'vm_group_policy_name': v0['group_policy_name'],
                'vm_is_enable_group_policy': v0['is_enable_group_policy'],
                'role_names': _role_names,
                'role_ids': _role_ids,
                'role_desc': _role_desc,
                'role_relation_uids': _role_relation_uids,
                'role_area_id': _role_area_id,
                'role_rc_ids': _role_rc_ids,
            }
        return self.get_vdcSource()

    def update_sourceInfo_for_VDC(self):
        '''
        从本地VDC源去更新数据源
        '''
        for v0 in self.vdcSource.values():
            self.resourcesDict[v0['rc_name']]['note'] = v0['rc_note']
            self.resourcesDict[v0['rc_name']]['grp_id'] = v0['rc_grp_id']
            self.resourcesDict[v0['rc_name']]['role_name'] = v0['rc_role_name']

            self.resourceVMDict[v0['vm_name']]['rc_id'] = v0['vm_rc_id']
            self.resourceVMDict[v0['vm_name']]['rc_name'] = v0['vm_rc_name']
            self.resourceVMDict[v0['vm_name']]['apply_user'] = v0['vm_apply_user']
            self.resourceVMDict[v0['vm_name']]['apply_user_status'] = v0['vm_apply_user_status']
            self.resourceVMDict[v0['vm_name']]['agent_version'] = v0['vm_agent_version']
            self.resourceVMDict[v0['vm_name']]['last_login'] = v0['vm_last_login']
            self.resourceVMDict[v0['vm_name']]['is_used'] = v0['vm_is_used']
            self.resourceVMDict[v0['vm_name']]['vm_user_desc'] = v0['user_desc']
            self.resourceVMDict[v0['vm_name']]['areaId'] = v0['vm_areaId']
            self.resourceVMDict[v0['vm_name']]['group_policy_id'] = v0['vm_group_policy_id']
            self.resourceVMDict[v0['vm_name']]['group_policy_name'] = v0['vm_group_policy_name']
            self.resourceVMDict[v0['vm_name']]['is_enable_group_policy'] = v0['vm_is_enable_group_policy']

            self.usersDict[v0['user_name']]['note'] = v0['user_note']
            self.usersDict[v0['user_name']]['phone'] = v0['user_phone']
            self.usersDict[v0['user_name']]['group_id'] = v0['user_group_id']
            self.usersDict[v0['user_name']]['area_name'] = v0['user_area_name']
            self.usersDict[v0['user_name']]['grpolicy'] = v0['user_grpolicy']
            self.usersDict[v0['user_name']]['role_names'] = v0['user_role_names']
            self.usersDict[v0['user_name']]['enable'] = v0['user_enable']
            self.usersDict[v0['user_name']]['expire'] = v0['user_expire']
            self.usersDict[v0['user_name']]['last_login_time'] = v0['user_last_login_time']

            if v0['role_name'] != '' and v0['role_name'] != -1:
                _nn = 0
                for item in v0['role_names'].split(','):
                    self.rolesDict[item]['desc'] = v0['role_desc'][_nn]
                    self.rolesDict[item]['relation_uids'] = v0['role_relation_uids'][_nn]
                    self.rolesDict[item]['area_id'] = v0['role_area_id'][_nn]
                    self.rolesDict[item]['rc_ids'] = v0['role_rc_ids'][_nn]
                    _nn += 1
        return self.get_vdcSource()

    def update_repairInfo(self):
        '''
        排查/纠错 数据源
        '''
        self.bindCount = 0
        self.noBindRoleDict.clear()
        self.idleVMDict.clear()
        self.lossVMUserDict.clear()
        self.userBindMultVMDict.clear()
        # 获取关联多台虚拟机的用户列表
        _statistics_user = []
        for v0 in self.vdcSource.values():
            # 获取LDAP里已分配虚拟机的LDAP用户列表 (即LDAP里存在该用户, 未离职)
            if v0['user_name']:
                _statistics_user.append(v0['user_name'])
                self.bindCount += 1
                # 关联了虚拟机但未关联角色的用户列表
                if v0['role_names'] == '':
                    self.noBindRoleDict[v0['user_name']] = {
                        'vm_name': v0['vm_name'],
                        'rc_name': v0['rc_name'],
                        'user_name': v0['user_name'],
                        'role_name': v0['role_names']
                    }
            else:
                # 获取闲置的虚拟机列表 (满足虚拟机未关联用户条件)
                if v0['vm_name'] == v0['vm_name_user']:
                    self.idleVMDict[v0['vm_name']] = {
                        'vm_name': v0['vm_name'],
                        'rc_name': v0['rc_name'],
                        'user_name': v0['user_name'],
                        'role_name': v0['role_names']
                    }
                # 获取曾经关联过虚拟机的LDAP用户列表
                elif v0['vm_name'] != v0['vm_name_user'] and v0['vm_name_user'].split('_')[1] in self.usersDict.keys():
                    _lossvm_user = v0['vm_name_user'].split('_')[1]
                    _current_vm_list = [v['vm_name'] for v in self.resourceVMDict.values() if v['apply_user'] == _lossvm_user]
                    _current_rc_list = [v['rc_name'] for v in self.resourceVMDict.values() if v['apply_user'] == _lossvm_user]
                    self.lossVMUserDict[_lossvm_user] = {
                        'current_vm_list': ','.join(_current_vm_list),
                        'current_rc_list': ','.join(_current_rc_list),
                        'loss_vm_name': v0['vm_name'],
                        'loss_vm_name_user': v0['vm_name_user'],
                        'rc_name': v0['rc_name'],
                        'user_name': _lossvm_user,
                        'role_name': v0['role_names']
                    }
        for item in list(set([v for v in _statistics_user if _statistics_user.count(v) > 1])):
            _sourceInfo = [k for k in self.vdcSource.values() if item == k['user_name']][0]
            # print('_sourceInfo:', _sourceInfo, '\n')
            self.userBindMultVMDict[item] = {
                'vm_name': _sourceInfo['vm_name'],
                'rc_name': _sourceInfo['rc_name'],
                'user_name': item,
                'role_name': _sourceInfo['role_names']
            }  # 获取LDAP里不存在且已分配虚拟机的用户 (即LDAP里不存在该用户, 已离职, 但VDC还存在该用户的绑定关系)

    def update_writeJson(self, flag_: int):
        '''
        执行更新覆盖json到文件
        flag_为-1 则提示写入, flag_为0 则不提示写入.
        '''
        OpenAPITools.WriteJson(self.rolesDict, self.programSourceFilePath, 'VDC角色列表', flag_)
        OpenAPITools.WriteJson(self.resourcesDict, self.programSourceFilePath, 'VDC资源列表', flag_)
        OpenAPITools.WriteJson(self.resourceVMDict, self.programSourceFilePath, 'VDC虚拟机列表', flag_)
        OpenAPITools.WriteJson(self.usersDict, self.programSourceFilePath, 'VDC用户列表', flag_)
        OpenAPITools.WriteJson(self.get_vdcSource(), self.programSourceFilePath, 'VDC数据源', flag_)
        OpenAPITools.WriteJson(self.noBindRoleDict, self.checkFilePath, self.noBindRoleFile, flag_)
        OpenAPITools.WriteJson(self.lossVMUserDict, self.checkFilePath, self.lossVmUserFile, flag_)
        OpenAPITools.WriteJson(self.idleVMDict, self.checkFilePath, self.idleVMFile, flag_)
        OpenAPITools.WriteJson(self.userBindMultVMDict, self.checkFilePath, self.userBindMultVMFile, flag_)


class OpenAPITools:
    '''
    辅助工具类
    '''

    # GLOBAL var
    ONCE_COUNTERS_QPS = 500

    @staticmethod
    def custom_random(input_, n_, flag_):
        """
        自定义取小数点后n位, flag的 0: 四舍五入, 1: 向下取整, 2: 向上取整
        """

        # custom_random = lambda r,n: str(r)[:str(r).rfind('.') + n + 1]
        num = str(input_)
        mash = num[num.rfind('.') + 1:]
        if flag_ == 0:
            for nx in range(len(mash)):
                if n_ == 0:
                    if mash[0] <= 4:
                        return num[:num.find('.')]
                    else:
                        return num[:num.find('.')] + 1
                else:
                    if nx <= n_ + 1:
                        if mash[nx] < 4:
                            return num[:num.find('.') + n_]
                        elif mash[nx] == 4:
                            continue
                        else:
                            # n=0 : +1
                            # n=1 : +0.1
                            # n=2 : +0.01
                            # ...
                            return num[:num.find('.') + n_ + 1] + (1 / 10**n_)
                    else:
                        print('#')
        elif flag_ == 1:
            return num[:num.find('.') + n_ + 1]
        elif flag_ == 2:
            return num[:num.find('.') + n_ + 1] + (1 / 10**n_)
        else:
            return "flag为错误值"

    @staticmethod
    def WriteJson(json_: object, filedir_: str, filename_: str, prefix_: str = 'OpenAPI_', flag_: int = -1):
        """
        输出json数据到文件
        json_       : 写入的json
        filedir_    : 写入的文件夹路径
        filename_   : 写入的文件名称
        flag_       : print输出执行结果
        """
        writeJson = {'writeTime': time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time())), 'result': json_}
        with open(os.path.join(filedir_, "{_prefix}{_fname}.json".format(_prefix=prefix_, _fname=filename_)), 'w', encoding='utf-8') as f:
            f.write(json.dumps(writeJson, indent=2, ensure_ascii=False))
        print('执行写入:{_dir}\\{_prefix}{_fname}.json'.format(_dir=filedir_, _prefix=prefix_, _fname=filename_)) if flag_ == -1 else ''

    @staticmethod
    def input_csv():
        '''
        获取CSV文件数据
        '''
        while True:
            try:
                csv_file = input('拖拽CSV文件获取路径 >>> ').strip()
                if csv_file == '':
                    continue
                elif ('csv' in os.path.splitext(csv_file)[1] and os.path.exists(csv_file)):
                    return str(csv_file)
                elif 'csv' not in os.path.splitext(csv_file)[1]:
                    print('错误: 非CSV文件, 重新输入')
                    continue
                elif not os.path.exists(csv_file):
                    print('错误: CSV文件不存在, 重新输入')
                    continue
            except Exception:
                print('CSV文件错误, 重新输入')
                continue

    @staticmethod
    def get_errormsg(errorMsg_: str, msg_: str, flag_: int = -1):
        while True:
            try:
                if flag_ == -1:
                    result = input('读取%s失败, 输入0获取错误信息, 输入1重启当前失败请求, 输入2退出程序 >>> ' % msg_).strip()
                elif flag_ == 1:
                    result = input('输入1重启程序, 输入2退出程序 >>> ')
                if int(result) == 0:
                    print('错误信息如下:\n', errorMsg_)
                    return OpenAPITools.get_errormsg(errorMsg_, msg_, 1)
                elif int(result) == 1:
                    return 1
                elif int(result) == 2:
                    return 2
            except Exception:
                print('输入错误, 重新输入')
                continue

    @staticmethod
    def ret_error(obj_: GetOpenAPI, flag_: int, args_: object = ''):
        _msgs = {1: '资源组', 2: '资源', 3: '用户列表', 4: '资源组', 5: '用户'}
        if flag_ == 1:
            result = obj_.get_resourcesGroup()
        elif flag_ == 2:
            result = obj_.get_resource_servers([args_['id'], 1, OpenAPITools.ONCE_COUNTERS_QPS, 0])
        elif flag_ == 3:
            result = obj_.get_users([-100, 1, 1])
        elif flag_ == 4:
            result = obj_.get_resources_list(args_)
        elif flag_ == 5:
            result = obj_.get_users([-100, args_ + 1, 200])
        elif flag_ == 6:
            result = obj_.get_roles([1, OpenAPITools.ONCE_COUNTERS_QPS])
        elif flag_ == 7:
            result = obj_.get_rolesId(args_)
        elif flag_ == 8:
            result = obj_.get_usersId(args_)
        elif flag_ == 9:
            print('result args_:', args_)
            result = obj_.get_servers_bind_users_list(args_)
        elif flag_ == 10:
            result = obj_.get_bind_users_servers(args_)

        if int(result[0]) == 400:
            lock.acquire()
            _code = OpenAPITools.get_errormsg(result[1], _msgs[flag_])  # Debugger期间用来获取日志
            lock.release()
            if _code == 2:
                print('退出程序...')
                sys.exit()
            elif _code == 1:
                return OpenAPITools.ret_error(obj_, flag_, args_)
        elif int(result[0]) == 200 and (result[1]['error_code'] == 1002 and result[1]['error_message'] == '[COMMON_GET_LOCK_FAILED]'):
            # 达到OpenAPI的并发QPS上限, 等待2秒后重新请求
            qps_msg = ''
            if flag_ == 1:
                qps_msg = _msgs[flag_]
            elif flag_ == 2:
                qps_msg = _msgs[flag_] + ':' + str(args_['id'])
            elif flag_ == 3:
                qps_msg = _msgs[flag_]
            elif flag_ == 4:
                qps_msg = _msgs[flag_] + ':' + str(args_)
            elif flag_ == 5:
                qps_msg = _msgs[flag_] + ':' + str(args_ * 200 + 1) + ' - ' + str((args_ + 1) * 200)
            elif flag_ == 6:
                qps_msg = _msgs[flag_]
            elif flag_ == 7:
                qps_msg = _msgs[flag_] + ':' + str(args_)
            elif flag_ == 8:
                qps_msg = _msgs[flag_] + ':' + str(args_)

            print('当前请求[{0}]触发了OpenAPI的QPS, 等待2s后执行...'.format(qps_msg))
            time.sleep(2)
            return OpenAPITools.ret_error(obj_, flag_, args_)
        elif int(result[0]) == 200:
            return result

    @staticmethod
    def loop_dir(fullname_: str, num: int = 1):
        '''
        新建指定名称的文件夹
        xxxx-xx-xx xx.NODE.1
        xxxx-xx-xx xx.NODE.2
        xxxx-xx-xx xx.NODE....
        '''
        programFullPath = fullname_[:fullname_.rfind('.') + 1] + str(num)

        if (os.path.exists(programFullPath)):
            num += 1
            return OpenAPITools.loop_dir(fullname_=programFullPath, num=num)
        else:
            return programFullPath
