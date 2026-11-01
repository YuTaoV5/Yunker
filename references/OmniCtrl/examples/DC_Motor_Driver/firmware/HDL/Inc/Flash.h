/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-03 21:11
* @version: v1.0.0
* @description: Flash
********************************************************************************/
#ifndef __FLASH_H
#define __FLASH_H

#include "bsp_flash.h"

void Flash_Write(uint32_t address, uint32_t *data_addr, uint32_t *lens, uint8_t data_num);
void Flash_Read(uint32_t address, uint8_t *data, uint32_t len);

#endif  // __FLASH_H
