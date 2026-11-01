/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-18 16:22
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/control_log.h"
#include <stdio.h>

#define CTRL_LOG_LEVEL_DEFAULT CONTROL_LOG_INFO // 默认日志级别
#define CTRL_LOG_Tx_LEVEL 1     // 发送日志等级[0->不发送，1->发送]
static Ctrl_Log_Tx_t ctrl_log_tx_ = NULL;    // 控制日志传输函数指针

/**
 * @description: 注册控制日志传输函数
 * @param func 控制日志传输函数指针
 * @return None
 */
void Control_Log_Tx_Register(Ctrl_Log_Tx_t func)
{
    ctrl_log_tx_ = func;
}

/**
 * @description: 打印控制日志
 * @param level 日志级别
 * @param info 日志信息
 * @param len 日志信息长度
 * @return None
 */
void Control_Log(Control_Log_Level_t level, uint8_t *info, uint16_t len)
{
    // 1. 检查日志级别是否有效
    if (level > CTRL_LOG_LEVEL_DEFAULT || ctrl_log_tx_ == NULL)
    {
        return;
    }

    // 2. 打印日志级别
    if (CTRL_LOG_Tx_LEVEL == 1)
    {
        switch (level)
        {
        case CONTROL_LOG_INFO:
            ctrl_log_tx_((uint8_t *)"[INFO]", 6); break;
        case CONTROL_LOG_WARN:
            ctrl_log_tx_((uint8_t *)"[WARN]", 6); break;
        case CONTROL_LOG_ERROR:
            ctrl_log_tx_((uint8_t *)"[ERROR]", 7); break;
        default:
        break;
        }
    }

    // 3. 打印日志信息
    ctrl_log_tx_(info, len-1);

    // 4. 延迟
    for(int i = 1; i <= 50000; i++);
}
