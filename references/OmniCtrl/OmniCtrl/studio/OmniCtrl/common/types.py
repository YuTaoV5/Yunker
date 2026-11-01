#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-20 16:58
@Author  : Ternura_xiang
@File    : types.py
@Project : OmniCtrl
@Desc    : 定义项目通用的枚举及常量
"""

from enum import Enum


class DataType(Enum):
    """
    C 语言数据类型映射
    @Note: 应与C语言端定义的枚举名保持一致
    """
    SIGNAL_T = "CTRL_PARAM_SIGNAL_T"
    SIZE_T = "CTRL_PARAM_SIZE_T"
    CHAR = "CTRL_PARAM_CHAR"
    FLOAT = "CTRL_PARAM_FLOAT"
    DOUBLE = "CTRL_PARAM_DOUBLE"
    SHORT = "CTRL_PARAM_SHORT"
    INT = "CTRL_PARAM_INT"
    LONG = "CTRL_PARAM_LONG"
