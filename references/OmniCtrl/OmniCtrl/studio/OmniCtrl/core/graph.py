#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Time    : 2026-02-27 9:47
@Author  : Ternura_xiang
@File    : graph.py
@Project : OmniCtrl
@Desc    : 图类
"""

import collections, struct
from copy import deepcopy
from typing import Dict, List, Tuple
from ..common import DataType
from ..models import Module, ExternalParam, OutputParam


class GraphError(Exception):
    """
    图操作的相关异常
    """
    pass

class ControlGraph:
    """
    逻辑图管理器(Logic Layer)
    负责维护节点关系、校验逻辑以及生成执行序列
    """
    def __init__(self):
        # 存储节点：logic_id -> Module 实例
        self.nodes: Dict[int, Module] = {}
        # 存储外部参数：hash -> ExternalParam 实例
        self.ext_params: Dict[int, ExternalParam] = {}
        # 存储输出参数：hash -> OutputParam 实例
        self.out_params: Dict[int, OutputParam] = {}
        # 存储连线：(src_node_id, is_ext_param, dst_node_id, dst_param_id)
        # 注意：在电机控制图中，一个输出可以连多个输入
        self.edges: List[Tuple[int, bool, int, int]] = [] 
        self.signal_type = DataType.SIGNAL_T

        self._next_id = 0

    def _is_type_compatible(self, src_type: DataType, dst_type: DataType) -> bool:
        if src_type == dst_type:
            return True
        signal_types = {DataType.SIGNAL_T, self.signal_type}
        return src_type in signal_types and dst_type in signal_types

    def reset(self):
        """
        重置图数据
        """
        self.nodes.clear()
        self.ext_params.clear()
        self.edges.clear()
        self._next_id = 0

    def add_node(self, module: Module, node_id: int = None) -> Module:
        """
        添加节点并分配唯一的逻辑 ID

        Args:
            module: 要添加的模块实例
            node_id: 指配模块ID
        Returns:
            int: 分配的唯一逻辑 ID
        """
        if node_id is None:
            node_id = self._next_id
        elif node_id in self.nodes:
            raise GraphError(f"Node ID={node_id} already exists.")
        elif node_id < 0:
            raise GraphError(f"Node ID={node_id} is invalid.")

        module_template = deepcopy(module)  # 深拷贝模块实例
        module_template.id = node_id    # 为模块实例设置逻辑ID
        self.nodes[node_id] = module_template   # 存储模块实例到节点字典
        self._next_id = max(self.nodes.keys(), default=-1) + 1
        return module_template

    def get_node(self, node_id: int) -> Module:
        """
        获取节点实例

        Args:
            node_id: 节点ID
        Returns:
            Module: 节点实例
        """
        return self.nodes[node_id]

    def remove_node(self, node_id: int):
        """
        删除节点及其关联的所有连线

        Args:
            node_id: 要删除的节点ID
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            # 删除所有涉及该节点的连线
            self.edges = [e for e in self.edges if e[0] != node_id and e[2] != node_id]
            self._next_id = max(self.nodes.keys(), default=-1) + 1

    def add_ext_param(self, ext_param: ExternalParam) -> int:
        """
        添加外部参数

        Args:
            ext_param: 要添加的外部参数实例
        Returns:
            int: 外部参数的哈希值
        """
        if ext_param.hash not in self.ext_params:
            self.ext_params[ext_param.hash] = ext_param
        return ext_param.hash

    def add_out_param(self, out_param: OutputParam) -> int:
        """
        添加输出参数

        Args:
            out_param: 要添加的输出参数实例
        Returns:
            int: 输出参数的哈希值
        """
        if out_param.hash not in self.out_params:
            self.out_params[out_param.hash] = out_param
        return out_param.hash

    def add_edge(self, src_node_id: int, is_ext_param: bool, 
                 dst_node_id: int, dst_param_id: int):
        """
        建立连接

        Args:
            src_node_id: 源模块ID (输出端)
            is_ext_param: 标志是否为外部参数(如果为True,则src_node_id为外部参数哈希值)
            dst_node_id: 目标模块ID/输出模块Hash
            dst_param_id: 目标模块的具体参数ID (输入端)，若为255则dst为输出模块
        """
        # 1. 基础校验
        src_param_type = DataType.SIGNAL_T
        dst_param_type = DataType.SIGNAL_T
        if is_ext_param and dst_param_id == 255:
            raise GraphError("外部参数不能连接到输出参数")
        # 1.1 源模块类型检验
        if is_ext_param:
            if src_node_id not in self.ext_params:
                raise GraphError(f"外部参数Hash={src_node_id}不存在")
            src_param = self.ext_params[src_node_id]
            src_param_type = src_param.param_type
        else:
            if src_node_id not in self.nodes:
                raise GraphError(f"源节点ID={src_node_id}不存在")
        # 1.2 目标模块类型检验
        if dst_param_id != 255:
            if dst_node_id not in self.nodes:
                raise GraphError(f"目标节点ID={dst_node_id}不存在")
            elif dst_param_id > self.nodes[dst_node_id].params_num:
                raise GraphError(f"目标节点ID={dst_node_id}的参数ID={dst_param_id}不存在")
            # 获取节点及变量
            dst_node = self.nodes[dst_node_id]
            dst_param = dst_node.get_param(dst_param_id)
            dst_param_type = dst_param.param_type
        else:
            if dst_node_id not in self.out_params:
                raise GraphError(f"输出参数Hash={dst_node_id}不存在")
            dst_param = self.out_params[dst_node_id]

        # 1.3. 类型校验
        if not self._is_type_compatible(src_param_type, dst_param_type):
            raise GraphError(f"参数类型不匹配:{src_param_type} -> {dst_param_type}")

        # 2. 记录连线
        edge = (src_node_id, is_ext_param, dst_node_id, dst_param_id)
        if edge not in self.edges:
            self.edges.append(edge)
            # 更新模型状态
            if is_ext_param:
                dst_param.connect_param(src_node_id)
            else:
                dst_param.connect_output(src_node_id)

    def remove_edge(self, src_node_id: int, is_ext_param: bool, 
                    dst_node_id: int, dst_param_id: int):
        """
        断开连接

        Args:
            src_node_id: 源模块ID (输出端)
            is_ext_param: 标志是否为外部参数(如果为True,则src_node_id为外部参数哈希值)
            dst_node_id: 目标模块ID
            dst_param_id: 目标模块的具体参数ID (输入端)
        """
        # 1. 查找连线
        edge = (src_node_id, is_ext_param, dst_node_id, dst_param_id)
        if edge in self.edges:
            # 2. 更新模型状态
            if dst_param_id != 255:
                self.nodes[dst_node_id].get_param(dst_param_id).disconnect()
            else:
                self.out_params[dst_node_id].disconnect()
            # 3. 从列表中移除连线
            self.edges.remove(edge)
        else:
            raise GraphError(f"连线({src_node_id}, {is_ext_param}, {dst_node_id}, {dst_param_id})不存在")

    def topological_sort(self) -> List[int]:
        """
        拓扑排序：计算单片机的执行顺序
        """
        # 1. 构建邻接表和入度表（仅针对计算模块 nodes）
        in_degree = {node_id: 0 for node_id in self.nodes}
        adj = collections.defaultdict(list)
        
        for src_id, is_ext, dst_id, dst_param_id in self.edges:
            # 外部参数不参与排序依赖，因为它们始终是可用的
            if not is_ext and dst_param_id != 255:
                adj[src_id].append(dst_id)
                in_degree[dst_id] += 1
        
        # 2. 初始队列：所有入度为 0 的节点
        queue = collections.deque([n for n, d in in_degree.items() if d == 0])
        sorted_nodes = []
        
        while queue:
            u = queue.popleft()
            sorted_nodes.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        # 3. 闭环检测
        if len(sorted_nodes) != len(self.nodes):
            # 找出哪些节点没被包含，那就是环路的一部分
            missing = set(self.nodes.keys()) - set(sorted_nodes)
            raise GraphError(f"检测到非法环路！涉及节点ID: {missing}。请断开反馈路径或引入延迟模块。")
        
        return sorted_nodes

    def export_binary_manifest(self, signal_type: DataType):
        """
        将排好序的图转换成字节流

        Args:
            signal_type: 信号类型

        """
        order = self.topological_sort()
        TYPE_MAP = {
            DataType.SIZE_T:   (1, 'I'),    # 假设 SIZE_T 是4字节无符号
            DataType.CHAR:     (2, 'c'),    # 单字符
            DataType.FLOAT:    (3, 'f'),    # 4字节浮点数
            DataType.DOUBLE:   (4, 'd'),    # 8字节浮点数
            DataType.SHORT:    (5, 'h'),    # 2字节有符号
            DataType.INT:      (6, 'i'),    # 4字节有符号
            DataType.LONG:     (7, 'q'),    # 8字节有符号
        }

        # 1. 帧头信息
        magic = b'\x20\x13\x14'     # 魔法数
        binary = bytearray(magic)   # 使用bytearry方便动态追加
        binary.extend(b'\x00\x00\x00\x00')  # 预留4字节长度字段

        # 2. 节点信息
        for num, node_id in enumerate(order):
            # 2.1 节点类型
            node = self.get_node(node_id)
            binary.extend(struct.pack('>B', node.type_id))
            # 2.2 节点参数
            for param in node.get_changed_params():
                print(param)
                # 2.2.1 参数ID
                binary.extend(struct.pack('>B', param.id))
                if not param.is_static and param.is_hash:
                    src = self.ext_params.get(int(param.value)); hash_value = 2166136261 if src else int(param.value)
                    if src:
                        for _b in src.name.encode('utf-8'): hash_value = ((hash_value ^ _b) * 16777619) & 0xFFFFFFFF
                    binary.extend(struct.pack('<B', 0x01)); binary.extend(struct.pack('<I', hash_value)); continue
                if not param.is_static and not param.is_hash:
                    binary.extend(struct.pack('<B', 0x02)); binary.extend(struct.pack('<B', order.index(param.value))); continue
                # 2.2.2 参数类型
                if param.param_type == DataType.SIGNAL_T:
                    type_code, fmt = TYPE_MAP.get(signal_type, (None, None))
                    type_code = 0
                else:
                    type_code, fmt = TYPE_MAP.get(param.param_type, (None, None))
                if type_code is None:
                    raise GraphError(f"参数ID={param.id}的类型({param.param_type})未定义")
                # 2.2.3 参数静态属性
                packed = struct.pack(f'<{fmt}', param.value)
                binary.extend(struct.pack('<B', (type_code << 4) | ({1:0,2:1,4:2,8:3}[len(packed)] << 2)))
                # 2.2.4 参数值
                binary.extend(packed)
            
            # 2.3 模块结束标志
            binary.extend(struct.pack('>B', 0xFF))
        
        # 3. 帧尾信息
        for out_param in self.out_params.values():
            if not out_param.connect:
                continue
            binary.extend(struct.pack('>B', 0x80 | order.index(out_param.value)))
            binary.extend(struct.pack('>B', 0xFF))

        binary.extend(struct.pack('>B', 0xFF))

        # 4. CRC32校验
        # 4.1 回填帧长度(大端): 头3字节 + 长度4字节 + 数据 + CRC4字节
        frame_len = len(binary) + 3
        binary[3:7] = struct.pack('>I', frame_len)
        # 4.2 CRC32计算:
        #     init=0xFFFFFFFF, poly=0xEDB88320, 无最终异或
        crc32_value = 0xFFFFFFFF
        for b in binary:
            crc32_value ^= b
            for _ in range(8):
                if crc32_value & 0x01:
                    crc32_value = (crc32_value >> 1) ^ 0xEDB88320
                else:
                    crc32_value >>= 1
        # 4.3 按小端追加CRC
        binary.extend(struct.pack('<I', crc32_value & 0xFFFFFFFF))

        print(f"Hex Result: 0x{binary.hex()}")
        print(f"Bytes Result: {bytes(binary)}")
        print(f"CRC32: 0x{crc32_value:08X}")
