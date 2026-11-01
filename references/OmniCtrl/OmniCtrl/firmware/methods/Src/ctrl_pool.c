/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-08 23:55
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/ctrl_pool.h"
#include "../../bases/Inc/control_log.h"

// 全局内存池定义
AlignmentUnit_t g_module_memory_pool[POOL_SIZE_IN_UNITS];
// 内存池头指针
static size_t g_pool_head = 0;


/**
 * @brief: 从内存池分配指定大小的内存
 * @param size: 需要分配的内存大小（字节）
 * @return: 分配的内存指针，失败返回NULL
 */
void *CtrlPool_Malloc(size_t size)
{
    // 1. 计算需要内存池单位数量
    size_t units_needed = (size + sizeof(AlignmentUnit_t) - 1) 
                            / sizeof(AlignmentUnit_t);
    // 2. 检查内存池是否有足够空间
    if (g_pool_head + units_needed > POOL_SIZE_IN_UNITS)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"No memory for module\n", 22);
        assert(0 && "CtrlPool_Malloc: 内存池空间不足");
        return NULL;
    }
    // 3. 分配内存池单位
    AlignmentUnit_t *ptr = &g_module_memory_pool[g_pool_head];
    // 4. 更新内存池头指针
    g_pool_head += units_needed;
    // 5. 返回分配的内存池单位指针
    return ptr;
}

/**
 * @brief: 释放所有内存池单位
 */
void CtrlPool_FreeAll(void)
{
    // 重置内存池头指针，实现全部释放
    g_pool_head = 0;
}
