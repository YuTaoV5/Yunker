#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-20 17:20
@Author  : Ternura_xiang
@File    : schema.py
@Project : OmniCtrl
@Desc    : 定义 OmniCtrl 的核心数据结构与校验规则
"""

from dataclasses import dataclass, field
from typing import Any

from ..common import DataType


@dataclass
class ModuleParam:
    """
    模块参数定义
    模块参数分为静态参数与动态参数两种:
    -> 静态参数一经设置，不可改变。
    -> 动态参数需连接至其他两类参数:
        -> 1. 模块输出(此时_value为该模块输出)
        -> 2. 其他动态参数(此时_value为该参数的哈希值)

    Attributes:
        name: 参数名
        param_type: 参数数据类型
        id: 参数id
        __value: 参数值
        __is_static: 标志参数是否为静态参数(默认True)
        __is_hash: 标志_value是否为哈希值(仅在动态参数下有效)
    """
    name: str
    param_type: DataType
    id: int
    __value: Any = field(default=0, init=False)
    __is_static: bool = field(default=True, init=False)
    __is_hash: bool = field(default=False, init=False)

    # ------------------------- 属性访问器 -------------------------
    @property
    def value(self):
        """ 获取参数值 """
        return self.__value

    @property
    def is_static(self):
        """ 获取参数是否为静态参数标志 """
        return self.__is_static

    @property
    def is_hash(self):
        """ 获取参数值是否为哈希值 """
        return self.__is_hash

    # ------------------------- 参数设置方法 -------------------------
    def disconnect(self):
        """ 断开参数连接 """
        self.__is_static = True
        self.__is_hash = False

    def set_static_value(self, value: Any):
        """ 设置静态参数值 """
        self.__value = value
        self.__is_static = True
        self.__is_hash = False

    def connect_output(self, module_id: int):
        """
        连接至模块输出
        :param module_id: 模块ID
        """
        self.__value = module_id
        self.__is_static = False
        self.__is_hash = False

    def connect_param(self, param_hash: int):
        """
        连接至其他动态参数(参数哈希值)
        :param param_hash: 参数哈希值
        """
        self.__value = param_hash
        self.__is_static = False
        self.__is_hash = True

    def to_dict(self) -> dict:
        """
        将参数转换为字典
        :return: 参数字典表示
        """
        return {
            "name": self.name,
            "value": self.__value,
            "is_static": self.__is_static,
            "is_hash": self.__is_hash
        }

    def __repr__(self):
        """ 模块参数表示字符串 """
        if self.is_static:
            return f"{self.name}: {self.value} ({self.param_type})"
        elif self.is_hash:
            return f"{self.name}: {self.value} (HASH)"
        else:
            return f"{self.name}: module id {self.value}`s output"


@dataclass
class Module:
    """
    模块定义

    Attributes:
        father_name: 模块名(模板名:如PID)
        type_id: 模块类型id
        __name: 模块名(每个实例的单独标识名)
        __type_name: 模块类型名
        __type_init: 模块C端初始化函数(仅在开发者模块下显示)
        __id: 模块ID
        __params: 参数类列表
        __params_num: 参数数量
    """
    father_name: str
    type_id: int
    __name: str = field(default="unknown", init=False)
    __type_name: str = field(default="unknown", init=False)
    __type_init: str = field(default="unknown", init=False)
    __id: int = field(default=-1, init=False)
    __params: list[ModuleParam] = field(default_factory=list, init=False)
    __params_num: int = field(default=0, init=False)

    # ------------------------- 属性访问器 -------------------------
    @property
    def type_name(self):
        """ 获取模块类型名 """
        return self.__type_name

    @type_name.setter
    def type_name(self, value: str):
        """ 设置模块类型名 """
        self.__type_name = value

    @property
    def type_init(self):
        """ 获取模块C端初始化函数名 """
        return self.__type_init

    @type_init.setter
    def type_init(self, value: str):
        """ 设置模块C端初始化函数名 """
        self.__type_init = value

    @property
    def id(self):
        """ 获取模块ID """
        return self.__id

    @id.setter
    def id(self, value: int):
        """ 设置模块ID """
        self.__id = value

    @property
    def params_num(self):
        """ 获取参数数量 """
        self.__params_num = len(self.__params)
        return self.__params_num

    # ------------------------- 参数获取方法 -------------------------
    def set_name(self, value: str):
        """
        设置模块名
        :param value: 模块名(每个实例的单独标识名)
        """
        self.__name = value

    def get_name(self) -> str:
        """
        获取模块名
        :return: 模块名(每个实例的单独标识名)
        """
        return self.__name

    def set_param(self, param_id: int, value: Any):
        """
        设置模块参数值
        :param param_id: 参数ID
        :param value: 参数值
        """
        for param in self.__params:
            if param.id == param_id:
                param.set_static_value(value)
                return
        raise ValueError(f"Parameter ID {param_id} not found in module {self.father_name}")

    def get_param(self, param_id: int) -> ModuleParam:
        """
        获取模块参数
        :param param_id: 参数ID
        :return: 参数对象
        """
        for param in self.__params:
            if param.id == param_id:
                return param
        raise ValueError(f"Parameter ID {param_id} not found in module {self.father_name}")

    def set_param_by_name(self, param_name: str, value: Any):
        """
        设置模块参数值
        :param param_name: 参数名
        :param value: 参数值
        """
        for param in self.__params:
            if param.name == param_name:
                param.set_static_value(value)
                return
        raise ValueError(f"Parameter name {param_name} not found in module {self.father_name}")

    def get_param_by_name(self, param_name: str) -> ModuleParam:
        """
        获取模块参数
        :param param_name: 参数名
        :return: 参数对象
        """
        for param in self.__params:
            if param.name == param_name:
                return param
        raise ValueError(f"Parameter name {param_name} not found in module {self.father_name}")

    def get_changed_params(self) -> list[ModuleParam]:
        """
        获取所有已改变的参数
        :return: 已改变参数列表
        """
        return [param for param in self.__params if (param.value != 0 or not param.is_static)]

    def add_param(self, param: ModuleParam):
        """
        添加模块参数
        :param param: 参数对象
        """
        # 检查参数ID是否重复
        if any(p.id == param.id for p in self.__params):
            raise ValueError(f"Parameter ID {param.id} already exists in module {self.father_name}")
        self.__params.append(param)

    def to_dict(self) -> dict:
        """
        将模块转换为字典
        :return: 模块字典表示
        """
        return {
            "father_name": self.father_name,
            "name": self.__name,
            "id": self.__id,
            "params": [param.to_dict() for param in self.__params],
        }

    def __repr__(self):
        """ 获取模块字符串表示 """
        return f"{self.father_name} (Type: {self.__type_name}, ID: {self.__id})"


@dataclass
class ExternalParam:
    """
    外部参数定义

    Attributes:
        name: 参数名
        param_type: 参数类型
        hash: 参数哈希值
    """
    name: str
    param_type: DataType
    hash: int

    def __repr__(self):
        """ 获取外部参数字符串表示 """
        return f"{self.name} Type: {self.param_type.name} (Hash: {self.hash})"


@dataclass
class OutputParam:
    """
    输出参数定义

    Notes: 与外部参数具有相同的属性
    """
    name: str
    hash: int
    __connect: bool = field(default=False, init=False)
    __value: int = field(default=None, init=False)

    # ------------------------- 属性访问器 -------------------------
    @property
    def value(self):
        """ 获取参数值 """
        return self.__value

    @property
    def connect(self):
        """ 获取连线状态 """
        return self.__connect

    # ------------------------- 参数设置方法 -------------------------
    def disconnect(self):
        self.__connect = False

    def connect_output(self, module_id: int):
        """
        连接至模块输出
        :param module_id: 模块ID
        """
        self.__value = module_id
        self.__connect = True

    def __repr__(self):
        """ 获取输出参数字符串表示 """
        return f"{self.name}(Hash: {self.hash})"

@dataclass
class Manifest:
    """
    清单定义

    Attributes:
        modules: 可用模块列表
        ext_params: 外部参数列表
        signal_type: 信号类型
    """
    modules: list[Module] = field(default_factory=list, init=False)
    ext_params: list[ExternalParam] = field(default_factory=list, init=False)
    out_params: list[OutputParam] = field(default_factory=list, init=False)
    signal_type: DataType = field(init=False)
    hash: int = field(init=False)
