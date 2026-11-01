#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-12-04 0:02
@Author  : Ternura_xiang
@File    : main.py
@Project : OmniCtrl
@Desc    : 主程序
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OmniCtrl.services.loader import ManifestLoader
from OmniCtrl.ui.main_window import MainWindow
from OmniCtrl.core.graph import ControlGraph


def main():
    """
    主函数
    """
    # 加载清单文件
    manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "definitions", "omni_manifest.json")
    loader = ManifestLoader(manifest_path)
    control_graph = ControlGraph()
    # 初始化主窗口
    ui = MainWindow(loader.manifest, control_graph)
    ui.show()
    control_graph.export_binary_manifest(loader.manifest.signal_type)


if __name__ == "__main__":
    main()
