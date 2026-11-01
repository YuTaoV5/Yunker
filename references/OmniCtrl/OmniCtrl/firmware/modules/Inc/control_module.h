/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-10 23:05
* @version: v1.0.0
* @description: 控制模块基类
********************************************************************************/
#ifndef CONTROL_MODULE_H
#define CONTROL_MODULE_H

#include "../../bases/Inc/control_types.h"
#include <assert.h>
#include <stddef.h>


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief 控制模块基类结构体
 */
typedef struct {
    signal_t output_;               // 输出信号
    ModuleType_t type_;             // 模块类型标识
    void (*Process)(void *self);    // 执行函数
    char (*Connect)(void *self, char param_id, CtrlModule_Param_t param); // 设置动态参数（0失败，1成功）
    char (*SetStaticParam)(void *self, char param_id, CtrlModule_Param_t param); // 设置静态参数（0失败，1成功）
} ControlModule_t;

#endif //CONTROL_MODULE_H
