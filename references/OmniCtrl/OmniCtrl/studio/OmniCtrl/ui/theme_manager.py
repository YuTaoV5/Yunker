#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2025-12-08 11:31
@Author  : Ternura_xiang
@File    : theme_manager.py
@Project : OmniCtrl
@Desc    : 主题
"""

import dearpygui.dearpygui as dpg


class ThemeManager:
    @staticmethod
    def load_font(font_path: str, size: int = 20):
        """
        加载自定义字体
        注意：必须要有中文字体文件(.ttf/.otf)，否则中文无法显示
        """
        with dpg.font_registry():
            # 这里增加了中文范围的字符集，防止中文乱码
            with dpg.font(font_path, size) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full_Common_1)

            dpg.bind_font(default_font)

    @staticmethod
    def apply_modern_theme():
        """
        应用现代扁平化主题
        """
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                # --- 1. 样式 (Style) ---
                # 让所有元素都有圆角
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6, category=dpg.mvThemeCat_Core)

                # 增加控件之间的间距，不再挤在一起
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6, category=dpg.mvThemeCat_Core)

                # --- 2. 颜色 (Color) ---
                # 背景色：更深沉的黑灰色
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (40, 40, 40), category=dpg.mvThemeCat_Core)

                # 按钮颜色：低调的深蓝/深灰
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 120, 200), category=dpg.mvThemeCat_Core)  # 悬停变亮蓝
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (50, 80, 150), category=dpg.mvThemeCat_Core)

                # 标题栏颜色
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (50, 50, 50), category=dpg.mvThemeCat_Core)

                # 节点编辑器的背景网格线稍微淡一点
                # dpg.add_theme_color(dpg.mvThemeCol_NodeBackground, (50, 50, 50), category=dpg.mvThemeCat_Core)

        dpg.bind_theme(global_theme)
