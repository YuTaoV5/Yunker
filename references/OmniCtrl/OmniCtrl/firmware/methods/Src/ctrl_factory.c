/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 01:13
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/ctrl_factory.h"
#include "../Inc/ctrl_pool.h"
#include "../Inc/ctrl_registry.h"


#define MAX_CONTROL_MODULES 30  // 最大控制模块数量(最大值为256)
ControlModule_t *g_control_modules[MAX_CONTROL_MODULES];  // 控制模块句柄数组
size_t g_control_module_count = 0;  // 当前控制模块数量


/**
 * @brief: 创建指定类型的控制模块
 * @param type: 控制模块类型
 * @return: 创建的控制模块句柄，失败返回NULL
 */
ControlModule_t *Ctrl_Factory_CreateModule(ModuleType_t type)
{
    // 参数检查
    if(type >= MODULE_NUM || g_control_module_count >= MAX_CONTROL_MODULES)
    {
        Control_Log(CONTROL_LOG_WARN, (uint8_t *)"Invalid module type\n", 21);
        return NULL;
    }
    
    // 从控制模块注册数组中获取初始化函数指针
    CtrlModule_Registry_t *registry = CtrlModule_Get_Init(type);
    if(registry == NULL)
    {
        Control_Log(CONTROL_LOG_WARN, (uint8_t *)"Not registered module\n", 23);
        return NULL;
    }

    // 从控制模块池中分配控制模块
    ControlModule_t *module;
    module = CtrlPool_Malloc(registry->size_);
    if(module == NULL)
    {
        Control_Log(CONTROL_LOG_WARN, (uint8_t *)"No memory for module\n", 22);
        return NULL;
    }

    // 调用控制模块初始化函数
    registry->ctrl_module_init(module);

    // 存储控制模块句柄
    g_control_modules[g_control_module_count++] = module;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Create module Success\n", 23);
    return module;
}

/**
 * @brief: 获取当前已创建的控制模块数量
 * @return: 控制模块数量
 */
size_t Ctrl_Factory_Get_ModuleCount(void)
{
    return g_control_module_count;
}

/**
 * @brief: 获取指定索引的控制模块句柄
 * @param index: 控制模块索引
 * @return: 控制模块句柄，失败返回NULL
 */
ControlModule_t *Ctrl_Factory_Get_Module(size_t index)
{
    // 参数检查
    if(index >= g_control_module_count)
    {
        Control_Log(CONTROL_LOG_WARN, (uint8_t *)"Invalid module index\n", 22);
        return NULL;
    }
    return g_control_modules[index];
}

/**
 * @brief: 重置控制模块工厂，释放所有控制模块
 */
void Ctrl_Factory_Reset(void)
{
    CtrlPool_FreeAll();
    g_control_module_count = 0;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"Reset factory Success\n", 23);
}
