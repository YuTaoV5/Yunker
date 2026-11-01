/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-10 01:11
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef CTRL_HASH_H
#define CTRL_HASH_H

#include <stdint.h>
#include <stddef.h>

/*-----------------------------------函数声明-----------------------------------*/
uint32_t Ctrl_Hash_FNV1a(const char* str);
// char Ctrl_Hash_CheckCollision(uint32_t hashes[], size_t hash_count, uint32_t new_hash);

#endif // CTRL_HASH_H
