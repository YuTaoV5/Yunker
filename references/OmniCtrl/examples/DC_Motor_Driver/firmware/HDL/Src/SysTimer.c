/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-17 12:08
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "SysTimer.h"
#include "bsp_interface.h"
#include "bsp_rtc.h"

// 系统定时器回调函数指针（）
static SysTimer_Callback app_callback = NULL;

static inline void SysTimer_BSPCallbackAdapter(BSP_TIMx_t tim)
{
    if(app_callback != NULL)
    {
        app_callback();
    }
}

void SysTimer_Init(void)
{
    // 开启系统定时器
    BSP_TIM_Start(Sys_Timer_TIMx);
}

void SysTimer_RegisterCallback(SysTimer_Callback callback)
{
    app_callback = callback;
    // 注册系统定时器回调函数
    BSP_TIM_RegisterPeriodElapsedCallback(Sys_Timer_TIMx, SysTimer_BSPCallbackAdapter);
}

// @brief: RTC延时函数
// @param ms: 延时时间（毫秒）
void SysTimer_DelayMs(uint32_t ms)
{
    BSP_RTC_Delay_ms(ms);
}
