/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-06 17:11
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __LOG_H
#define __LOG_H

#include "bsp_common.h"
#include "bsp_uart.h"
#include <stdio.h>
#include <string.h>

/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief: 日志等级枚举
 */
typedef enum{
    LOG_LEVEL_DEBUG = 0,    //调试信息
    LOG_LEVEL_INFO,         //一般信息
    LOG_LEVEL_WARN,         //警告信息
    LOG_LEVEL_ERROR,        //错误信息
}Log_Level_t;


/*-----------------------------------宏定义-----------------------------------*/
#define LOG_ON 1            // 日志总开关(1:开启 0:关闭)
#define LOG_TIM_ON 1        // 日志时间开关(1:开启 0:关闭)
#define LOG_LEVEL_ON 1      // 日志等级开关(1:开启 0:关闭)
#define LOG_LEVEL LOG_LEVEL_DEBUG   // 日志等级
#define LOG_BUF_SIZE 64             // 日志缓存大小


/*-----------------------------------函数声明-----------------------------------*/
void Log_Init(void);
void Log_Debug(uint8_t *info, uint16_t len);
void Log_Info(uint8_t *info, uint16_t len);
void Log_Warn(uint8_t *info, uint16_t len);
void Log_Error(uint8_t *info, uint16_t len);

#endif // __LOG_H