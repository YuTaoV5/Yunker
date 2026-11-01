#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-24 11:12
@Author  : Ternura_xiang
@File    : main_window.py
@Project : OmniCtrl
@Desc    : 主窗口模块
"""

from typing import Dict
import dearpygui.dearpygui as dpg
from ..services.file_manager import FileManager
from ..models import Manifest, Module
from ..core.graph import ControlGraph
from .theme_manager import ThemeManager
from .toolbar_builder import build_toolbar
from .node_factory import NodeFactory
from .line_manager import LineManager


class MainWindow:
    """
    主窗口类
    """

    def __init__(self, manifest: Manifest, control_graph: ControlGraph):
        """
        初始化主窗口

        Args:
            manifest (Manifest): 模块清单
            control_graph (ControlGraph): 控制图
        """
        self.width = 800
        self.height = 600
        self.title = "OmniCtrl Studio"
        self.manifest = manifest
        self.control_graph = control_graph
        self.file_manager = FileManager()
        self.current_project_path = None

        # 公开的 Tag，供外部管理器使用
        self.root_tag = "Primary Window"
        self.toolbar_tag = "win_toolbar_container"  # 工具栏容器
        self.editor_tag = "main_node_editor"  # 编辑器容器
        # 初始化节点工厂
        self.node_factory = NodeFactory(self.editor_tag, self.control_graph)
        self.control_graph.signal_type = self.manifest.signal_type
        # 初始化连线管理器
        self.line_manager = LineManager(self.control_graph)
        # 外部/输出参数节点索引（hash -> node_tag）
        self.ext_param_node_tags: Dict[int, str] = {}
        self.out_param_node_tags: Dict[int, str] = {}

    def setup_dpg_context(self):
        """初始化 DPG 上下文和视口"""
        dpg.create_context()
        ThemeManager.apply_modern_theme()
        dpg.create_viewport(title=self.title, width=self.width, height=self.height)
        dpg.setup_dearpygui()

    def save_project(self, path: str):
        """
        保存项目
        :param path: 项目文件路径
        """
        # 1. 强制同步一帧，防止获取坐标崩溃
        dpg.split_frame()

        # 2. 收集节点信息
        omni = {
            "Metadata": {
                "ManifestHash": self.manifest.hash
            },
            "Nodes": {},
            "Links": self.control_graph.edges
        }
        for node_id, module in self.control_graph.nodes.items():
            omni["Nodes"][node_id] = module.to_dict()
            if dpg.does_item_exist(f"node_{module.id}"):
                omni["Nodes"][node_id]["Pos"] = dpg.get_item_pos(f"node_{module.id}")
        self.file_manager.save_omni(path, omni)

    def import_project(self, path: str):
        """
        导入项目
        :param path: 项目文件路径
        :return: bool
        """
        # 1. 加载项目文件
        omni = self.file_manager.load_omni(path)
        if omni is None:
            print(f"[Import] Failed to load project: {path}")
            return False

        try:
            # 2. 校验项目数据
            metadata = omni.get("Metadata")
            nodes_raw = omni.get("Nodes")
            links_raw = omni.get("Links")
            if not isinstance(metadata, dict) or metadata.get("ManifestHash") != self.manifest.hash:
                raise ValueError("ManifestHash mismatch.")
            if not isinstance(nodes_raw, dict) or not isinstance(links_raw, list):
                raise ValueError("Project data is invalid.")

            # 3. 重置编辑区
            if dpg.does_item_exist(self.editor_tag):
                dpg.delete_item(self.editor_tag, children_only=True)
            self.control_graph.reset()
            self.line_manager.clear_links()
            for out_param in self.manifest.out_params:
                out_param.disconnect()
            self.control_graph.out_params.clear()
            self.ext_param_node_tags.clear()
            self.out_param_node_tags.clear()
            self.__layout_ext_params()
            self.__layout_out_params()

            module_templates = {module.father_name: module for module in self.manifest.modules}
            sorted_nodes = sorted((int(node_id), node_data) for node_id, node_data in nodes_raw.items())

            for node_id, node_data in sorted_nodes:
                if not isinstance(node_data, dict):
                    raise ValueError(f"Node entry is invalid: {node_id}")
                if int(node_data.get("id", node_id)) != node_id:
                    raise ValueError(f"Node ID mismatch: {node_id}")

                father_name = node_data.get("father_name")
                template = module_templates.get(father_name)
                if template is None:
                    raise ValueError(f"Invalid module template: {father_name}")

                params_data = node_data.get("params")
                if not isinstance(params_data, list) or len(params_data) != template.params_num:
                    raise ValueError(f"Param count mismatch for node={node_id}")

                for param_id, param_data in enumerate(params_data):
                    if not isinstance(param_data, dict):
                        raise ValueError(f"Param entry invalid for node={node_id}, param={param_id}")
                    if param_data.get("name") != template.get_param(param_id).name:
                        raise ValueError(f"Param name mismatch for node={node_id}, param={param_id}")

                module = self.node_factory.create_module_node(template, node_id=node_id)
                if isinstance(node_data.get("name"), str):
                    module.set_name(node_data.get("name"))

                for param_id, param_data in enumerate(params_data):
                    if param_data.get("is_static") is True:
                        module.get_param(param_id).set_static_value(param_data.get("value"))

                node_tag = f"node_{node_id}"
                attrs = dpg.get_item_children(node_tag)[1]
                if len(attrs) >= module.params_num + 2:
                    name_groups = dpg.get_item_children(attrs[0])[1]
                    if len(name_groups) > 0:
                        name_widgets = dpg.get_item_children(name_groups[0])[1]
                        if len(name_widgets) >= 2 and module.get_name() != "unknown":
                            dpg.set_value(name_widgets[1], module.get_name())
                    for i in range(module.params_num):
                        param_groups = dpg.get_item_children(attrs[i + 1])[1]
                        if len(param_groups) == 0:
                            continue
                        param_widgets = dpg.get_item_children(param_groups[0])[1]
                        if len(param_widgets) >= 2 and module.get_param(i).is_static:
                            dpg.set_value(param_widgets[1], module.get_param(i).value)
                            dpg.show_item(param_widgets[1])

                pos = node_data.get("Pos")
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    dpg.set_item_pos(node_tag, [pos[0], pos[1]])

            for idx, link in enumerate(links_raw):
                if not isinstance(link, (list, tuple)) or len(link) != 4:
                    raise ValueError(f"Link format invalid at index={idx}")

                src_node_id = int(link[0])
                is_ext_param = link[1]
                dst_node_id = int(link[2])
                dst_param_id = int(link[3])
                if not isinstance(is_ext_param, bool):
                    raise ValueError(f"Link ext flag invalid at index={idx}")

                if is_ext_param:
                    source_node_tag = self.ext_param_node_tags.get(src_node_id)
                    if source_node_tag is None:
                        raise ValueError(f"External param not found: {src_node_id}")
                    source_attr = f"{source_node_tag}_output"
                else:
                    source_node_tag = f"node_{src_node_id}"
                    if not dpg.does_item_exist(source_node_tag):
                        raise ValueError(f"Source module not found: {src_node_id}")
                    source_attr = dpg.get_item_children(source_node_tag)[1][-1]

                if dst_param_id == 255:
                    target_node_tag = self.out_param_node_tags.get(dst_node_id)
                    if target_node_tag is None:
                        raise ValueError(f"Target output param not found: {dst_node_id}")
                    target_attr = f"{target_node_tag}_output"
                else:
                    target_node_tag = f"node_{dst_node_id}"
                    if not dpg.does_item_exist(target_node_tag):
                        raise ValueError(f"Target module not found: {dst_node_id}")
                    target_attrs = dpg.get_item_children(target_node_tag)[1]
                    target_index = dst_param_id + 1
                    if target_index <= 0 or target_index >= len(target_attrs) - 1:
                        raise ValueError(f"Target param missing: node={dst_node_id}, param={dst_param_id}")
                    target_attr = target_attrs[target_index]

                self.line_manager.add_link(self.editor_tag, (source_attr, target_attr))
                if (src_node_id, is_ext_param, dst_node_id, dst_param_id) not in self.control_graph.edges:
                    raise ValueError(f"Link rebuild failed at index={idx}")

            print(f"[Import] Project imported: {path}")
            return True
        except Exception as e:
            raise ValueError(f"[Import] Failed: {e}")

    def __layout_ext_params(self, client_w: int = None, client_h: int = None):
        """
        外部参数左侧网格布局
        """
        if not dpg.does_item_exist(self.editor_tag):
            return
        start_x, start_y = 20, 120
        x_step, y_step = 190, 110
        viewport_w = client_w if client_w is not None else dpg.get_viewport_client_width()
        viewport_h = client_h if client_h is not None else dpg.get_viewport_client_height()
        if viewport_w <= 0:
            viewport_w = self.width
        if viewport_h <= 0:
            viewport_h = self.height
        rows_per_col = max(1, (viewport_h - start_y - 20) // y_step)
        max_cols = max(1, (viewport_w - start_x - 20) // x_step)
        ext_count = len(self.manifest.ext_params)
        if ext_count <= 0:
            return
        cols_needed = max(1, (ext_count + rows_per_col - 1) // rows_per_col)
        cols = min(max_cols, cols_needed)
        rows_per_col = max(1, (ext_count + cols - 1) // cols)

        for idx, ext_param in enumerate(self.manifest.ext_params):
            col = idx // rows_per_col
            row = idx % rows_per_col
            node_tag = self.node_factory.create_param_node(ext_param)
            self.ext_param_node_tags[ext_param.hash] = node_tag
            dpg.set_item_pos(node_tag, [start_x + col * x_step, start_y + row * y_step])

    def __layout_out_params(self, client_w: int = None, client_h: int = None):
        """
        输出参数左侧网格布局
        """
        if not dpg.does_item_exist(self.editor_tag):
            return
        start_x, start_y = 400, 120
        x_step, y_step = 190, 110
        viewport_w = client_w if client_w is not None else dpg.get_viewport_client_width()
        viewport_h = client_h if client_h is not None else dpg.get_viewport_client_height()
        if viewport_w <= 0:
            viewport_w = self.width
        if viewport_h <= 0:
            viewport_h = self.height
        rows_per_col = max(1, (viewport_h - start_y - 20) // y_step)
        max_cols = max(1, (viewport_w - start_x - 20) // x_step)
        ext_count = len(self.manifest.out_params)
        if ext_count <= 0:
            return
        cols_needed = max(1, (ext_count + rows_per_col - 1) // rows_per_col)
        cols = min(max_cols, cols_needed)
        rows_per_col = max(1, (ext_count + cols - 1) // cols)

        for idx, ext_param in enumerate(self.manifest.out_params):
            col = idx // rows_per_col
            row = idx % rows_per_col
            node_tag = self.node_factory.create_output_node(ext_param)
            self.out_param_node_tags[ext_param.hash] = node_tag
            dpg.set_item_pos(node_tag, [start_x + col * x_step, start_y + row * y_step])

    def __on_viewport_resize(self, sender, app_data):
        """
        视口尺寸变化时，重排工具栏
        """
        if not dpg.does_item_exist(self.toolbar_tag):
            return
        client_w, client_h = None, None
        if isinstance(app_data, (tuple, list)):
            if len(app_data) >= 4:
                client_w, client_h = app_data[2], app_data[3]
            elif len(app_data) >= 2:
                client_w, client_h = app_data[0], app_data[1]
        build_toolbar(self.toolbar_tag, self.manifest, self.create_module_node, client_w)

    def __on_save_project(self, sender, app_data, user_data):
        """保存项目"""
        if self.current_project_path is None:
            dpg.show_item("file_dialog")
        else:
            self.save_project(self.current_project_path)

    def __on_save_as(self, sender, app_data, user_data):
        """保存项目为..."""
        dpg.show_item("file_dialog")

    def __on_import_project(self, sender, app_data, user_data):
        """导入项目"""
        dpg.show_item("import_file_dialog")

    def __create_menu_bar(self):
        """创建菜单条"""
        with dpg.menu_bar(tag="menu_bar"):
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save Project", callback=self.__on_save_project)
                dpg.add_menu_item(label="Load as...", callback=self.__on_save_as)
                dpg.add_menu_item(label="Import Project", callback=self.__on_import_project)

    def __on_dialog_save_ok(self, sender, app_data, user_data):
        """文件对话框确认保存"""
        file_path = app_data['file_path_name']
        self.current_project_path = file_path
        self.save_project(file_path)

    def __create_file_dialog(self):
        """创建文件对话框"""
        with dpg.file_dialog(directory_selector=False, show=False, tag="file_dialog",
                                callback=self.__on_dialog_save_ok,
                                width=600, height=400):
            dpg.add_file_extension(".omni", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*")

        with dpg.file_dialog(directory_selector=False, show=False, tag="import_file_dialog",
                                callback=lambda sender, app_data, user_data: self.import_project(app_data['file_path_name']),
                                width=600, height=400):
            dpg.add_file_extension(".omni", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*")

    def setup_ui(self):
        """构建 DearPyGUI 布局"""
        # 创建菜单条
        with dpg.window(tag=self.root_tag, no_title_bar=True, no_move=True):
            self.__create_file_dialog()

            # 1. 菜单条
            self.__create_menu_bar()

            # 2. 顶部区域（工具栏）
            with dpg.child_window(tag=self.toolbar_tag, height=100):
                # 为了让图标/按钮横向排列，这里内部需要一个 horizontal group
                with dpg.group(horizontal=True):
                    dpg.add_text("Loading...")

            # 3. 底部区域（编辑器）
            with dpg.group(horizontal=True):
                with dpg.node_editor(tag=self.editor_tag,
                                     callback=self.line_manager.add_link,
                                     delink_callback=self.line_manager.del_link):
                    pass

            # 4. 初始化外部、输出参数节点
            self.__layout_ext_params()
            self.__layout_out_params()

        # 5. 设置该窗口为主窗口（随视口大小缩放）
        dpg.set_primary_window(self.root_tag, True)

        # 6. 监听 Delete 键事件
        with dpg.handler_registry():
            # 监听 Delete 键，触发 self._on_key_delete
            dpg.add_key_press_handler(dpg.mvKey_Delete, callback=self.__on_key_delete)

    def create_module_node(self, sender, app_data, user_data):
        """创建模块节点"""
        module = user_data
        self.node_factory.create_module_node(module)

    def __on_key_delete(self, sender, app_data):
        """
        处理 Delete 键事件
        """
        # 1. 删除选中的连线
        selected_links = dpg.get_selected_links(self.editor_tag)
        for link_id in selected_links:
            self.line_manager.del_link(self.editor_tag, link_id)

        # 2. 删除选中的节点
        selected_nodes = dpg.get_selected_nodes(self.editor_tag)
        # 2.1 获取所有参数的ID
        child_ids = []
        for node_id in selected_nodes:
            if isinstance(dpg.get_item_user_data(node_id), Module):
                for child_id in dpg.get_item_children(node_id)[1]:
                    child_ids.append(child_id)
        # 2.2 遍历连线库查找连线
        links_del = []
        for link_id, (source, target) in self.line_manager.get_links().items():
            if target in child_ids:
                links_del.append(link_id)
            elif source in child_ids:
                links_del.append(link_id)
        # 2.3 删除连线(先存起来，避免遍历过程中删除导致迭代器失效)
        for link_id in links_del:
            self.line_manager.del_link(self.editor_tag, link_id)
        # 2.4 删除节点
        for node_id in selected_nodes:
            module = dpg.get_item_user_data(node_id)
            if isinstance(module, Module):
                self.control_graph.remove_node(module.id)
                dpg.delete_item(node_id)

    def show(self):
        """启动应用循环"""
        self.setup_dpg_context()
        self.setup_ui()
        dpg.show_viewport()
        # 视口显示后重排一次，获取真实窗口尺寸
        client_w = dpg.get_viewport_client_width()
        client_h = dpg.get_viewport_client_height()
        self.__layout_ext_params(client_w, client_h)
        self.__layout_out_params(client_w, client_h)
        build_toolbar(self.toolbar_tag, self.manifest, self.create_module_node, client_w)
        dpg.set_viewport_resize_callback(self.__on_viewport_resize)
        dpg.start_dearpygui()
        dpg.destroy_context()
