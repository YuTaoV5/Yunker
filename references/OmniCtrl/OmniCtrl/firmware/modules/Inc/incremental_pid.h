/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:50
* @version: v1.0.0
* @description: 增量式PID
********************************************************************************/
#ifndef __INCREMENTAL_PID_H
#define __INCREMENTAL_PID_H

#include "../Inc/control_module.h"

/*-----------------------------------枚举定义------------------------------------*/
typedef enum{
    INCREMENTALPID_PORT_INPUT = 0,
    INCREMENTALPID_PORT_KP,
    INCREMENTALPID_PORT_KI,
    INCREMENTALPID_PORT_KD,
    INCREMENTALPID_PORT_SETPOINT,
    INCREMENTALPID_PORT_INTEGRAL_LIMIT,
    INCREMENTALPID_PORT_AUTO_RESET_ENABLE,
    INCREMENTALPID_PORT_AUTO_RESET_THRESHOLD,
}IncrementalPID_Ports;


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief: 增量式PID控制器
 * @description: 实现PID控制器的功能
 */
typedef struct{
    /* 基类 */
    ControlModule_t base_;      // 基类
    /* PID参数 */
    // 静态参数
    float kp_static_;               // 比例系数
    float ki_static_;               // 积分系数
    float kd_static_;               // 微分系数
    signal_t setpoint_static_;         // 目标设定值
    signal_t integral_limit_static_;    // 积分项限幅值
    char auto_reset_enable_static_;    // 自动重置标志位
    signal_t auto_reset_threshold_static_;   // 自动重置阈值
    // 动态参数指针
    signal_t *input_;          // 输入信号指针
    float *kp_;               // 比例系数指针
    float *ki_;               // 积分系数指针
    float *kd_;               // 微分系数指针
    signal_t *setpoint_;         // 目标设定值指针
    signal_t *integral_limit_;    // 积分项限幅值指针
    char *auto_reset_enable_;    // 自动重置标志位指针
    signal_t *auto_reset_threshold_;   // 自动重置阈值指针
    /* 内部状态变量 */
    signal_t prev_error_;       // 前次误差（用于微分计算）
    signal_t prev_prev_error_;  // 前前次误差（用于微分计算）
    char is_wired_;            // 是否已绑定输入输出指针
}IncrementalPID_t;


/*-----------------------------------函数声明-----------------------------------*/
void IncrementalPID_Init(void *self);


#endif //__INCREMENTAL_PID_H
