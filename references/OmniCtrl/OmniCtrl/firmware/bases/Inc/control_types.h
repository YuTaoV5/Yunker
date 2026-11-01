/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 19:31
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __CONTROL_TYPES_H
#define __CONTROL_TYPES_H

#include "../Inc/control_log.h"
#include <stddef.h>

/*-----------------------------------类型定义------------------------------------*/
/* 定义通用的信号数据类型，例如32位浮点数 */
// 若使用long long，需修改类型转化函数，将输入、输出signal_t单独处理(直接转换，不通过double中转)
typedef float signal_t;
/* 定义控制模块句柄类型 */
typedef void ControlModuleHandle_t;


/*-----------------------------------枚举定义------------------------------------*/
/**
 * @brief: 控制模块类型枚举
 */
typedef enum
{
    MODULE_GAIN = 0,
    MODULE_LIMIT,
    MODULE_OFFSET,
    MODULE_POSITIONAL_PID,
    MODULE_INCREMENTAL_PID,
    MODULE_RAMP_INJECTOR,
    MODULE_CURVE_ACCEL,
    MODULE_BRANCH_JUDGE,
    MODULE_MEAN_FILTER,
    MODULE_NUM,
}ModuleType_t;

/**
 * @brief: 控制模块参数类型枚举
 */
typedef enum
{
    CTRL_PARAM_SIGNAL_T,
    CTRL_PARAM_SIZE_T,
    CTRL_PARAM_CHAR,
    CTRL_PARAM_FLOAT,
    CTRL_PARAM_DOUBLE,
    CTRL_PARAM_SHORT,
    CTRL_PARAM_INT,
    CTRL_PARAM_LONG,
    CTRL_PARAM_NUM,
}CtrlModule_Param_Type_t;

/**
 * @brief: 控制模块参数结构体
 */
typedef struct
{
    CtrlModule_Param_Type_t type_;  // 参数类型(当is_ptr_为1时标志指针存储的类型)
    char is_ptr_;   // 标志参数是否为指针类型(0: 否, 1: 是)
    union
    {
        void *ptr_;
        signal_t signal_t_;
        size_t size_t_;
        char char_;
        float float_;
        double double_;
        short short_;
        int int_;
        long long_;
    }value_;
}CtrlModule_Param_t;


/*-----------------------------------函数定义------------------------------------*/
CtrlModule_Param_t CtrlModule_Param_Transform(CtrlModule_Param_Type_t type, 
            CtrlModule_Param_t param);


#endif // __CONTROL_TYPES_H
