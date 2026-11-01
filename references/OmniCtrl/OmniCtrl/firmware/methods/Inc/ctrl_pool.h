/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-08 23:55
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef CTRL_POOL_H
#define CTRL_POOL_H

#include <assert.h>
#include <stddef.h>

/**
 * @brief 内存池对齐单位
 * 
 */
typedef union
{
    long long max_int;
    long double max_float;
    void *max_ptr;
}AlignmentUnit_t;


#define MODULE_MEM_POOL_SIZE (1024 * 8) // 8KB内存池大小
#define POOL_SIZE_IN_UNITS (MODULE_MEM_POOL_SIZE / sizeof(AlignmentUnit_t)) // 内存池单位数量

extern AlignmentUnit_t g_module_memory_pool[POOL_SIZE_IN_UNITS];


/*-----------------------------------函数声明-----------------------------------*/
void *CtrlPool_Malloc(size_t size);
void CtrlPool_FreeAll(void);

#endif // CTRL_POOL_H
