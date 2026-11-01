/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-18 16:22
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __CONTROL_LOG_H
#define __CONTROL_LOG_H

#include <stdint.h>

/*-----------------------------------类型定义-----------------------------------*/
/*
* @brief 日志传输函数类型定义
* @param info 日志信息指针
* @param len 日志信息长度
* @return None
*/
typedef void (*Ctrl_Log_Tx_t)(uint8_t *, uint16_t);

/*
* @brief 日志级别枚举类型定义
*/
typedef enum
{
    CONTROL_LOG_NONE = 0,
    CONTROL_LOG_ERROR,
    CONTROL_LOG_WARN,
    CONTROL_LOG_INFO,
}Control_Log_Level_t;


/*-----------------------------------函数声明-----------------------------------*/
// 注册控制日志传输函数
void Control_Log_Tx_Register(Ctrl_Log_Tx_t func);
// 打印控制日志
void Control_Log(Control_Log_Level_t level, uint8_t *info, uint16_t len);

#endif  // __CONTROL_LOG_H
