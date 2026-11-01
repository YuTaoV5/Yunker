#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2026-03-09 10:19
@Author  : Ternura_xiang
@File    : file_manager.py
@Project : OmniCtrl
@Desc    : 文件管理器
"""

import json


class FileManager:
    def __init__(self):
        pass

    def save_omni(self, path:str, data: dict):
        """
        保存清单
        :param manifest: 清单对象
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving omni to {path}: {e}")

    def load_omni(self, path: str) -> dict | None:
        """
        加载清单
        :param path: 项目文件路径
        :return: dict | None
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                print(f"Error loading omni from {path}: root is not object")
            return data
        except Exception as e:
            print(f"Error loading omni from {path}: {e}")
        return None
