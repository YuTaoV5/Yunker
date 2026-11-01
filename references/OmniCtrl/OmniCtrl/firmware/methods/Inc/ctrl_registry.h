/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 23:00
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef CTRL_REGISTRY_H
#define CTRL_REGISTRY_H

#include "../../bases/Inc/control_types.h"
#include <stdint.h>


#define MODULE_NAME_MAX 32
#define CTRL_PARAM_MAX 32

/*----------------------------------结构体定义-----------------------------------*/
/**
 * @brief: 控制模块注册结构体
 * @description: 用于注册控制模块的初始化函数
 */
typedef struct
{
    size_t size_;       // 控制模块大小
    void (*ctrl_module_init)(void *self);   // 控制模块初始化函数指针
}CtrlModule_Registry_t;

/**
 * @brief: 控制参数注册结构体
 * @description: 用于注册控制参数的哈希值
 */
typedef struct
{
    char name_[MODULE_NAME_MAX];    // 控制参数名称
    uint32_t hash_;                 // 控制参数哈希值
    CtrlModule_Param_t param_;      // 控制参数值
}CtrlParam_Registry_t;


/*-----------------------------------函数声明-----------------------------------*/
char CtrlModule_Registry_Init(ModuleType_t module_type, size_t size, 
            void (*module_init)(void *self));
CtrlModule_Registry_t* CtrlModule_Get_Init(ModuleType_t module_type);
char CtrlModule_Registry_Param(char *name, CtrlModule_Param_Type_t param_type,
                                void *ptr, char is_out);
char CtrlModule_Get_Param(uint32_t hash, CtrlModule_Param_t *out_param);

#endif  // CTRL_REGISTRY_H
