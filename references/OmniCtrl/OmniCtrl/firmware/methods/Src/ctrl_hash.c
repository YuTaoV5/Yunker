/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-10 01:11
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/ctrl_hash.h"
#include "../../bases/Inc/control_log.h"

#define FNV_PRIME_32 16777619U  // FNV-1a 32-bit 哈希函数的素数
#define FNV_OFFSET_BASIS_32 2166136261U  // FNV-1a 32-bit 哈希函数的偏移基础值

/**
 * @brief: FNV-1a 32-bit 哈希函数
 * @param: str - 输入字符串
 * @return: 32-bit 哈希值
 */
uint32_t Ctrl_Hash_FNV1a(const char* str)
{
    uint32_t hash = FNV_OFFSET_BASIS_32;
    
    // 1. 参数检查
    if (str == NULL)
    {
        Control_Log(CONTROL_LOG_WARN, (uint8_t *)"NULL string for hash\n", 22);
        return hash;
    }

    // 2. 计算哈希值
    for (const char* p = str; *p; p++)
    {
        hash ^= (uint32_t)(*p); // (异或)
        hash *= FNV_PRIME_32;  // (乘)
    }
    
    return hash;
}


/**
 * @brief: 检查哈希值是否碰撞
 * @param: hashes - 哈希值数组
 * @param: hash_count - 哈希值数组的元素数量
 * @param: new_hash - 新的哈希值
 * @return: 1 - 碰撞，0 - 未碰撞
 */
/* 实现在注册函数中，目前以弃用此方法
char Ctrl_Hash_CheckCollision(uint32_t hashes[], size_t hash_count, uint32_t new_hash)
{
    for(size_t i = 0; i < hash_count; i++)
    {
        if(hashes[i] == new_hash)
        {
            return 1; // 碰撞
        }
    }
    return 0; // 未碰撞
}*/
