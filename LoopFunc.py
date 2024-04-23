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
import csv
import json
import os
import sys
import time
from copy import deepcopy
from getpass import getpass

import GetOpenAPI


class LoopFunc:
    '''
    循环获取指令, 用于用户交互.
    '''

    # Public var
    #
    normalCommands = [
        'config-mode-pro', 'config-mode-normal', 'check-bind-role', 'check-lossvm-user', 'check-idle-vm', 'check-mult-bindvm', 'exit', 'help', 'loadcsv ',
        'mode', 'quit', 'show '
    ]
    proCommands = [
        'csv-bind ', 'csv-unbind ', 'config-mode-pro', 'config-mode-normal', 'config-mode-debug', 'check-bind-role', 'check-lossvm-user', 'check-idle-vm',
        'check-mult-bindvm', 'exit', 'help', 'loadcsv ', 'mode', 'quit', 'rshow ', 'show '
    ]
    debugCommands = ['exec', 'exit', 'help', 'show-var ', 'quit']
    execCommands = ['exit', 'help', 'quit']
    currentMode = 1
    programFullPath: str
    debugSelfVars = []
    debugOpenApiVars = []
    debugVarsDict = {}

    # Private var
    #
    __my_open_api: GetOpenAPI.GetOpenAPI
    __vdc_source: dict
    # 本地VDC数据源
    __vm_info_count: tuple
    # 获取资源、虚拟机、用户、角色的总数
    __bind_count: int
    # 记录已分配虚拟机的用户数
    __csv_data: dict
    # 本地CSV数据 : rc_name, rc_id, user_name, user_id, vm_name, vm_id, role_names
    __loadcsv_stat: bool

    # csv文件的加载状态

    def __init__(self, myOpenApi_: GetOpenAPI.GetOpenAPI):
        '''
        构造函数:
        初始化对象, 输入csv数据生成交互指令
        '''

        self.__my_open_api = myOpenApi_
        self.programFullPath = myOpenApi_.programFullPath
        self.__vm_info_count = myOpenApi_.get_vm_info_count()
        self.__bind_count = myOpenApi_.bindCount
        self.__vdc_source = myOpenApi_.get_vdcSource()
        self.__loadcsv_stat = False

    def update_init(self):
        self.programFullPath = self.__my_open_api.programFullPath
        self.__vm_info_count = self.__my_open_api.get_vm_info_count()
        self.__bind_count = self.__my_open_api.bindCount
        self.__vdc_source = self.__my_open_api.get_vdcSource()

    def loop_func(self):
        '''
        循环获取指令
        '''
        while True:
            try:
                input_str = input('Python > ')
                if len(input_str) == 0:
                    continue
                if input_str == 'exit' or input_str == 'quit':
                    print('输入了%s: 终止程序' % input_str)
                    sys.exit()
                elif input_str == 'mode':
                    print('当前模式:', '常规模式' if self.currentMode == 1 else '专业模式')
                    continue
                elif self.currentMode == 2 and input_str.strip() == 'config-mode-debug':
                    self.loop_func_debug()
                    continue
                elif input_str.strip() == 'config-mode-pro':
                    self.currentMode = 2
                    print("切换到'专业模式', 输入 help 以获取更多帮助信息.")
                    continue
                elif input_str.strip() == 'config-mode-normal':
                    self.currentMode = 1
                    print("切换到'常规模式', 输入 help 以获取更多帮助信息.")
                    continue
                elif input_str[:4] == 'show':  # 查询指定序号的数据源 : 常规查询
                    self.loop_func_show(input_str)
                    continue
                elif input_str[:5] == 'rshow':  # 查询指定序号的数据源 : 高级查询
                    print('功能暂未开放，敬请期待。')
                    # self.loop_func_rshow(input_str)
                    continue
                elif input_str[:7] == 'loadcsv':  # 加载本地CSV数据源
                    self.loop_func_loadcsv(input_str)
                    continue
                elif input_str[:15] == 'check-bind-role':
                    self.loop_func_checkBindRole(input_str)
                    continue
                elif input_str[:17] == 'check-lossvm-user':
                    print('功能暂未开放，敬请期待。')
                    # self.loop_func_checkLossVMUser(input_str)
                    continue
                elif input_str[:13] == 'check-idle-vm':
                    print('功能暂未开放，敬请期待。')
                    # self.loop_func_checkIdleVM(input_str)
                    continue
                elif input_str[:17] == 'check-mult-bindvm':
                    print('功能暂未开放，敬请期待。')
                    # self.loop_func_checkMultBindVM(input_str)
                    continue
                elif self.currentMode == 2 and input_str[:8] == 'csv-bind':
                    print('功能暂未开放，敬请期待。')
                    # self.loop_func_csvbind(input_str)
                    continue
                elif self.currentMode == 2 and input_str[:10] == 'csv-unbind':
                    print('功能暂未开放，敬请期待。')
                    # self.loop_func_csvunbind(input_str)
                    continue
                elif self.currentMode == 1 and input_str == 'help':
                    self.loop_get_help(1)
                    continue
                elif self.currentMode == 2 and input_str == 'help':
                    self.loop_get_help(2)
                    continue
                else:
                    print("'%s'不是有效的命令, 输入 help 以获取更多帮助信息." % input_str)
                    continue
            except Exception as e:
                print('InputError:', e)
                continue

    def loop_func_show(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_show()
                return
            elif len(options) >= 4:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], options[3]))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                return
            elif options[1].lower() == '-csv':
                get_num_info = self.loop_ret_id(options[2], options[0])
                if get_num_info is None:
                    return
                else:
                    self.loop_get_vdc_source(get_num_info[2], get_num_info[0], get_num_info[1], mapcsv_=True)
                    return
            elif len(options) == 2:
                get_num_info = self.loop_ret_id(options[1], options[0])
                if get_num_info is None:
                    return
                else:
                    self.loop_get_vdc_source(get_num_info[2], get_num_info[0], get_num_info[1])
                    return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_rshow(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_rshow()
                return
            elif '-csv' in [v.lower() for v in options]:
                pass
            elif len(options) == 2 and '=' not in options:
                get_num_info = self.loop_ret_id(options[1], options[0])
                if get_num_info is None:
                    return
                else:
                    self.loop_get_vdc_source(get_num_info[2], get_num_info[0], get_num_info[1])
                    return
            elif '=' in options:
                pass
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_csvbind(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_csvbind()
                return
            elif len(options) >= 4:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], options[3]))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                return
            elif options[1].lower() == '-vu' or options[1].lower() == '--vm-user':
                get_num_info = self.loop_ret_id(options[2], options[0])
                if get_num_info is None:
                    return
                else:
                    self.loop_get_vdc_source(get_num_info[2], get_num_info[0], get_num_info[1])
                    return
            elif options[1].lower() == '-ur' or options[1].lower() == '--user-role':
                get_num_info = self.loop_ret_id(options[2], options[0])
                if get_num_info is None:
                    return
                else:
                    self.loop_get_vdc_source(get_num_info[2], get_num_info[0], get_num_info[1])
                    return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_csvunbind(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_csvunbind()
                return
            elif len(options) >= 4:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(options[3])))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                return
            elif options[1].lower() == '-l' or options[1].lower() == '--lock':
                get_num_info = self.loop_ret_id(options[2], options[0])
                if get_num_info is None:
                    return
                else:
                    return
            elif len(options) == 2:
                get_num_info = self.loop_ret_id(options[1], options[0])
                if get_num_info is None:
                    return
                else:
                    return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_loadcsv(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_loadcsv()
                return
            elif len(options) == 2:
                csv_file = options[1].replace('"', '').replace("'", '').strip()
                if ('csv' in os.path.splitext(csv_file)[1] and os.path.exists(csv_file)):
                    if self.__loadcsv_stat is False:
                        pass
                    elif self.__loadcsv_stat and input('当前已加载CSV文件, 是否覆盖？ ( yes ) ').lower().strip() == 'yes':
                        pass
                    else:
                        print('取消覆盖CSV数据源.')
                        return
                    print('正在覆盖CSV文件...') if self.__loadcsv_stat else print('读取CSV...')
                    self.__csv_data = {}
                    with open(csv_file, mode='r') as csvdata:
                        _csv_reader = csv.reader(csvdata)
                        for i, rows in enumerate(_csv_reader):
                            if i == 0:
                                for val in rows:  # 收集列id
                                    if '虚拟机名称' in val:
                                        _vm_name_id = rows.index(val)
                                    elif '关联用户' in val:
                                        _user_name_id = rows.index(val)
                                    elif '所属资源' in val:
                                        _rc_name_id = rows.index(val)
                            else:
                                self.__csv_data[rows[_vm_name_id]] = {
                                    'rc_name': rows[_rc_name_id],
                                    'user_name': rows[_user_name_id],
                                    'vm_name': rows[_vm_name_id]
                                }
                    print('覆盖CSV完成') if self.__loadcsv_stat else print('读取CSV完成')
                    GetOpenAPI.OpenAPITools.WriteJson(self.__csv_data, self.programSourceFilePath, 'CSV数据源')
                    self.__loadcsv_stat = True
                    return
                elif 'csv' not in os.path.splitext(csv_file)[1]:
                    print("{0}: 非CSV文件 -- '{1}'".format(options[0], str(options[1])))
                    print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                    return
                elif not os.path.exists(csv_file):
                    print("{0}: CSV文件不存在 -- '{1}'".format(options[0], str(options[1])))
                    print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                    return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_checkBindRole(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_checkBindRole()
                return
            elif self.__my_open_api.noBindRoleDict == '':
                print('当前查询为空.')
                return
            elif len(options) == 1:
                put_results = self.loop_get_put_source(options[0])
                if put_results[0] == 400:
                    print("{0}: ErrorMsg -- {1}".format(options[0], put_results[1]))
                    return
                elif put_results[0] == 200:
                    self.loop_put_checkBindRole(put_results[1])
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_checkLossVMUser(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_checkLossVMUser()
                return
            elif self.__my_open_api.lossVMUserDict == '':
                print('当前查询为空.')
                return
            elif len(options) == 1:
                put_results = self.loop_get_put_source(options[0])
                print('put_results:', put_results)
                if put_results[0] == 400:
                    print("{0}: ErrorMsg -- {1}".format(options[0], put_results[1]))
                    return
                elif put_results[0] == 200:
                    self.loop_put_checkLossVMUser(put_results[1])
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_checkIdleVM(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_checkIdleVM()
                return
            elif self.__my_open_api.idleVMDict == '':
                print('当前查询为空.')
                return
            elif len(options) == 1:
                self.loop_get_check_vdc_source(options[0])
                return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_checkMultBindVM(self, input_str):
        try:
            options = input_str.split()
            if '--help' in options:
                self.loop_get_help_checkMultBindVM()
                return
            elif self.__my_open_api.userBindMultVMDict == '':
                print('当前查询为空.')
                return
            elif len(options) == 1:
                self.loop_get_check_vdc_source(options[0])
                return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_str[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_debug(self):
        n = 0
        while n < 2:
            if getpass('Input-Sangfor-Pass:') == 'sangfor*******':
                self.currentMode = 3
                print("切换到'Debugger模式', 输入 help 以获取更多帮助信息.")
                self.loop_get_debug_vars()
                while True:
                    try:
                        input_debugstr = input('Python Debug > ')
                        if len(input_debugstr) == 0:
                            continue
                        if input_debugstr == 'exit' or input_debugstr == 'quit':
                            print('输入了%s: 退出Debugger模式' % input_debugstr)
                            self.currentMode = 2
                            return
                        elif input_debugstr == 'mode':
                            print('当前模式: Debugger模式')
                            continue
                        elif input_debugstr[:4] == 'exec':
                            self.loop_func_debug_exec(input_debugstr)
                            continue
                        elif input_debugstr[:8] == 'show-var':
                            self.loop_func_debug_showVar(input_debugstr)
                            continue
                        elif input_debugstr == 'help':
                            self.loop_get_help(3)
                            continue
                        else:
                            print("'%s'不是有效的命令, 输入 help 以获取更多帮助信息." % input_debugstr)
                            continue
                    except Exception as e:
                        print('Debug InputError:', e)
                        continue
            else:
                time.sleep(1)
                n += 1
                continue
        print('鉴权失败: codeReturn 691')

    def loop_func_debug_exec(self, input_debugstr):
        options = input_debugstr.split()
        if '--help' in options:
            self.loop_get_help_debug_exec()
            return
        elif input_debugstr == 'exec':
            self.currentMode = 4
            while True:
                try:
                    input_exec = input('Python Debug exec >')
                    if input_exec == 'exit' or input_exec == 'quit':
                        print('exec Quit')
                        return
                    elif input_exec == 'help':
                        self.loop_get_help_debug_exec()
                        continue
                    else:
                        exec(input_exec)
                except Exception as e:
                    print('exec InputError:', e)
                    continue
        else:
            print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_debugstr[len(options[0]) + 1:].strip())))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_func_debug_showVar(self, input_debugstr):
        try:
            options = input_debugstr.split()
            if '--help' in options:
                self.loop_get_help_debug_showVar()
                return
            elif len(options) >= 4:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], options[3]))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                return
            elif len(options) == 3 and (options[2] in self.debugSelfVars or options[2] in self.debugOpenApiVars):
                exec('self.debugVarsDict=deepcopy(%s)' %
                     (str(options[2]).replace('openapi.', 'self._LoopFunc__my_open_api._GetOpenAPI') if '__' in options[2] else str(options[2]).replace(
                         'openapi.', 'self._LoopFunc__my_open_api.'))) if 'openapi.' in options[2] else exec(
                             'self.debugVarsDict=deepcopy(%s)' % (str(options[2]).replace('self.', 'self._LoopFunc' if '__' in options[2] else options[2])))
                if options[1].lower() in ['-d', '--dict']:
                    for k0, v0 in self.debugVarsDict.items():
                        print('{{{2} {0}: {1}{2}}}'.format(k0, v0, '\n'), '\n')
                    return
                elif options[1].lower() in ['-j', '--json']:
                    print(json.dumps(self.debugVarsDict, indent=2, ensure_ascii=False))
                    return
                else:
                    print("{0}: 错误的选项 -- '{1}'".format(options[0], options[1]))
                    print("尝试 '%s --help' 获取更多帮助信息." % options[0])
                    return
            elif len(options) == 2 and (options[1] in self.debugSelfVars or options[1] in self.debugOpenApiVars):
                exec('print(%s)' % str(options[1]).replace('openapi.', 'self._LoopFunc__my_open_api._GetOpenAPI') if '__' in options[1] else 'print(%s)' %
                     str(options[1]).replace('openapi.', 'self._LoopFunc__my_open_api.')) if 'openapi.' in options[1] else exec(
                         'print(%s)' % str(options[1]).replace('self.', 'self._LoopFunc') if '__' in options[1] else 'print(%s)' % options[1])
                return
            elif len(options) == 1:
                for v0 in self.debugSelfVars:
                    print('Self.PrivateVars: %s' % v0) if '__' in v0 else ''
                print('\n')
                for v0 in self.debugSelfVars:
                    '' if '__' in v0 else print('Self.PublicVars: %s' % v0)
                print('\n')
                for v1 in self.debugOpenApiVars:
                    print('OpenAPI.PrivateVars: %s' % v1) if '__' in v1 else ''
                print('\n')
                for v1 in self.debugOpenApiVars:
                    '' if '__' in v1 else print('OpenAPI.PublicVars: %s' % v1)
                print('\n')
                return
            else:
                print("{0}: 错误的选项 -- '{1}'".format(options[0], str(input_debugstr[len(options[0]) + 1:].strip())))
                print("尝试 '%s --help' 获取更多帮助信息." % options[0])
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(options[0], e))
            print("尝试 '%s --help' 获取更多帮助信息." % options[0])

    def loop_get_vdc_source(self, get_flag_: int = -1, startNum_: int = -1, stopNum_: int = -1, mapcsv_: bool = False):
        '''
        循环获取本地数据源
        '''
        # os.system('cls')
        _bind_count = deepcopy(self.__bind_count)
        _rc_count = self.__vm_info_count[0]
        _vm_count = self.__vm_info_count[1]
        _user_count = self.__vm_info_count[2]
        _role_count = self.__vm_info_count[3]
        print('--序号 {1}虚拟机名称 (CSV-虚拟机名称) {0}关联用户{2} (CSV-关联用户) {0}所属资源 (CSV-所属资源) {3}{0} 用户的关联角色 (CSV-用户的关联角色) '.format(
            '-' * 12, '-' * 8, ' ' * 7, ' ' * 20).ljust(os.get_terminal_size()[0] - 42, '-')) if mapcsv_ else print(
                '--序号 {1}虚拟机名称  {0}关联用户{2}{0}所属资源{3}{0} 用户的关联角色'.format('-' * 12, '-' * 8, ' ' * 7, ' ' * 20).ljust(os.get_terminal_size()[0] - 22, '-'))
        _num = 0
        for v0 in self.__vdc_source.values():
            if mapcsv_:
                _csv_vm_name = self.__csv_data[v0['vm_name']]['vm_name'] if v0['vm_name'] in self.__csv_data.keys() else -1
                _csv_rc_name = self.__csv_data[v0['vm_name']]['rc_name'] if v0['vm_name'] in self.__csv_data.keys() else -1
                _csv_user_name = self.__csv_data[v0['vm_name']]['user_name'] if v0['vm_name'] in self.__csv_data.keys() else -1
            _num += 1
            if get_flag_ == -1 or (stopNum_ == -1 and _num == startNum_) or (_num >= startNum_ and _num <= stopNum_):
                print('{0}{id_}'.format(' ' * 2, id_=_num).ljust(15, ' '),
                      str(v0['vm_name']).ljust(23, ' '),
                      str(_csv_vm_name).ljust(23, ' '),
                      str(v0['user_name'] if v0['user_name'] != '' else '""').ljust(26, ' '),
                      str(_csv_user_name).ljust(26, ' '),
                      str(v0['rc_name']).ljust(20, ' '),
                      str(_csv_rc_name).ljust(40 - len(str(v0['rc_name'])), ' '), (v0['role_names'] if v0['role_names'] != '' else '""')) if mapcsv_ else print(
                          '{0}{id_}'.format(' ' * 2, id_=_num).ljust(14, ' '),
                          str(v0['vm_name']).ljust(23, ' '),
                          str(v0['user_name'] if v0['user_name'] != '' else '""').ljust(26, ' '),
                          str(v0['rc_name']).ljust(40 - len(str(v0['rc_name'])), ' '), (v0['role_names'] if v0['role_names'] != '' else '""'))
        print('-' * int(os.get_terminal_size()[0]))
        if get_flag_ == -1:
            print('当前（VDC数据源 对比 CSV数据源）查询ID: all') if mapcsv_ else print('当前（VDC数据源）查询ID: all')
        elif get_flag_ == 0:
            print('当前（VDC数据源 对比 CSV数据源）查询ID: {}'.format(startNum_)) if mapcsv_ else print('当前（VDC数据源）查询ID: {}'.format(startNum_))
        elif get_flag_ == 1:
            print('当前（VDC数据源 对比 CSV数据源）查询ID: {}-{}'.format(startNum_, stopNum_)) if mapcsv_ else print('当前（VDC数据源）查询ID: {}-{}'.format(startNum_, stopNum_))
        print('-- VDC 当前资源总数: {}'.format(_rc_count).ljust(29, ' '), '-- VDC 当前虚拟机总数: {}'.format(_vm_count).ljust(29, ' '),
              '-- VDC 当前用户总数: {}'.format(_user_count).ljust(29, ' '), '-- VDC 当前角色总数: {}'.format(_role_count))
        print('-- VDC 已分配虚拟机的用户数: {}'.format(_bind_count).ljust(25, ' '), '-- VDC 当前虚拟机使用比例: {:.2%}\n'.format(_bind_count / _vm_count))

        _csv_rc_count = len(set([v['rc_name'] for v in self.__csv_data.values()])) if mapcsv_ else ''
        _csv_vm_count = len(set([v['vm_name'] for v in self.__csv_data.values()])) if mapcsv_ else ''
        _csv_bind_count = len(set([v['user_name'] for v in self.__csv_data.values()])) if mapcsv_ else ''
        print('\n-- CSV 当前资源总数: {}'.format(_csv_rc_count).ljust(29, ' '), '-- CSV 当前虚拟机总数: {}'.format(_csv_vm_count)) if mapcsv_ else ''
        print('-- CSV 已分配虚拟机的用户数: {}'.format(_csv_bind_count).ljust(25, ' '), '-- CSV 当前虚拟机使用比例: {:.2%}\n'.format(_csv_bind_count /
                                                                                                                  _csv_vm_count)) if mapcsv_ else ''
        print('  当前模式: %s, 输入 help 查看更多帮助信息.\n' % ('常规模式' if self.currentMode == 1 else '专业模式'))
        print("  Alert : 用户关联了虚拟机但未关联角色, 输入 check-bind-role 进行下一步修复. 或查看当前程序目录下的 '%s.json' 文件进行手工修复.\n" %
              self.__my_open_api.noBindRoleFile) if self.__my_open_api.noBindRoleDict else ''
        print("  Alert : 用户曾经关联过虚拟机但现在未关联, 输入 check-lossvm-user 进行下一步修复. 或查看当前程序目录下的 '%s.json' 文件进行手工修复.\n" %
              self.__my_open_api.lossVmUserFile) if self.__my_open_api.lossVMUserDict else ''
        print("  Notice: 用户关联多个资源的虚拟机, 可能是分发虚机重复了. 输入 check-mult-bindvm 进行下一步操作. 或查看当前程序目录下的 '%s.json' 文件进行手工操作.\n" %
              self.__my_open_api.userBindMultVMFile) if self.__my_open_api.userBindMultVMDict else ''
        print("  Notice: 存在闲置的虚拟机, 输入 check-idle-vm 进行下一步操作. 或查看当前程序目录下的 '%s.json' 文件进行手工操作.\n" %
              self.__my_open_api.idleVMFile) if self.__my_open_api.idleVMDict else ''

    def loop_get_check_vdc_source(self, get_msg_: str):
        '''
        获取闲置虚拟机列表
        '''
        # os.system('cls')
        print('当前（VDC数据源）查看任务: {}'.format('闲置虚拟机列表' if get_msg_ == 'check-idle-vm' else '关联多个虚拟机的用户列表'))
        _num = 0
        if get_msg_ == 'check-idle-vm':
            print('--序号 {1}虚拟机名称  {0}关联用户{2}{0}所属资源{3}{0} 用户的关联角色'.format('-' * 12, '-' * 8, ' ' * 7, ' ' * 20).ljust(os.get_terminal_size()[0] - 22, '-'))
            for v0 in self.__my_open_api.idleVMDict.values():
                _num += 1
                print('{0}{id_}'.format(' ' * 2, id_=_num).ljust(14, ' '),
                      str(v0['vm_name']).ljust(23, ' '),
                      str(v0['user_name'] if v0['user_name'] != '' else '""').ljust(26, ' '),
                      str(v0['rc_name']).ljust(40 - len(str(v0['rc_name'])), ' '), (v0['role_name'] if v0['role_name'] != '' else '""'))
        elif get_msg_ == 'check-mult-bindvm':
            print('--序号 {1}虚拟机名称  {0}关联用户{2}{0}所属资源{3}{0} 用户的关联角色'.format('-' * 12, '-' * 8, ' ' * 7, ' ' * 20).ljust(os.get_terminal_size()[0] - 22, '-'))
            for v0 in self.__my_open_api.userBindMultVMDict.values():
                _num += 1
                print('{0}{id_}'.format(' ' * 2, id_=_num).ljust(14, ' '),
                      str(','.join(v0['vm_name'])).ljust(23, ' '),
                      str(v0['user_name'] if v0['user_name'] != '' else '""').ljust(26, ' '),
                      str(','.join(v0['rc_name'])).ljust(40 - len(str(','.join(v0['rc_name']))), ' '),
                      (','.join(v0['role_name']) if v0['role_name'] != '' else '""'))
        print('-' * int(os.get_terminal_size()[0]))

    def loop_get_put_source(self, put_msg_: str):
        '''
        循环获取需要对比和修改的数据源
        '''
        # os.system('cls')
        print('当前（VDC数据源）修改任务: {}'.format('关联了虚拟机但没有关联角色的用户列表' if put_msg_ == 'check-bind-role' else '用户曾经关联过虚拟机但现在未关联'))
        _num = 0
        _put_results = []
        if put_msg_ == 'check-bind-role':
            print('--序号 {0}用户名称{1}{0}关联虚拟机{1}{0}所属资源{2}{0} 用户的关联角色 --> (待添加关联角色)'.format('-' * 10, ' ' * 7,
                                                                                         ' ' * 16).ljust(os.get_terminal_size()[0] - 29, '-'))
            for v0 in self.__my_open_api.noBindRoleDict.values():
                _num += 1
                _put_roleName = self.__my_open_api.resourcesDict[v0['rc_name']]['role_name']
                print('{0}{id_}'.format(' ' * 2, id_=_num).ljust(16, ' '),
                      str(v0['user_name']).ljust(24, ' '),
                      str(v0['vm_name']).ljust(26, ' '),
                      str(v0['rc_name']).ljust(30 - len(str(v0['rc_name'])), ' '), (v0['role_name'] if v0['role_name'] != '' else '""').ljust(18, ' '),
                      _put_roleName)

                _usersDict_keys = self.__my_open_api.usersDict.keys()
                _put_roleId = self.__my_open_api.rolesDict[_put_roleName]['id']
                if v0['user_name'] not in _usersDict_keys:
                    return (400, '用户查询失败(不存在该用户): %s , 请重启程序.' % v0['user_name'])
                else:
                    _put_userId = self.__my_open_api.usersDict[v0['user_name']]['id']
                    _put_results.append({
                        'vm_name': v0['vm_name'],
                        'rc_name': v0['rc_name'],
                        'user_name': v0['user_name'],
                        'user_id': _put_userId,
                        'put_role_name': _put_roleName,
                        'put_role_id': _put_roleId
                    })
        elif put_msg_ == 'check-lossvm-user':
            _currentVm_maxLength = max(list(map(lambda x: len(x), [v['current_vm_list'] for v in self.__my_open_api.lossVMUserDict.values()])))
            print('--序号 {0}用户名称{1}{0}已关联虚拟机{2} --> (待添加关联虚拟机)     {0}(待添加虚拟机的所属资源)    {0}该用户的已关联角色{1}待添加虚拟机是否相同资源'.format(
                '-' * 10, ' ' * 7, ' ' * (_currentVm_maxLength - 10)).ljust(os.get_terminal_size()[0] - 20, '-'))
            for v0 in self.__my_open_api.lossVMUserDict.values():
                _num += 1
                print('{0}{id_}'.format(' ' * 2, id_=_num).ljust(16, ' '),
                      str(v0['user_name']).ljust(24, ' '),
                      str(v0['current_vm_list'] if v0['current_vm_list'] != '' else '""').ljust(_currentVm_maxLength + 6, ' '),
                      str(v0['loss_vm_name']).ljust(32, ' '),
                      str(v0['rc_name']).ljust(40 - len(str(v0['rc_name'])), ' '),
                      str(v0['role_name']).ljust(50 - len(str(v0['role_name']), ' ')),
                      "是, 该用户无法关联 '%s'虚拟机" % v0['loss_vm_name'] if '' else '')
                _get_roleName = self.__my_open_api.resourcesDict[v0['rc_name']]['role_name']
                _put_rcId = self.__my_open_api.resourcesDict[v0['rc_name']]['id']
                _put_vmId = self.__my_open_api.resourceVMDict[v0['loss_vm_name']]['_id']
                _put_userId = self.__my_open_api.usersDict[v0['user_name']]['id']
                _put_userGroupId = self.__my_open_api.usersDict[v0['user_name']]['group_id']
                _put_results.append({
                    'id': _num,
                    'vm_name': v0['loss_vm_name'],
                    'rc_name': v0['rc_name'],
                    'user_name': v0['user_name'],
                    'role_name': _get_roleName,
                    'put_vm_id': int(_put_vmId),
                    'put_rc_id': int(_put_rcId),
                    'put_user_id': int(_put_userId),
                    'put_usergroup_id': int(_put_userGroupId)
                })
        print('-' * int(os.get_terminal_size()[0]))
        return (200, _put_results)

    def loop_get_help(self, mode_: int):
        if mode_ == 1:
            print('当前模式：常规模式, 该模式可用命令：\n')
            print('show [-CSV] ID|ID1-ID2'.ljust(22, ' '), '查询指定序号的虚拟机, 支持n-m查询 (n < m).')
            print('ID: 查询指定的序号'.rjust(34, ' '))
            print('-CSV: 对比本地CSV数据\n'.rjust(39, ' '))
            print('loadcsv CSVFILE'.ljust(22, ' '), '加载本地CSV数据源. 拖拽CSV文件获取路径\n')
            print('check-bind-role'.ljust(22, ' '), '查看用户关联了虚拟机但没有关联角色的用户列表\n')
            print('check-lossvm-user'.ljust(22, ' '), '查看用户曾经关联过虚拟机但现在未关联的用户列表\n')
            print('check-idle-vm'.ljust(22, ' '), '查看闲置的虚拟机\n')
            print('mode'.ljust(22, ' '), '查看当前模式\n')
            print('config-mode-normal'.ljust(22, ' '), '进入常规模式\n')
            print('config-mode-pro'.ljust(22, ' '), '进入专业模式\n')
            print('help'.ljust(22, ' '), '查看帮助\n')
            print('exit|quit'.ljust(22, ' '), '退出程序')
            print('\n')
        elif mode_ == 2:
            print('当前模式：专业模式, 该模式可用命令：\n')
            print('csv-bind -VU[--vm-user]|-UR[--user-role] ID|ID1-ID2'.ljust(48, ' '), '对CSV数据源的指定序号的虚拟机进行关联操作, 支持n-m操作 (n < m).')
            print('-VU, --vm-user: 虚拟机关联用户'.rjust(72, ' '))
            print('-UR, --user-role: 用户关联角色\n'.rjust(74, ' '))
            print('csv-unbind [-L|--lock] ID|ID1-ID2'.ljust(48, ' '), '对CSV数据源的指定序号的虚拟机进行闲置[或锁定],支持n-m操作 (n < m).')
            print('-L: 锁定虚拟机\n'.rjust(59, ' '))
            print('show [-CSV] ID|ID1-ID2'.ljust(22, ' '), '查询指定序号的虚拟机, 支持n-m查询 (n < m).')
            print('ID: 查询指定的序号'.rjust(34, ' '))
            print('-CSV: 对比本地CSV数据\n'.rjust(39, ' '))
            print('loadcsv CSVFILE'.ljust(22, ' '), '加载本地CSV数据源. 拖拽CSV文件获取路径\n')
            print('check-bind-role'.ljust(22, ' '), '查看用户关联了虚拟机但没有关联角色的用户列表\n')
            print('check-lossvm-user'.ljust(22, ' '), '查看用户曾经关联过虚拟机但现在未关联的用户列表\n')
            print('check-idle-vm'.ljust(22, ' '), '查看闲置的虚拟机\n')
            print('mode'.ljust(22, ' '), '查看当前模式\n')
            print('config-mode-normal'.ljust(22, ' '), '进入常规模式\n')
            print('config-mode-pro'.ljust(22, ' '), '进入专业模式\n')
            print('config-mode-debug'.ljust(22, ' '), '进入Debugger模式\n')
            print('help'.ljust(22, ' '), '查看帮助\n')
            print('exit|quit'.ljust(22, ' '), '退出程序')
            print('\n')
        elif mode_ == 3:
            print('当前模式：Debugger模式, 该模式可用命令：\n')
            print('show-var [-D|--dict]|[-J|--json] [VAR]'.ljust(40, ' '), 'Debuuger程序时: 查看当前vars列表. 可选[参数0]查询, 无参数则显示vars.keys')
            print('-D, --dict: 以字典形式查询'.rjust(60, ' '))
            print('-J, --json: 以json形式查询\n'.rjust(63, ' '))
            print('exec'.ljust(22, ' '), 'Debugger程序时: 进入Python的exec命令执行模式\n')
            print('help'.ljust(22, ' '), '查看帮助\n')
            print('exit|quit'.ljust(22, ' '), '退出Debugger模式')

    def loop_get_help_show(self):
        print('Usage: show [OPTION] COMMAND')
        print('常规查询:查询指定序号的虚拟机, 支持n-m查询 (n < m).\n')
        print('  ID|ID1-ID2'.ljust(20, ' '), '查询指定的序号')
        print('  -csv|-CSV'.ljust(20, ' '), '对比CSV数据')
        print('eg:  show 1-10'.ljust(20, ' '), '查询序号1-10的虚拟机')
        print('eg:  show all'.ljust(20, ' '), '查询所有虚拟机')
        print('eg:  show -csv all'.ljust(20, ' '), '查询所有虚拟机, 并对比本地CSV数据源')

    def loop_get_help_rshow(self):
        print('Usage: rshow [OPTION] COMMAND')
        print('高级查询:查询指定序号的虚拟机, 支持特定条件查询, 支持合并查询, 支持模糊查询. (模糊查询只能按单个条件查询)\n')
        print('  ID|ID1-ID2'.ljust(20, ' '), '查询指定序号')
        print('  -csv|-CSV'.ljust(20, ' '), '对比CSV数据')
        print('  --like="var"'.ljust(20, ' '), "模糊查询. 以单个条件查询, 条件为空则无效")
        print('  --user="string"'.ljust(20, ' '), '按用户名称查询')
        print('  --vm="string"'.ljust(20, ' '), '按虚拟机名称查询')
        print('  --role="string"'.ljust(20, ' '), '按角色名称查询')
        print('  --resource="string"'.ljust(20, ' '), '按资源名称查询')
        print('eg:  rshow 1-10'.ljust(20, ' '), '查询序号1-10的虚拟机')
        print('eg:  rshow all'.ljust(20, ' '), '查询所有虚拟机')
        print('eg:  rshow -csv all'.ljust(20, ' '), '查询所有虚拟机, 并对比本地CSV数据源')
        print('eg:  rshow --user=test1'.ljust(20, ' '), '查询用户名为test1的记录')
        print('eg:  rshow --user=test1 --vm=cishi-0020'.ljust(20, ' '), '查询用户名为test1、虚拟机名称为cishi-0020的记录')
        print('eg:  rshow --user=test1 --vm=cishi --like=vm'.ljust(20, ' '), '以虚拟机名称为条件做模糊查询, 查询用户名为test1、虚拟机名称为cishi*的记录. ')
        print('eg:  rshow --vm=cishi --like=vm -csv'.ljust(20, ' '), '以虚拟机名称为条件做模糊查询, 查询虚拟机名称为cishi*的记录, 并对比本地CSV数据源')

    def loop_get_help_csvbind(self):
        print('Usage: csv-bind [OPTION] COMMAND')
        print('对CSV数据源的指定序号的虚拟机进行关联操作, 支持n-m操作 (n < m).\n')
        print('  -vu|-VU, --vm-user'.ljust(20, ' '), '虚拟机关联用户')
        print('  -ur|-UR, --user-role'.ljust(20, ' '), '用户关联角色\n')
        print('eg:  csv-bind --vm-user 1-10'.ljust(20, ' '), '对序号1-10进行虚拟机关联用户')
        print('eg:  csv-bind --user-role 11-20'.ljust(20, ' '), '对序号11-20进行用户关联角色')

    def loop_get_help_csvunbind(self):
        print('Usage: csv-unbind [OPTION] COMMAND')
        print('对CSV数据源的指定序号的虚拟机进行闲置[或锁定],支持n-m操作 (n < m).\n')
        print('  -l|-L, --lock'.ljust(20, ' '), '锁定虚拟机\n')
        print('eg:  csv-unbind 1-10'.ljust(20, ' '), '对序号1-10的虚拟机进行闲置')
        print('eg:  csv-unbind --lock 1-10'.ljust(20, ' '), '对序号1-10的虚拟机进行锁定')

    def loop_get_help_loadcsv(self):
        print('Usage: loadcsv COMMAND')
        print('加载本地CSV数据源. 拖拽CSV文件获取路径\n')
        print('  CSVFILE'.ljust(20, ' '), 'CSV文件的绝对路径\n')
        print('eg:  loadcsv C:\\1.csv'.ljust(20, ' '), '加载本地的CSV文件')

    def loop_get_help_checkBindRole(self):
        print('Usage: check-bind-role')
        print('查看并修复 关联了虚拟机但没有关联角色的用户列表.\n')
        print('eg:  check-bind-role')

    def loop_get_help_checkLossVMUser(self):
        print('Usage: check-lossvm-user')
        print('查看并修复 用户曾经关联过虚拟机但现在未关联.\n')
        print('eg:  check-lossvm-user')

    def loop_get_help_checkIdleVM(self):
        print('Usage: check-idle-vm')
        print('查看闲置的虚拟机.\n')
        print('eg:  check-idle-vm')

    def loop_get_help_checkMultBindVM(self):
        print('Usage: check-mult-bindvm')
        print('查看闲置的虚拟机.\n')
        print('eg:  check-mult-bindvm')

    def loop_get_help_debug_exec(self):
        print('Usage: exec')
        print('Debugger程序时: 进入Python的exec命令执行模式.')
        print('eg:  exec')

    def loop_get_help_debug_showVar(self):
        print('Usage: show-var [OPTION] [COMMAND]')
        print('Debuuger程序时: 查看当前vars列表, 可选[参数0]查询, 无参数则显示vars.keys\n')
        print('  -d|-D, --dict'.ljust(20, ' '), '以字典形式遍历查询')
        print('  -j|-J, --json'.ljust(20, ' '), '以json形式遍历查询')
        print('  VAR'.ljust(20, ' '), '按var的key参数进行查询\n')
        print('eg:  show-var'.ljust(20, ' '), '显示vars.keys')
        print('eg:  show-var self.__vdc_source'.ljust(20, ' '), '显示vdc数据源')
        print('eg:  show-var --dict self.__vdc_source'.ljust(20, ' '), '显示vdc数据源, 以字典形式查询')
        print('eg:  show-var --json self.__vdc_source'.ljust(20, ' '), '显示vdc数据源, 以json形式查询')

    def loop_get_debug_vars(self):
        self.debugSelfVars = [
            'self.%s' % v.replace('_LoopFunc', '') for v in self.__dict__.keys() if v != 'debugSelfVars' and v != 'debugOpenApiVars' and v != 'debugVarsDict'
        ]
        self.debugOpenApiVars = ['openapi.%s' % v.replace('_GetOpenAPI', '') for v in self.__my_open_api.__dict__.keys()]

    def loop_put_checkBindRole(self, put_roles_: list):
        ret_write_log = {}
        while True:
            try:
                _confirm_input = input("输入'yes'执行修复用户关联角色的操作, 输入'no'则退出不执行. ( yes / no ): ")
                if _confirm_input.lower() == 'yes':
                    break
                elif _confirm_input.lower() == 'no':
                    return
                else:
                    print("请输入'YES' or 'NO'")
            except Exception:
                print("请输入'YES' or 'NO'")
        for item in put_roles_:
            _put_userInfo = GetOpenAPI.OpenAPITools.ret_error(self.__my_open_api, 8, item['user_id'])
            _args = [
                _put_userInfo[1]['data']['id'], 'edit_user', _put_userInfo[1]['data']['name'], _put_userInfo[1]['data']['note'],
                _put_userInfo[1]['data']['passwd'], _put_userInfo[1]['data']['phone'], _put_userInfo[1]['data']['group_id'], _put_userInfo[1]['data']['enable'],
                _put_userInfo[1]['data']['area_id'], _put_userInfo[1]['data']['b_inherit_auth'], _put_userInfo[1]['data']['b_inherit_grpolicy'],
                _put_userInfo[1]['data']['grpolicy_id'],
                str(item['put_role_id']), 1, _put_userInfo[1]['data']['expire']
            ]
            put_result = None
            put_result = self.__my_open_api.put_usersId(_args)
            if put_result[1]['error_code'] == 0:
                _confirm_userId = GetOpenAPI.OpenAPITools.ret_error(self.__my_open_api, 8, item['user_id'])
                if _confirm_userId[1]['data']['roles']:
                    _new_role_name = item['put_role_name']
                    self.__my_open_api.usersDict[item['user_name']]['role_names'] = _new_role_name
                    self.__my_open_api.rolesDict[item['rc_name']]['relation_uids'] += ',%s' % item['user_id'] if self.__my_open_api.rolesDict[
                        item['rc_name']]['relation_uids'] else item['user_id']
                    self.__my_open_api.update_VDCInfo_for_source()
                    self.__my_open_api.update_repairInfo()
                    self.__my_open_api.update_writeJson(0)
                    self.update_init()
                    print('用户关联角色修复: 用户[ {0} ] -- 关联角色[ {1} ] '.format(item['user_name'], item['put_role_name']).ljust(45, '-'),
                          '耗时: %s s' % str(put_result[2]))
                else:
                    _new_role_name = ''
                    print('用户关联角色失败: {0} '.format(put_result[1]['error_message']))
            else:
                print('用户 %s 关联角色失败:' % item['user_name'], put_result[1]['error_message'])

            ret_write_log[item['user_name']] = {
                '响应代码': put_result[0] if put_result[0] == 400 else put_result[1]['error_code'],
                '响应结果': put_result[1] if put_result[0] == 400 else put_result[1]['error_message'],
                '关联信息': {
                    '虚拟机名称': item['vm_name'],
                    '资源名称': item['rc_name'],
                    '用户名称': item['user_name'],
                    '角色名称': _new_role_name if '_new_role_name' in vars().keys() else ''
                }
            }
        GetOpenAPI.OpenAPITools.WriteJson(ret_write_log, self.__my_open_api.checkFilePath, '用户关联角色-响应结果')

    def loop_put_checkLossVMUser(self, put_bindUser_: list):
        ret_write_log = {}
        while True:
            try:
                _confirm_input = input("输入'yes'执行修复虚拟机关联用户的操作, 输入'no'则退出不执行. ( yes / no ): ")
                if _confirm_input.lower() == 'yes':
                    break
                elif _confirm_input.lower() == 'no':
                    return
                else:
                    print("请输入'YES' or 'NO'")
            except Exception:
                print("请输入'YES' or 'NO'")
        for item in put_bindUser_:
            print('item:', item, '\n')
            put_result = None
            _put_ifBind = GetOpenAPI.OpenAPITools.ret_error(self.__my_open_api, 9, [item['put_rc_id'], item['put_usergroup_id'], 1, 100])
            print('_put_ifBind:', _put_ifBind, '\n')
            if str(item['put_user_id']) in [v['_id'] for v in _put_ifBind[1]['data']['data']]:
                _args = [item['put_rc_id'], item['put_vm_id'], 1, item['put_user_id'], item['user_name'], 1]
                print('_args:', _args)
                put_result = self.__my_open_api.put_servers_bind_users(_args)
                print('put_result:', put_result)
                if put_result[1]['error_code'] == 0:
                    _confirm_vmInfo = GetOpenAPI.OpenAPITools.ret_error(self.__my_open_api, 10, item['user_name'])
                    if item['put_vm_id'] in [v['vm_id'] for v in _confirm_vmInfo[1]['data']]:
                        self.__my_open_api.vdcSource[item['vm_name']]['vm_apply_user'] = item['user_name']
                        self.__my_open_api.update_sourceInfo_for_VDC()
                        self.__my_open_api.update_repairInfo()
                        self.__my_open_api.update_writeJson(0)
                        self.update_init()
                        print('序号 {0}: 虚拟机关联用户修复: 虚拟机[ {1} ] -- 关联用户[ {2} ] '.format(item['id'], item['vm_name'], item['user_name']).ljust(45, '-'),
                              '耗时: %s s' % str(put_result[2]))
                    else:
                        print('序号 {0}: 虚拟机关联用户失败: {1} '.format(item['id'], put_result[1]['error_message']))
                else:
                    print('序号 {0}: 虚拟机关联用户 {1} 失败:'.format(item['id'], item['user_name']), put_result[1]['error_message'])
            else:
                print('序号 {0}: 用户({1})关联虚拟机({2})失败, ErrorMsg -- 用户未关联角色: {3}'.format(item['id'], item['user_name'], item['vm_name'], item['role_name']))

            ret_write_log[item['user_name']] = {
                '响应代码': '400' if put_result is None else put_result[1]['error_code'],
                '响应结果': '({0})用户未关联角色({1})'.format(item['user_name'], item['role_name']) if put_result is None else put_result[1]['error_message'],
                '关联信息': {
                    '虚拟机名称': item['vm_name'],
                    '资源名称': item['rc_name'],
                    '用户名称': item['user_name'],
                    '角色名称': item['role_name']
                }
            }
        GetOpenAPI.OpenAPITools.WriteJson(ret_write_log, self.__my_open_api.checkFilePath, '虚拟机关联用户-响应结果')

    def loop_ret_id(self, num_str, commend_: str):
        try:
            if num_str == 'all':
                return (-1, -1, -1)
            elif '-' in num_str:
                mult_num = num_str.split('-')
                if len(mult_num) == 2:
                    if ((mult_num[0][-1] != ' ' and mult_num[1][0] != ' ')):
                        start_n = int(mult_num[0])
                        stop_n = int(mult_num[1])
                        if start_n > stop_n:
                            print('%s: ID的起始值必须小于终止值.' % str(commend_))
                            return None
                        else:
                            return (start_n, stop_n, 1)
                    else:
                        print("{0}: 无效的指令 -- '{1}'".format(commend_, num_str))
                        print("尝试 '%s --help' 获取更多帮助信息." % str(commend_))
                        return None
                else:
                    print("{0}: 无效的指令 -- '{1}'".format(commend_, num_str))
                    print("尝试 '%s --help' 获取更多帮助信息." % str(commend_))
                    return None
            else:
                if int(num_str):
                    return (int(num_str), -1, 0)
        except Exception as e:
            print("{0}: 错误信息 -- '{1}'".format(commend_, e))
            print("尝试 '%s --help' 获取更多帮助信息." % str(commend_))
            return None

    def completer_tab(self, text, state):
        if self.currentMode == 1:
            options = [cmd for cmd in self.normalCommands if cmd.startswith(text)]
        elif self.currentMode == 2:
            options = [cmd for cmd in self.proCommands if cmd.startswith(text)]
        elif self.currentMode == 3:
            options = [cmd for cmd in self.debugCommands if cmd.startswith(text)]
        elif self.currentMode == 4:
            options = [cmd for cmd in self.execCommands if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None
