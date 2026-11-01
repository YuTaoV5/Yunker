/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-06 17:11
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "log.h"
#include "bsp_rtc.h"
#include "bsp_interface.h"

/**
 * @brief 打印时间
 * @param None
 * @return None
 */
static void Log_Print_Time(void)
{
    static char log_buf[LOG_BUF_SIZE]; // 日志缓冲区
    // 打印时间
    if(LOG_TIM_ON)
    {
        BSP_RTC_GetTime();
        sprintf(log_buf, "[%02d:%02d:%02d]", rtc_time.Hours, rtc_time.Minutes, rtc_time.Seconds);
        BSP_UART_Transmit(LOG_UART, (uint8_t *)log_buf, 10);
    }
}

/**
 * @brief 初始化日志模块
 * @param None
 * @return None
 */
void Log_Init(void)
{
    BSP_UART_Init(LOG_UART, 115200);
}


/**
 * @brief 打印调试日志
 * @param info 日志内容
 * @param len 日志内容长度
 * @return None
 */
void Log_Debug(uint8_t *info, uint16_t len)
{
    // 检查是否需要打印日志
    if(LOG_ON == 0 || LOG_LEVEL_DEBUG < LOG_LEVEL) return;

    // 打印时间
    Log_Print_Time();

    // 打印日志级别
    if(LOG_LEVEL_ON)
        BSP_UART_Transmit(LOG_UART, (uint8_t *)"[DEBUG]: ", 9);
    
    // 打印日志内容
    BSP_UART_Transmit(LOG_UART, info, len);

    // 打印换行
    BSP_UART_Transmit(LOG_UART, (uint8_t *)"\r\n", 1);
}

/** 
 * @brief 打印信息日志
 * @param info 日志内容
 * @param len 日志内容长度
 * @return None
 */
void Log_Info(uint8_t *info, uint16_t len)
{
    // 检查是否需要打印日志
    if(LOG_ON == 0 || LOG_LEVEL_INFO < LOG_LEVEL) return;

    // 打印时间
    Log_Print_Time();

    // 打印日志级别
    if(LOG_LEVEL_ON)
        BSP_UART_Transmit(LOG_UART, (uint8_t *)"[INFO]:  ", 9);
    
    // 打印日志内容
    BSP_UART_Transmit(LOG_UART, info, len);

    // 打印换行
    BSP_UART_Transmit(LOG_UART, (uint8_t *)"\r\n", 1);
}


void Log_Warn(uint8_t *info, uint16_t len)
{
    // 检查是否需要打印日志
    if(LOG_ON == 0 || LOG_LEVEL_WARN < LOG_LEVEL) return;

    // 打印时间
    Log_Print_Time();

    // 打印日志级别
    if(LOG_LEVEL_ON)
        BSP_UART_Transmit(LOG_UART, (uint8_t *)"[WARN]:  ", 9);
    
    // 打印日志内容
    BSP_UART_Transmit(LOG_UART, info, len);

    // 打印换行
    BSP_UART_Transmit(LOG_UART, (uint8_t *)"\r\n", 1);
}


void Log_Error(uint8_t *info, uint16_t len)
{
    // 检查是否需要打印日志
    if(LOG_ON == 0 || LOG_LEVEL_ERROR < LOG_LEVEL) return;

    // 打印时间
    Log_Print_Time();

    // 打印日志级别
    if(LOG_LEVEL_ON)
        BSP_UART_Transmit(LOG_UART, (uint8_t *)"[ERROR]: ", 9);
    
    // 打印日志内容
    BSP_UART_Transmit(LOG_UART, info, len);

    // 打印换行
    BSP_UART_Transmit(LOG_UART, (uint8_t *)"\r\n", 1);
}