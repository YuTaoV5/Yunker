/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 23:00
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/ctrl_registry.h"
#include "../Inc/ctrl_hash.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>

// 控制模块注册数组
static CtrlModule_Registry_t ctrl_module_registry[MODULE_NUM] = {0};
// 控制参数注册数组
static CtrlParam_Registry_t ctrl_param_registry[CTRL_PARAM_MAX] = {0};
static CtrlParam_Registry_t ctrl_out_param_registry[CTRL_PARAM_MAX] = {0};
static size_t ctrl_param_count = 0;
static size_t ctrl_out_param_count = 0;

/**
 * @brief: 控制模块注册初始化函数
 * @description: 用于初始化控制模块注册结构体
 * @param module_type 控制模块类型
 * @param size 控制模块大小
 * @param module_init 控制模块初始化函数指针
 * @return char 初始化状态，1表示成功，0表示失败
 */
char CtrlModule_Registry_Init(ModuleType_t module_type, size_t size, 
            void (*module_init)(void *self))
{
    if(module_type >= MODULE_NUM || size == 0 || module_init == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Registry_Init Input Error\n", 27);
        assert(0 && "Invalid module type or size or module_init");
        return 0;
    }
    ctrl_module_registry[module_type].size_ = size;
    ctrl_module_registry[module_type].ctrl_module_init = module_init;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Registry_Init Success\n", 23);
    return 1;
}

/**
 * @brief: 控制模块获取初始化函数指针
 * @description: 用于获取控制模块注册结构体的初始化函数指针
 * @param module_type 控制模块类型
 * @return CtrlModule_Registry_t* 控制模块注册结构体指针
 */
CtrlModule_Registry_t* CtrlModule_Get_Init(ModuleType_t module_type)
{
    if(module_type >= MODULE_NUM)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Invalid module type\n", 21);
        assert(0 && "Invalid module type");
        return NULL;
    }
    else if(ctrl_module_registry[module_type].ctrl_module_init == NULL || 
                ctrl_module_registry[module_type].size_ == 0)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Module not initialized\n", 24);
        assert(0 && "Module not initialized");
        return NULL;
    }
    
    return &ctrl_module_registry[module_type];
}

/**
 * @brief: 控制参数注册初始化函数
 * @description: 用于初始化控制参数注册结构体
 * @param name 控制参数名称
 * @param param_type 控制参数类型
 * @param ptr 控制参数指针
 * @param is_out 是否为输出参数
 * @return char 初始化状态，1表示成功，0表示失败
 */
char CtrlModule_Registry_Param(char *name, CtrlModule_Param_Type_t param_type
                                , void *ptr, char is_out)
{
    size_t* param_count = is_out ? &ctrl_out_param_count : &ctrl_param_count;
    CtrlParam_Registry_t* param_registry = is_out ? ctrl_out_param_registry : ctrl_param_registry;

    // 参数检查
    if(name == NULL || ptr == NULL || param_type >= CTRL_PARAM_NUM)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Invalid name or ptr or param_type\n", 35);
        assert(0 && "Invalid name or ptr or param_type");
        return 0;
    }
    else if(*param_count >= CTRL_PARAM_MAX)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CtrlParam registry full\n", 25);
        assert(0 && "CtrlParam registry full");
        return 0;
    }

    // 计算哈希值
    uint32_t hash = Ctrl_Hash_FNV1a(name);
    for(size_t i = 0; i < *param_count; i++)    // 检查哈希值是否重复
    {
        if(param_registry[i].hash_ == hash)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CtrlParam name duplicated\n", 27);
            assert(0 && "CtrlParam name duplicated");
            return 0;
        }
    }

    // 注册控制参数
    strncpy(param_registry[*param_count].name_, name, 
                MODULE_NAME_MAX - 1);
    param_registry[*param_count].name_[MODULE_NAME_MAX - 1] = '\0';
    param_registry[*param_count].hash_ = hash;
    param_registry[*param_count].param_.type_ = param_type;
    param_registry[*param_count].param_.is_ptr_ = 1;
    param_registry[*param_count].param_.value_.ptr_ = ptr;
    (*param_count)++;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Registry_Param Success\n", 24);
    return 1;
}

/**
 * @brief: 控制参数获取指针函数
 * @description: 用于获取控制参数注册结构体的指针
 * @param hash 控制参数哈希值
 * @param out_param 输出控制参数指针
 * @return char 查找状态，1表示成功，0表示失败
 */
char CtrlModule_Get_Param(uint32_t hash, CtrlModule_Param_t *out_param)
{
    // 参数检查
    if(out_param == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Invalid out_param\n", 19);
        assert(0 && "Invalid out_param");
        return 0;
    }
    
    // 查找控制参数
    for(size_t i = 0; i < ctrl_param_count; i++)
    {
        if(ctrl_param_registry[i].hash_ == hash)
        {
            *out_param = ctrl_param_registry[i].param_;
            return 1;
        }
    }

    // 未找到控制参数
    Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CtrlParam not found\n", 21);
    assert(0 && "CtrlParam not found");
    return 0;
}
