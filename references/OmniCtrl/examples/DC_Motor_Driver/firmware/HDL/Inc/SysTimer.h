/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-17 12:08
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __SYSTIMER_H
#define __SYSTIMER_H

#include "bsp_tim.h"

typedef void (*SysTimer_Callback)(void); // 系统定时器回调函数

void SysTimer_Init(void);
void SysTimer_RegisterCallback(SysTimer_Callback callback);
void SysTimer_DelayMs(uint32_t ms);

#endif // __SYSTIMER_H
