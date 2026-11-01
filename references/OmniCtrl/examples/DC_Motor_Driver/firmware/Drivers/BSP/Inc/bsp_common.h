/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 0:21
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __BSP_COMMON_H__
#define __BSP_COMMON_H__

#include "stm32g4xx_hal.h"
#include <assert.h>

/**
 * @brief: 状态枚举
 * @note: 0: 成功, 1: 失败
 */
typedef enum
{
    BSP_OK = 0,
    BSP_ERROR = 1,
}BSP_Status_t;

#endif //__BSP_COMMON_H__
