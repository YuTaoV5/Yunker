/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 10:47
* @version: v1.0.0
* @description: SPI驱动头文件,包含SPI初始化、发送、DMA发送等函数
********************************************************************************/
#ifndef __BSP_SPI_H__
#define __BSP_SPI_H__

#include "bsp_common.h"


#ifdef __cplusplus
extern "C" {
#endif


/*-----------------------------------宏定义------------------------------------*/
#define BSP_SPI_TIMEOUT 0xFFFF  // 默认超时时间


/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief SPI外设实例枚举（根据硬件实际支持的SPI外设扩展）
 */
typedef enum {
    BSP_SPI1 = 0,
} BSP_SPIx_t;


/*-----------------------------------函数声明-----------------------------------*/
void BSP_SPI_Init(BSP_SPIx_t SPIx);
void BSP_SPI_Transmit(BSP_SPIx_t SPIx, uint8_t *data, uint16_t size);
void BSP_SPI_Transmit_DMA(BSP_SPIx_t SPIx, uint8_t *data, uint16_t size, uint32_t timeout);


#ifdef __cplusplus
}
#endif


#endif //__BSP_SPI_H__
