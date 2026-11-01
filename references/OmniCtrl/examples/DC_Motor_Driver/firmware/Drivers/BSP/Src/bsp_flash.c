/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-23 17:41
* @version: v1.0.0
* @description: Flash 操作函数
********************************************************************************/
#include "bsp_flash.h"
#include <string.h>

/**
 * @brief: 解锁 Flash 控制寄存器
 * @return: BSP_Status_t
 */
static BSP_Status_t BSP_Flash_Unlock(void)
{
    // 解锁 Flash 控制寄存器
    HAL_FLASH_Unlock();

    // 检查是否解锁成功
    if(__HAL_FLASH_GET_FLAG(FLASH_FLAG_BSY))
    {
        return BSP_ERROR;
    }

    return BSP_OK;
}

/**
 * @brief: 锁定 Flash 控制寄存器
 * @return: BSP_Status_t
 */
static BSP_Status_t BSP_Flash_Lock(void)
{
    // 锁定 Flash 控制寄存器
    HAL_FLASH_Lock();

    // 检查是否锁定成功
    if(__HAL_FLASH_GET_FLAG(FLASH_FLAG_BSY))
    {
        return BSP_ERROR;
    }

    return BSP_OK;
}

/**
 * @brief: 擦除 Flash 页面
 * @param: page_address: 页面地址
 * @return: BSP_Status_t
 */
static BSP_Status_t BSP_Flash_ErasePage(uint32_t page_address)
{
    // 1. 配置擦除参数
    FLASH_EraseInitTypeDef erase_init;
    erase_init.TypeErase = FLASH_TYPEERASE_PAGES;   // 按页面擦除
    erase_init.Banks = FLASH_BANK_1;
    erase_init.Page = (page_address - FLASH_BASE) / BSP_FLASH_PAGE_SIZE; // 计算页号
    erase_init.NbPages = 1;                         // 擦除1页

    // 2. 执行擦除操作
    uint32_t page_error;
    if(HAL_FLASHEx_Erase(&erase_init, &page_error) != HAL_OK)
    {
        return BSP_ERROR;
    }

    return BSP_OK;
}

/**
 * @brief: 写入 Flash 数据
 * @param: address: 写入地址
 * @param: data_addr: 数据指针的数组
 * @param: lens: 数据长度的数组
 * @param: data_num: 数据数量
 * @return: BSP_Status_t
 */
BSP_Status_t BSP_Flash_Write(uint32_t address, uint32_t *data_addr, uint32_t *lens, 
                            uint8_t data_num)
{
    // 1. 计算总长度
    uint32_t len = 0;
    for(uint8_t i = 0; i < data_num; i++)
    {
        len += lens[i];
    }
    
    // 2. 计算地址
    uint32_t double_count = (len + 7) / 8;    // 计算需要的双字数，向上取整
    uint32_t write_size = double_count * 8;   // 计算需要的内存
    uint32_t page_start = address & ~(BSP_FLASH_PAGE_SIZE - 1); // 计算页面起始地址

    // 3. 检查地址是否对齐或溢出
    if(address % 8 != 0 || address < FLASH_BASE || 
        (address + write_size) > (FLASH_BASE + FLASH_SIZE) ||
        write_size > BSP_FLASH_PAGE_SIZE)
    {
        return BSP_ERROR;
    }

    // 4. 解锁 Flash 控制寄存器
    if(BSP_Flash_Unlock() != BSP_OK) return BSP_ERROR;

    // 5. 擦除页面
    if(BSP_Flash_ErasePage(page_start) != BSP_OK) return BSP_ERROR;

    // 6. 写入数据
    uint8_t cur_data_idx = 0;       // 当前数据索引
    uint32_t cur_data_offset = 0;   // 当前数据偏移量(已使用量)

    for(uint32_t i = 0; i < double_count; i++)
    {
        uint64_t data_to_write = 0xFFFFFFFFFFFFFFFF;    // 当前要写入的数据
        uint8_t bytes_filled = 0;   // 当前已填充的字节数(0-7)

        while(bytes_filled < 8 && cur_data_idx < data_num)
        {
            // 获取当前源数据指针
            uint8_t *src_ptr = (uint8_t *)data_addr[cur_data_idx];
            uint32_t src_len = lens[cur_data_idx];

            // 计算当前 Buffer 还能提供多少字节
            uint32_t buf_remain = src_len - cur_data_offset;

            // 如果当前 Buffer 没有数据了，切换到下一个数据
            if(buf_remain == 0)
            {
                cur_data_idx++;
                cur_data_offset = 0;
                continue;
            }

            // 计算本次需要填充的字节
            uint32_t bytes_to_fill = 8 - bytes_filled;
            if(buf_remain < bytes_to_fill)
            {
                bytes_to_fill = buf_remain;
            }
            
            // 填充数据到 data_to_write
            // 正确写法
            memcpy(((uint8_t *)&data_to_write) + bytes_filled, 
                    src_ptr + cur_data_offset, bytes_to_fill);
            cur_data_offset += bytes_to_fill;
            bytes_filled += bytes_to_fill;
        }

        // 写入数据到 Flash
        if(HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, address + i * 8, 
                            data_to_write) != HAL_OK)
        {
            BSP_Flash_Lock();
            return BSP_ERROR;
        }
    }

    // 7. 锁定 Flash 控制寄存器
    if(BSP_Flash_Lock() != BSP_OK)
    {
        return BSP_ERROR;
    }

    return BSP_OK;
}
