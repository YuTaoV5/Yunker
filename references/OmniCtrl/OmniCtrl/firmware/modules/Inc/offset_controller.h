/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 23:00
* @version: v1.0.0
* @description: 偏移控制器实现
********************************************************************************/
#ifndef __OFFSET_CONTROLLER_H
#define __OFFSET_CONTROLLER_H

#include "../Inc/control_module.h"


/*-----------------------------------枚举定义------------------------------------*/
typedef enum{
    OFFSET_PORT_INPUT = 0,
    OFFSET_PORT_OFFSET = 1,
} OffsetController_Ports;


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief: 偏移控制器类
 * @description: 对输入进行偏移处理
 */
typedef struct{
    /* 基类 */
    ControlModule_t base_;      // 基类
    /* 偏移参数 */
    // 静态偏移量
    signal_t offset_static_;    // 偏移量
    // 动态偏移量指针
    signal_t *input_;          // 输入指针
    signal_t *offset_;    // 偏移量索引指针
    /* 内部状态变量 */
    char is_wired_;
}OffsetController_t;


/*-----------------------------------函数声明-----------------------------------*/
void OffsetController_Init(void *self);


#endif //__OFFSET_CONTROLLER_H
