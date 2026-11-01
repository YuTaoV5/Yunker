/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 01:13
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef CTRL_FACTORY_H
#define CTRL_FACTORY_H

#include "../../bases/Inc/control_types.h"
#include "../../modules/Inc/control_module.h"

/*-----------------------------------变量声明-----------------------------------*/
extern ControlModule_t *g_control_modules[];  // 控制模块句柄数组


/*-----------------------------------函数声明-----------------------------------*/
ControlModule_t *Ctrl_Factory_CreateModule(ModuleType_t type);
size_t Ctrl_Factory_Get_ModuleCount(void);
ControlModule_t *Ctrl_Factory_Get_Module(size_t index);
void Ctrl_Factory_Reset(void);

#endif // CTRL_FACTORY_H
