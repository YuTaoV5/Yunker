/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-13 18:58
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "control_core.h"
#include <string.h>
#include "bases/Inc/control_config.h"
/* 导入系统方法 */
#include "methods/Inc/ctrl_factory.h"
#include "methods/Inc/ctrl_registry.h"
#include "methods/Inc/ctrl_wiring.h"
#include "bases/Inc/control_comm.h"

// 输出结果数组
uint8_t ctrl_output_signal_id[CTRL_PARAM_MAX];
signal_t ctrl_output_signal[CTRL_PARAM_MAX];
uint8_t output_num = 0;      // 输出参数数量

/**
 * @description: 初始化控制核心
 * @return None
 */
void ControlCore_Init(void)
{
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"ControlCore_Init Start\n", 24);
    
    /* 1. 初始化控制模块注册表 */
    Ctrl_Config_ModuleInit();

    /* 2. 初始化指针参数注册表 */
    Ctrl_Config_ParamInit();

    /* 3. 清空模块 */
    Ctrl_Factory_Reset();

    /*4. 检查是否进入引导模式 */
    if(control_into_bootloader)
    {
        Control_Comm_Bootloader_Func();
    }

    /* 4. 验证图数据正确性 */
    uint16_t graph_index = 0;

    /* 5. 初始化控制模块 */
    ControlModule_t *module = NULL;
    uint8_t module_flag = 1;    // 模块初始化标志位(1: 初始化模块, 0: 设置模块参数)
    uint8_t param_id = 0;       // 参数ID
    uint8_t param_type = 0;     // 参数类型(高四位为参数类型, 中间两位为数据长度, 低两位为是否为指针)
    uint32_t hash = 0;          // 哈希值(用于存储外部指针参数)
    size_t module_index = 0;    // 模块索引(用于存储模块句柄)
    CtrlModule_Param_t param;   // 参数结构体(用于存储参数值)
    for(uint8_t i = 0; i < CTRL_PARAM_MAX; i++)
    {
        ctrl_output_signal_id[i] = 0xFF;
        ctrl_output_signal[i] = 0;
    }
    while(graph[graph_index] != 0xFF)
    {
        if(module_flag) // 1. 初始化模块、输出参数
        {
            // 1.1 为模块
            if(graph[graph_index] < 0x80)
            {
                module = Ctrl_Factory_CreateModule(graph[graph_index]); // 创建模块
                if(module == NULL)  // 模块初始化失败
                {
                    Ctrl_Factory_Reset();
                    Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Module init failed\n", 20);
                    assert(0 && "Module init failed");
                }
                module_flag = 0;    // 模块初始化完成
                graph_index ++;
            }
            // 1.2 为输出参数
            else
            {
                ctrl_output_signal_id[output_num++] = graph[graph_index++]&0x7F;
                if(graph[graph_index++] != 0xFF)
                {
                    Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Output param error\n", 20);
                    assert(0 && "Output param error");
                }
            }
        }
        else    // 2. 设置模块参数
        {
            param_id = graph[graph_index++];    // 读取参数ID
            param_type = graph[graph_index++];  // 读取参数类型(高六位为参数类型, 低两位为是否为指针)
            switch(param_type & 0x03)        // 读取参数类型
            {
            case 0:
                // 0: 常量参数
                param.type_ = param_type>>4;
                param.is_ptr_ = 0;
                switch ((param_type>>2)&0x03)    // 读取数据长度(根据长度复制内存)
                {
                case 0:
                    memcpy(&param.value_, &graph[graph_index], 1); 
                    graph_index += 1; break;
                case 1:
                    memcpy(&param.value_, &graph[graph_index], 2); 
                    graph_index += 2; break;
                case 2:
                    memcpy(&param.value_, &graph[graph_index], 4); 
                    graph_index += 4; break;
                case 3:
                    memcpy(&param.value_, &graph[graph_index], 8); 
                    graph_index += 8; break;
                }
                CtrlModule_Wiring_Param(module, param_id, param);
                break;
            case 1:
                // 1: 外部指针参数(数据位为哈希)
                memcpy(&hash, &graph[graph_index], 4);  // 读取参数值(4字节)
                graph_index += 4;
                CtrlModule_Wiring_hash(module, param_id, hash);
                break;
            case 2:
                // 2: 内部指针参数(指向其他模块的输出信号)
                memcpy(&module_index, &graph[graph_index], 1);
                graph_index += 1;
                CtrlModule_Wiring_ptr(module, param_id, 
                    &Ctrl_Factory_Get_Module(module_index)->output_);
                break;
            default:
                Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Unknown param type\n", 20);
                assert(0 && "Unknown param type");
                break;
            }
            // 3. 模块结束标志
            if(graph[graph_index] == 0xFF)
            {
                Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Module wiring success\n", 23);
                module_flag = 1;
                graph_index ++;
            }
        }
    }
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"ControlCore_Init Success\n", 26);
}

/**
 * @description: 更新控制核心
 */
void ControlCore_Update(void)
{
    ControlModule_t *module;
    size_t module_count = Ctrl_Factory_Get_ModuleCount();
    signal_t module_output[module_count];
    // 1. 遍历所有控制模块
    for(size_t i = 0; i < module_count; i++)
    {
        module = Ctrl_Factory_Get_Module(i);   // 获取当前控制模块
        module->Process(module);    // 执行当前控制模块的处理函数
        module_output[i] = module->output_;
    }
    for (size_t i = 0; i < output_num; i++)
    {
        ctrl_output_signal[i] = module_output[ctrl_output_signal_id[i]];
    }
}
