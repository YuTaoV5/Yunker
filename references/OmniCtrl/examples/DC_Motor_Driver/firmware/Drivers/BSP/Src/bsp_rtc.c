/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 01:57
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "bsp_rtc.h"

RTC_TimeTypeDef rtc_time;   // RTC时间结构体
RTC_DateTypeDef rtc_date;   // RTC日期结构体

/**
 * @brief: 获取RTC时间
 * @param: None
 * @return: None
 */
void BSP_RTC_GetTime(void)
{
    HAL_RTC_GetTime(&hrtc, &rtc_time, RTC_FORMAT_BIN);
    HAL_RTC_GetDate(&hrtc, &rtc_date, RTC_FORMAT_BIN);
}

/**
 * @brief: 获取系统时间（ms）
 * @param: None
 * @return: uint32_t 系统时间（ms）
 */
uint32_t BSP_RTC_GetSysTime_ms(void)
{
    return HAL_GetTick();
}

/**
 * @brief: 延时（ms）
 * @param: uint32_t ms 延时时间（ms）
 * @return: None
 */
void BSP_RTC_Delay_ms(uint32_t ms)
{
    HAL_Delay(ms);
}
