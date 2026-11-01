/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:47
* @version: v1.0.0
* @description: 限幅控制器类
********************************************************************************/
#ifndef LIMIT_CONTROLLER_H
#define LIMIT_CONTROLLER_H

#include "../Inc/control_module.h"


/*-----------------------------------枚举定义------------------------------------*/
typedef enum{
    LIMIT_PORT_INPUT = 0,
    LIMIT_PORT_OUTPUT_MIN,
    LIMIT_PORT_OUTPUT_MAX,
}LimitController_Ports;


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief 限幅控制器结构体
 */
typedef struct {
    /* 基类 */
    ControlModule_t base_;      // 继承自控制模块基类
    /* 限幅参数 */
    // 静态限幅值
    signal_t output_min_static_; // 静态存储的最小输出值
    signal_t output_max_static_; // 静态存储的最大输出值
    // 动态限幅值指针
    signal_t *input_;           // 输入信号指针
    signal_t *output_min_;      // 输出最小值指针
    signal_t *output_max_;      // 输出最大值指针
    /* 内部状态变量 */
    char is_wired_;             // 标志位，指示是否已绑定输入输出
} LimitController_t;


/*-----------------------------------函数声明------------------------------------*/
void LimitController_Init(void *self);
                                                                                                             
#endif // LIMIT_CONTROLLER_H
