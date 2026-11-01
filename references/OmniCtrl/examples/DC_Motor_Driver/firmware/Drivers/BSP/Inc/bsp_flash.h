/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-23 17:41
* @version: v1.0.0
* @description: Flash 操作函数
********************************************************************************/
#ifndef __BSP_FLASH_H
#define __BSP_FLASH_H

#include "bsp_common.h"

#ifdef __cplusplus
extern "C" {
#endif


/*-----------------------------------宏定义------------------------------------*/
#define BSP_FLASH_ADDR ((uint32_t)0x0801F800)
#define BSP_FLASH_PAGE_SIZE ((uint32_t)0x800)  // 2KB


/*----------------------------------函数声明-----------------------------------*/
BSP_Status_t BSP_Flash_Write(uint32_t address, uint32_t *data_addr, 
                                uint32_t *lens, uint8_t data_num);


#ifdef __cplusplus
}
#endif

#endif  //__BSP_FLASH_H