#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-28 23:38
@Author  : Ternura_xiang
@File    : toolbar_builder.py
@Project : OmniCtrl
@Desc    : 工具栏构建模块
"""

import dearpygui.dearpygui as dpg
from ..models import Manifest


def build_toolbar(toolbar_tag: str, manifest: Manifest, callback_handle, available_width: int = None):
    """
    构建工具栏

    Args:
        toolbar_tag: 工具栏标签
        manifest: 清单对象
        callback_handle: 按钮点击回调函数
    """
    if not dpg.does_item_exist(toolbar_tag):
        return
    # 1. 删除所有子项
    dpg.delete_item(toolbar_tag, children_only=True)
    # 2. 获取父项宽度
    parent_width = available_width if available_width else 0
    if parent_width <= 0:
        parent_width = dpg.get_item_rect_size(toolbar_tag)[0]
    if parent_width <= 0:
        parent_width = dpg.get_item_width(toolbar_tag)
    if parent_width <= 0:
        parent_width = dpg.get_viewport_client_width()
    if parent_width <= 0:
        parent_width = 800
    # 3. 布局常量
    ITEM_SPACING_X = 10  # 对应 theme_manager 中的 mvStyleVar_ItemSpacing
    BUTTON_PADDING_X = 20  # 按钮内部左右 padding (估算值)

    current_row_width = 0
    # 3. 创建初始的第一行 (水平组)
    # parent=toolbar_tag 确保它被添加到工具栏子窗口中
    current_group = dpg.add_group(horizontal=True, parent=toolbar_tag)

    for module in manifest.modules:
        label_text = module.father_name
        # 4. 估算当前按钮宽度
        # 宽度 ≈ 文本宽度 + 内部Padding
        try:
            text_width, _ = dpg.get_text_size(label_text)
            btn_width = int(text_width) + BUTTON_PADDING_X
        except Exception:
            # 在极少数渲染状态边界下回退到字符宽估算，避免布局流程中断
            btn_width = int(len(label_text) * 14) + BUTTON_PADDING_X
        # 5. 判断是否需要换行
        # 如果 (当前行宽 + 间距 + 新按钮宽) > 父容器宽 -> 换行
        needed_width = btn_width if current_row_width == 0 else current_row_width + ITEM_SPACING_X + btn_width
        if needed_width > parent_width:
            # 换行：在 toolbar_tag 下新建一个水平组，作为新的一行
            current_group = dpg.add_group(horizontal=True, parent=toolbar_tag)
            needed_width = btn_width  # 新行第一个按钮
        # 6. 添加按钮到当前行
        dpg.add_button(label=label_text, parent=current_group,
                       user_data=module, callback=callback_handle)
        # 7. 累加宽度
        current_row_width = needed_width
