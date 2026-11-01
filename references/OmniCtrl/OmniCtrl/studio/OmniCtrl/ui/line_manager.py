#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-12-08 22:23
@Author  : Ternura_xiang
@File    : line_manager.py
@Project : OmniCtrl
@Desc    : 连线管理器
"""

import dearpygui.dearpygui as dpg
from ..models import Module, ExternalParam, OutputParam
from ..core.graph import ControlGraph, GraphError


class LineManager:
    """
    连线管理器

    Attributes:
        _links: 存储连线信息的字典，键为连线ID，值为连线信息字典
            连线信息字典包含以下键值对:
            - source: 源参数对象
            - target: 目标参数对象
    """

    def __init__(self, control_graph: ControlGraph):
        """
        初始化连线管理器
        """
        self.control_graph = control_graph
        self.__links = {}

    def add_link(self, sender, app_data):
        """
        添加连线
        :param sender: 发送者ID
        :param app_data: 应用数据，包含连线信息
        """
        source, target = app_data

        # 1. 获取源参数和目标参数的用户数据
        source_data = dpg.get_item_user_data(source)
        target_data = dpg.get_item_user_data(target)
        is_out_param = isinstance(target_data, OutputParam)
        # 检查目标参数是否存在, 解决环境报错
        if is_out_param:
            if target_data.connect:
                return
        else:
            if target_data is None or not isinstance(target_data, dict) or "param" not in target_data:
                return
            # 检查目标参数是否为静态参数(检查已连线)
            if not target_data["param"].is_static:
                return
        target_node_id = target_data.hash if is_out_param else target_data["module_id"]
        target_param_id = 255 if is_out_param else target_data["param_id"]

        # 2. 更新数据
        try:
            if isinstance(source_data, Module):
                self.control_graph.add_edge(source_data.id, False,
                                            target_node_id,
                                            target_param_id)
            elif isinstance(source_data, ExternalParam):
                self.control_graph.add_edge(source_data.hash, True,
                                            target_node_id,
                                            target_param_id)
            else:
                print("Error: 源参数必须为模块或外部参数")
                return
        except GraphError as e:
            print(f"[LineManager] Add link rejected: {e}")
            return

        # 3. 更新UI
        link_id = dpg.add_node_link(source, target, parent=sender)  # 添加连线到UI
        self.__links[link_id] = app_data   # 存储连线信息

        # 4. 隐藏目标参数的UI组件
        if not is_out_param:
            child = dpg.get_item_children(target)[1][0]
            child_child = dpg.get_item_children(child)[1][1]
            dpg.hide_item(child_child)

    def del_link(self, sender, app_data):
        """
        删除连线
        :param sender: 发送者ID
        :param app_data: 应用数据，包含连线ID
        """
        link_id = app_data

        # 1. 获取连线信息
        if link_id not in self.__links:
            dpg.delete_item(link_id)    # 野线，直接删除
            return
        source, target = self.__links[link_id]
        source_data = dpg.get_item_user_data(source)
        target_data = dpg.get_item_user_data(target)
        if target_data is None:
            return
        is_out_param = isinstance(target_data, OutputParam)
        target_node_id = target_data.hash if is_out_param else target_data["module_id"]
        target_param_id = 255 if is_out_param else target_data["param_id"]

        # 2. 更新数据
        try:
            if isinstance(source_data, Module):
                self.control_graph.remove_edge(source_data.id, False,
                                            target_node_id,
                                            target_param_id)
            elif isinstance(source_data, ExternalParam):
                self.control_graph.remove_edge(source_data.hash, True,
                                            target_node_id,
                                            target_param_id)
            else:
                print("Error: 源参数必须为模块或外部参数")
                return
        except GraphError as e:
            print(f"[LineManager] Remove link rejected: {e}")
        
        # 3. 维护连线信息
        del self.__links[link_id]
        # 4. 更新UI
        dpg.delete_item(link_id)  # 删除连线UI
        # 5. 恢复输入框
        if not is_out_param:
            child = dpg.get_item_children(target)[1][0]
            child_child = dpg.get_item_children(child)[1][1]
            dpg.show_item(child_child)

    def get_links(self):
        return self.__links

    def clear_links(self):
        self.__links.clear()
