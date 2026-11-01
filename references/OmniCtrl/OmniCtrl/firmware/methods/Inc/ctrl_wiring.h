/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 23:35
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef CTRL_WIRING_H
#define CTRL_WIRING_H

#include <stdint.h>
#include "../../bases/Inc/control_types.h"

/*-----------------------------------函数声明-----------------------------------*/
char CtrlModule_Wiring_ptr(void *self, char param_id, void *param_ptr);
char CtrlModule_Wiring_hash(void *self, char param_id, uint32_t param_hash);
char CtrlModule_Wiring_Param(void *self, char param_id, CtrlModule_Param_t param);

#endif  // CTRL_WIRING_H
