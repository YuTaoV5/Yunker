/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 0:19
* @version: v1.0.0
* @description: BSP层GPIO头文件，封装底层驱动库GPIO操作，提供统一的端口、引脚和状态枚举
********************************************************************************/
#ifndef __BSP_GPIO_H__
#define __BSP_GPIO_H__

#include "bsp_common.h"  // 包含BSP层通用定义


#ifdef __cplusplus
extern "C" {
#endif


/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief BSP层GPIO端口枚举
 * @note 枚举值为整数索引，通过BSP_GPIO_GetPort()函数映射到实际硬件端口
 * @see bsp_gpio.c中的BSP_GPIO_GetPort()函数实现（需根据目标硬件适配）
 */
typedef enum
{
    BSP_GPIO_PORT_A = 0,    /* 抽象端口A（对应硬件平台的GPIO端口A） */
    BSP_GPIO_PORT_B,        /* 抽象端口B（对应硬件平台的GPIO端口B） */
    // 扩展端口时需同步修改BSP_GPIO_GetPort()及底层硬件初始化
} BSP_GPIO_Port_t;

/**
 * @brief BSP层GPIO引脚枚举
 * @note 取值与底层驱动库的引脚宏定义一致，支持按位或操作（如同时控制多个引脚）
 * @note 位掩码格式：每个引脚对应1个bit位，如0x0001表示第0位引脚
 */
typedef enum
{
    BSP_GPIO_PIN_0  = 0x0001,  /* 引脚0（bit0置位） */
    BSP_GPIO_PIN_1  = 0x0002,  /* 引脚1（bit1置位） */
    BSP_GPIO_PIN_2  = 0x0004,  /* 引脚2（bit2置位） */
    BSP_GPIO_PIN_3  = 0x0008,  /* 引脚3（bit3置位） */
    BSP_GPIO_PIN_4  = 0x0010,  /* 引脚4（bit4置位） */
    BSP_GPIO_PIN_5  = 0x0020,  /* 引脚5（bit5置位） */
    BSP_GPIO_PIN_6  = 0x0040,  /* 引脚6（bit6置位） */
    BSP_GPIO_PIN_7  = 0x0080,  /* 引脚7（bit7置位） */
    BSP_GPIO_PIN_8  = 0x0100,  /* 引脚8（bit8置位） */  
    BSP_GPIO_PIN_9  = 0x0200,  /* 引脚9（bit9置位） */
    BSP_GPIO_PIN_10 = 0x0400,  /* 引脚10（bit10置位） */
    BSP_GPIO_PIN_11 = 0x0800,  /* 引脚11（bit11置位） */
    BSP_GPIO_PIN_12 = 0x1000,  /* 引脚12（bit12置位） */
    BSP_GPIO_PIN_13 = 0x2000,  /* 引脚13（bit13置位） */
    BSP_GPIO_PIN_14 = 0x4000,  /* 引脚14（bit14置位） */
    BSP_GPIO_PIN_15 = 0x8000,  /* 引脚15（bit15置位） */
    BSP_GPIO_PIN_All= 0xFFFF,  /* 所有引脚（bit0~bit15全置位） */
} BSP_GPIO_Pin_t;

/**
 * @brief BSP层GPIO引脚状态枚举（高低电平）
 * @note 与底层驱动库的引脚状态定义兼容，可直接转换为底层状态参数
 */
typedef enum
{
    BSP_GPIO_PIN_RESET = 0,  /* 引脚复位（低电平），对应底层驱动的复位状态 */
    BSP_GPIO_PIN_SET,        /* 引脚置位（高电平），对应底层驱动的置位状态 */
} BSP_GPIO_PinState_t;


/*-----------------------------------断言检查-----------------------------------*/
/* Keil断言报错
// 静态断言：确保BSP引脚枚举与HAL库GPIO_Pin_t兼容(编译期检查)
static_assert(
        BSP_GPIO_PIN_0 == GPIO_PIN_0 &&
        BSP_GPIO_PIN_1 == GPIO_PIN_1 &&
        BSP_GPIO_PIN_2 == GPIO_PIN_2 &&
        BSP_GPIO_PIN_3 == GPIO_PIN_3 &&
        BSP_GPIO_PIN_4 == GPIO_PIN_4 &&
        BSP_GPIO_PIN_5 == GPIO_PIN_5 &&
        BSP_GPIO_PIN_6 == GPIO_PIN_6 &&
        BSP_GPIO_PIN_7 == GPIO_PIN_7 &&
        BSP_GPIO_PIN_8 == GPIO_PIN_8 &&
        BSP_GPIO_PIN_9 == GPIO_PIN_9 &&
        BSP_GPIO_PIN_10 == GPIO_PIN_10 &&
        BSP_GPIO_PIN_11 == GPIO_PIN_11 &&
        BSP_GPIO_PIN_12 == GPIO_PIN_12 &&
        BSP_GPIO_PIN_13 == GPIO_PIN_13 &&
        BSP_GPIO_PIN_14 == GPIO_PIN_14 &&
        BSP_GPIO_PIN_15 == GPIO_PIN_15 &&
        BSP_GPIO_PIN_All == GPIO_PIN_All,
        "BSP_GPIO_PIN_enum values don't match HAL library's GPIO_Pin_t!"
);

// 静态断言：确保BSP引与HAL库兼容(编译期检查)
static_assert(
    (int)BSP_GPIO_Pin_Reset == (int)GPIO_PIN_RESET &&
    (int)BSP_GPIO_Pin_Set == (int)GPIO_PIN_SET,
    "BSP_GPIO_PinState_t enum values don't match HAL library's GPIO_PinState_t!"
);
*/

/*----------------------------------数声明-----------------------------------*/
void BSP_GPIO_Init(void);
BSP_GPIO_PinState_t BSP_GPIO_ReadPin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin);
void BSP_GPIO_WritePin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin, BSP_GPIO_PinState_t PinState);
void BSP_GPIO_SetPin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin);
void BSP_GPIO_ResetPin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin);
void BSP_GPIO_TogglePin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin);

#ifdef __cplusplus
}
#endif


#endif //__BSP_GPIO_H__
