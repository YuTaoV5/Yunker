/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 01:57
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __BSP_RTC_H
#define __BSP_RTC_H

#include "bsp_common.h"
#include "rtc.h"

extern RTC_TimeTypeDef rtc_time;
extern RTC_DateTypeDef rtc_date;

void BSP_RTC_GetTime(void);
uint32_t BSP_RTC_GetSysTime_ms(void);
void BSP_RTC_Delay_ms(uint32_t ms);

#endif /* __BSP_RTC_H */
