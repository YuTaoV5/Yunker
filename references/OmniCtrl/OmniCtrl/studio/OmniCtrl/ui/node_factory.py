#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-12-06 23:49
@Author  : Ternura_xiang
@File    : node_factory.py
@Project : OmniCtrl
@Desc    : 节点工厂模块
"""

import re
import dearpygui.dearpygui as dpg
from ..models import Module, ExternalParam, OutputParam
from ..models.schema import DataType
from ..core.graph import ControlGraph


class NodeFactory:
    """
    节点工厂类

    Attributes:
        editor_tag: 编辑器标签
        __input_shape: 输入端口形状
        __output_shape: 输出端口形状
        __input_min_width: 输入端口最小宽度
        __modules: 模块集合
    """

    def __init__(self, editor_tag: str, control_graph: ControlGraph):
        self.editor_tag = editor_tag
        self.control_graph = control_graph
        self.__input_shape = dpg.mvNode_PinShape_CircleFilled
        self.__output_shape = dpg.mvNode_PinShape_TriangleFilled
        self.__input_min_width = 80

    def create_module_node(self, template: Module, node_id: int = None):
        """
        创建节点

        Args:
            template: 模块对象
        """
        # -----解决对齐/解析参数名-----
        # 1. 收集所有参数名(自动解析并保留_PORT_后的部分)
        name = []
        max_len = 0
        module = self.control_graph.add_node(template, node_id=node_id)
        for i in range(module.params_num):
            name.append(module.get_param(i).name)
            if "_PORT_" in name[-1]:
                name[-1] = re.split(r"_PORT_", name[-1])[-1].lower()
        # 2. 计算最大参数名长度
        for i in name:
            max_len = max(max_len, len(i))
        max_len = max(max_len, len(module.father_name))
        max_len = self.__input_min_width + max_len * 7

        # -----创建节点-----
        with dpg.node(label=module.father_name, parent=self.editor_tag, user_data=module,
                        tag=f"node_{module.id}"):
            # 1. 创建名称静态文本端口
            with dpg.node_attribute(label="Name",
                                    attribute_type=dpg.mvNode_Attr_Static):
                with dpg.group(horizontal=True):
                    dpg.add_text("Name:")
                    dpg.add_input_text(default_value=module.father_name,
                                        width=max_len - len("Name:") * 7,
                                        callback=lambda sender, app_data: module.set_name(app_data))
            # 2. 创建输入端口
            for i in range(module.params_num):
                # 创建输入端口
                with dpg.node_attribute(label=name[i], shape=self.__input_shape,
                                        user_data={
                                            "param_id": i,
                                            "param": module.get_param(i),
                                            "module_id": module.id,
                                        },
                                        attribute_type=dpg.mvNode_Attr_Input):
                    with dpg.group(horizontal=True):
                        dpg.add_text(name[i])
                        # 根据不同参数类型添加不同的输入端口
                        if module.get_param(i).param_type in [DataType.FLOAT, DataType.SIGNAL_T,
                                                              DataType.DOUBLE]:
                            dpg.add_input_double(width=max_len - len(name[i]) * 7, step=0,
                                                 user_data=module.get_param(i),
                                                 callback=lambda sender, app_data, user_data:
                                                 module.set_param_by_name(user_data.name, app_data))
                        elif module.get_param(i).param_type in [DataType.SIZE_T, DataType.CHAR,
                                                                DataType.INT, DataType.SHORT,
                                                                DataType.LONG]:
                            dpg.add_input_int(width=max_len - len(name[i]) * 7, step=0,
                                              user_data=module.get_param(i),
                                              callback=lambda sender, app_data, user_data:
                                              module.set_param_by_name(user_data.name, app_data))
            # 3. 创建输出端口
            with dpg.node_attribute(label="Output", user_data=module,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=self.__output_shape):
                dpg.add_text("Output".rjust(int(max_len / 7), " "))

        return module

    def create_param_node(self, param: ExternalParam):
        """
        创建外部参数节点

        Args:
            param: 外部参数对象
        """
        # 1. 注册到 ControlGraph，确保外部参数可参与连线校验
        self.control_graph.add_ext_param(param)
        # 2. 使用稳定 tag，避免重复初始化时实例重叠
        node_tag = f"ext_param_node_{param.hash:08X}"
        output_tag = f"{node_tag}_output"
        if dpg.does_item_exist(node_tag):
            dpg.set_item_user_data(node_tag, param)
            dpg.set_item_label(node_tag, param.name)
            if dpg.does_item_exist(output_tag):
                dpg.set_item_user_data(output_tag, param)
            return node_tag

        with dpg.node(tag=node_tag, label=param.name, user_data=param, parent=self.editor_tag):
            # 创建输出端口
            with dpg.node_attribute(tag=output_tag, label="Output", user_data=param,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=self.__output_shape):
                dpg.add_text("Output")
        return node_tag

    def create_output_node(self, param: OutputParam):
        """
        创建输出参数节点

        Args:
            param: 输出参数对象
        """
        # 1. 注册到 ControlGraph，确保输出参数可参与连线校验
        self.control_graph.add_out_param(param)
        # 2. 使用稳定 tag，避免重复初始化时实例重叠
        node_tag = f"out_param_node_{param.hash:08X}"
        input_tag = f"{node_tag}_output"
        if dpg.does_item_exist(node_tag):
            dpg.set_item_user_data(node_tag, param)
            dpg.set_item_label(node_tag, param.name)
            if dpg.does_item_exist(input_tag):
                dpg.set_item_user_data(input_tag, param)
            return node_tag

        with dpg.node(tag=node_tag, label=param.name, user_data=param, parent=self.editor_tag):
            # 创建输入端口
            with dpg.node_attribute(tag=input_tag, label="Input", user_data=param,
                                    attribute_type=dpg.mvNode_Attr_Input,
                                    shape=self.__input_shape):
                dpg.add_text("Input")
        return node_tag
