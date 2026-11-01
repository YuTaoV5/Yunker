#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-22 14:25
@Author  : Ternura_xiang
@File    : loader.py
@Project : OmniCtrl
@Desc    : 模块加载器
"""

import json, zlib
from pathlib import Path
from typing import Optional

from ..models import *
from ..common import DataType


class ManifestLoader:
    """
    模块清单加载器

    Attributes:
        file_path: 清单文件路径
        __manifest: 加载后的清单对象
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.__manifest: Optional[Manifest] = None
        if not self.__load():
            raise ValueError("Manifest loading failed.")

    @property
    def manifest(self) -> Optional[Manifest]:
        """ 获取加载后的清单对象 """
        if self.__manifest is not None:
            return self.__manifest
        else:
            raise ValueError("Manifest not loaded Successfully.")

    def __calc_hash(self, key: str) -> int:
        """生成一个跨平台稳定的 32位 Hash"""
        return zlib.crc32(key.encode('utf-8')) & 0xFFFFFFFF

    def __load(self):
        """ 加载清单文件 """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {self.file_path}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # 1.创建Manifest实例
            self.__manifest = Manifest()

            # 2.解析 Modules
            for i, module in enumerate(raw_data.get("CtrlModules")):
                # 2.1.解析模块类型
                try:
                    temp_module_type = module["Type"]
                except ValueError:
                    print(f"[Loader Error] Missing Type for Module {i}")
                    continue
                # 2.2.解析模块名称
                try:
                    temp_module_name = module["Name"]
                except KeyError:
                    print(f"[Loader Error] Missing Name for Module {i}")
                    continue
                # 2.3.解析模块初始化参数
                try:
                    temp_module_init = module["Init"]
                except KeyError:
                    print(f"[Loader Error] Missing Init for Module {i}")
                    continue
                # 2.4.创建模块实例
                temp_module = Module(
                    father_name=temp_module_name,
                    type_id=i,
                )
                temp_module.type_name = temp_module_type
                temp_module.type_init = temp_module_init

                # 3.解析模块参数
                for j, param in enumerate(module["Params"]):
                    # 3.1.解析模块参数类型
                    try:
                        temp_param_type = DataType(param["Type"])
                    except ValueError:
                        print(f"[Loader Error] Invalid DataType: {param['Type']}")
                        continue
                    # 3.2.解析模块参数名称
                    try:
                        temp_param_name = param["Name"]
                    except KeyError:
                        print(f"[Loader Error] Missing Name for Param {j} in Module {i}")
                        continue
                    # 3.3.生成模块参数实例并添加到模块
                    temp_param = ModuleParam(
                        name=temp_param_name,
                        param_type=temp_param_type,
                        id=j,
                    )
                    temp_module.add_param(temp_param)   # 添加参数到模块
                self.__manifest.modules.append(temp_module)  # 添加模块到清单

            # 4.解析 ExternalParams
            for i, param in enumerate(raw_data.get("Params")):
                # 4.1.解析外部变量参数类型
                try:
                    temp_param_type = DataType(param["Type"])
                except ValueError:
                    print(f"[Loader Error] Invalid DataType: {param['Type']}")
                    continue
                # 4.2.解析外部变量名称
                try:
                    temp_param_name = param["Name"]
                except KeyError:
                    print(f"[Loader Error] Missing Name for Param {i}")
                    continue
                # 4.3.生成外部变量实例并添加到清单
                temp_param = ExternalParam(
                    name=temp_param_name,
                    param_type=temp_param_type,
                    hash=self.__calc_hash(temp_param_name),
                )
                self.__manifest.ext_params.append(temp_param)    # 添加外部变量到清单

            # 5.解析 OutputParams
            for i, param in enumerate(raw_data.get("OutputParams")):
                # 5.1.解析外部变量名称
                try:
                    temp_param_name = param["Name"]
                except KeyError:
                    print(f"[Loader Error] Missing Name for Param {i}")
                    continue
                # 5.2.生成外部变量实例并添加到清单
                temp_param = OutputParam(
                    name=temp_param_name,
                    hash=self.__calc_hash(temp_param_name),
                )
                self.__manifest.out_params.append(temp_param)  # 添加外部变量到清单

            # 6. 解析信号类型
            try:
                self.__manifest.signal_type = DataType(raw_data["signal_type"])
            except ValueError:
                print(f"[Loader Error] Invalid SignalType: {raw_data['signal_type']}")
                return False

            # 7. 计算清单哈希值
            self.__manifest.hash = self.__calc_hash(json.dumps(raw_data, ensure_ascii=False))

            # 8.解析完成
            return True

        # 文件打开失败
        except Exception as e:
            print(f"[Loader Error] {e}")
            return False
