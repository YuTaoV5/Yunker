/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-08 22:58
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __CONTROL_CORE_H
#define __CONTROL_CORE_H

#include <stdint.h>
#include "methods/Inc/ctrl_registry.h"


/* ------------------------------ 1.公共类型 ------------------------------- */
#include "bases/Inc/control_types.h"


/* ------------------------------ 2.公共变量 ------------------------------- */
extern signal_t ctrl_output_signal[CTRL_PARAM_MAX];


/* ----------------------------- 3.核心系统API ----------------------------- */
void ControlCore_Init(void);


/* ---------------------------- 4.运行时参数API ---------------------------- */
void ControlCore_Update(void);


#endif // __CONTROL_CORE_H
