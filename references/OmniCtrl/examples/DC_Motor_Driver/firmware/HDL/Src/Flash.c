/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-03 21:11
* @version: v1.0.0
* @description: Flash
********************************************************************************/
#include "Flash.h"


// 未来增加多页写入
/**
 * @brief: 写入 Flash 数据
 * @param: address: 写入地址(0x000-0x800)(2KB)
 * @param: data: 数据指针
 * @param: len: 数据长度
 * @return: void
 */
void Flash_Write(uint32_t address, uint32_t *data_addr, uint32_t *lens, uint8_t data_num)
{
    BSP_Flash_Write(BSP_FLASH_ADDR + address, data_addr, lens, data_num);
}

/**
 * @brief: 读取 Flash 数据
 * @param: address: 读取地址(0x000-0x800)(2KB)
 * @param: data: 数据指针
 * @param: len: 数据长度
 * @return: void
 */
void Flash_Read(uint32_t address, uint8_t *data, uint32_t len)
{
    for(uint32_t i = 0; i < len; i++)
    {
        data[i] = *((uint8_t *)(BSP_FLASH_ADDR + address + i));
    }
}
