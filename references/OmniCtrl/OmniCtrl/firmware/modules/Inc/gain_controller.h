/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:50
* @version: v1.0.0
* @description: 增益控制器
********************************************************************************/
#ifndef __GAIN_CONTROLLER_H
#define __GAIN_CONTROLLER_H

#include "../Inc/control_module.h"


/*-----------------------------------枚举定义------------------------------------*/
typedef enum{
    GAIN_PORT_INPUT = 0,
    GAIN_PORT_GAIN,
} GainController_Ports;


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief: 增益控制器结构体
 * @description: 实现增益控制器的功能
 */
typedef struct GainController{
    /* 基类 */
    ControlModule_t base_;
    /* 增益参数 */
    // 静态参数
    signal_t gain_static_;
    // 动态参数指针
    signal_t *input_;
    signal_t *gain_;
    /* 内部状态变量 */
    char is_wired_;
} GainController_t;


/*-----------------------------------函数声明-----------------------------------*/
void GainController_Init(void *self);

#endif // __GAIN_CONTROLLER_H
