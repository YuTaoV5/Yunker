/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 19:31
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/control_types.h"
#include <assert.h>

/**
 * @brief 控制模块参数类型转换
 * @param type 目标类型
 * @param param 源参数
 * @return CtrlModule_Param_t 转换后的参数
 * @note 1. 指针类型参数无法转换
 * @note 2. 为保证signal_t类型为long long时的精度问题，建立特殊处理(两个有嵌套的switch)
 * @note 3. 其他类型间转换通过double进行中转，使用两个switch语句转化
 */
CtrlModule_Param_t CtrlModule_Param_Transform(CtrlModule_Param_Type_t type, 
            CtrlModule_Param_t param)
{
    // 快速通道
    if(type == param.type_) // 1. 无需转化
    {
        return param;
    }
    else if(param.is_ptr_)  // 2. 指针类型参数(无法转化)
    {
        param.value_.ptr_ = NULL;
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Pointer parameter type mismatch\n", 33);
        assert(0 && "Pointer parameter type mismatch");
        return param;
    }

    // 转换参数类型
    double temp = 0;    // 临时变量，用于存储转换后的值
    switch(param.type_)
    {
        case CTRL_PARAM_SIGNAL_T:
            temp = (double)param.value_.signal_t_; break;
        case CTRL_PARAM_SIZE_T:
            temp = (double)param.value_.size_t_; break;
        case CTRL_PARAM_CHAR:
            temp = (double)param.value_.char_; break;
        case CTRL_PARAM_FLOAT:
            temp = (double)param.value_.float_; break;
        case CTRL_PARAM_DOUBLE:
            temp = param.value_.double_; break; 
        case CTRL_PARAM_SHORT:
            temp = (double)param.value_.short_; break;
        case CTRL_PARAM_INT:
            temp = (double)param.value_.int_; break;
        case CTRL_PARAM_LONG:
            temp = (double)param.value_.long_; break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Invalid parameter type\n", 24);
            assert(0 && "Invalid parameter type");
            return param;
    }

    // 转换参数值
    switch(type)
    {
        case CTRL_PARAM_SIGNAL_T:
            param.value_.signal_t_ = (signal_t)temp; break;
        case CTRL_PARAM_SIZE_T:
            param.value_.size_t_ = (size_t)temp; break;
        case CTRL_PARAM_CHAR:
            param.value_.char_ = (char)temp; break;
        case CTRL_PARAM_FLOAT:
            param.value_.float_ = (float)temp; break;
        case CTRL_PARAM_DOUBLE:
            param.value_.double_ = (double)temp; break; 
        case CTRL_PARAM_SHORT:
            param.value_.short_ = (short)temp; break;
        case CTRL_PARAM_INT:
            param.value_.int_ = (int)temp; break;
        case CTRL_PARAM_LONG:
            param.value_.long_ = (long)temp; break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Invalid parameter type\n", 24);
            assert(0 && "Invalid parameter type");
            return param;
    }

    // 更新参数类型
    param.type_ = type;
    return param;
}
