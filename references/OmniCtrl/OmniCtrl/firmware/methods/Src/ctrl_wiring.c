/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 23:35
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/ctrl_wiring.h"
#include "../../modules/Inc/control_module.h"
#include "../Inc/ctrl_registry.h"

/**
 * @brief: 控制参数指针连接函数
 * @description: 用于将控制参数指针连接到控制模块的指定参数位置
 * @param self 控制模块指针
 * @param param_id 控制参数位置索引
 * @param param_ptr 控制参数指针
 * @return char 连接状态，1表示成功，0表示失败
 */
char CtrlModule_Wiring_ptr(void *self, char param_id, void *param_ptr)
{
    // 参数检查
    if(self == NULL || param_ptr == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Wiring_ptr Input Error\n", 24);
        assert(0 && "Invalid self or param_ptr or type");
        return 0;
    }
    
    // 连接变量
    ControlModule_t *ctrl_module = (ControlModule_t *)self;
    CtrlModule_Param_t param = {
        .type_ = CTRL_PARAM_SIGNAL_T,
        .is_ptr_ = 1,
        .value_.ptr_ = param_ptr
    };
    if(ctrl_module->Connect(self, param_id, param) == 0)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Connect failed\n", 16);
        assert(0 && "Connect failed");
        return 0;
    }

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Wiring_ptr Success\n", 20);
    return 1;
}

/**
 * @brief: 控制参数哈希值连接函数
 * @description: 用于将控制参数哈希值连接到控制模块的指定参数位置
 * @param self 控制模块指针
 * @param param_id 控制参数位置索引
 * @param param_hash 控制参数哈希值
 * @return char 连接状态，1表示成功，0表示失败
 */
char CtrlModule_Wiring_hash(void *self, char param_id, uint32_t param_hash)
{
    // 获取控制参数指针
    CtrlModule_Param_t param;
    if(CtrlModule_Get_Param(param_hash, &param) == 0)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"GetParam failed\n", 17);
        assert(0 && "GetParam failed");
        return 0;
    }

    // 参数检查
    if(self == NULL || param.value_.ptr_ == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Wiring_hash Input Error\n", 28);
        assert(0 && "Invalid self or param_hash");
        return 0;
    }

    // 连接变量
    ControlModule_t *ctrl_module = (ControlModule_t *)self;
    if(ctrl_module->Connect(self, param_id, param) == 0)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Connect failed\n", 16);
        assert(0 && "Connect failed");
        return 0;
    }

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Wiring_hash Success\n", 21);
    return 1;
}

/**
 * @brief: 控制参数值连接函数
 * @description: 用于将控制参数值连接到控制模块的指定参数位置
 * @param self 控制模块指针
 * @param param_id 控制参数位置索引
 * @param param 控制参数值
 * @return char 连接状态，1表示成功，0表示失败
 */
char CtrlModule_Wiring_Param(void *self, char param_id, CtrlModule_Param_t param)
{
    // 参数检查
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Wiring_Param Input Error\n", 26);
        assert(0 && "Invalid self or param");
        return 0;
    }

    // 连接变量
    ControlModule_t *ctrl_module = (ControlModule_t *)self;
    if(ctrl_module->SetStaticParam(self, param_id, param) == 0)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"SetStaticParam failed\n", 23);
        assert(0 && "SetStaticParam failed");
        return 0;
    }
    
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Wiring_Param Success\n", 22);
    return 1;
}
