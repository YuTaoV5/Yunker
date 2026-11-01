/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 12:07
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __BSP_TIM_H__
#define __BSP_TIM_H__

#include "bsp_common.h"


/*-----------------------------------宏定义------------------------------------*/
#define BSP_PWM_ARR 1000  // 自动重装载值(用于简化占空比计算, 该值在PWM_Start中应用后不应更改)
#define BSP_PWM_DUTY_MAX 1000  // 最大占空比


/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief 定时器实例枚举
 */
typedef enum
{
    BSP_TIM2 = 0,
    BSP_TIM3,
    BSP_TIM4,
    BSP_TIM6,
    BSP_TIM17,
    BSP_TIM_NUM
}BSP_TIMx_t;

/**
 * @brief 定时器通道枚举
 */
typedef enum
{
    BSP_TIM_CHANNEL_1   = 0x00000000U,
    BSP_TIM_CHANNEL_2   = 0x00000004U,
    BSP_TIM_CHANNEL_3   = 0x00000008U,
    BSP_TIM_CHANNEL_4   = 0x0000000CU,
    BSP_TIM_CHANNEL_5   = 0x00000010U,
    BSP_TIM_CHANNEL_6   = 0x00000014U,
    BSP_TIM_CHANNEL_All = 0x0000003CU,
}BSP_TIM_Channel_t;


/*----------------------------------结构体定义----------------------------------*/
typedef void (*BSP_TIM_PeriodElapsedCallback)(BSP_TIMx_t tim); // 周期溢出回调


/*-----------------------------------断言检查-----------------------------------*/
/* Keil断言报错
// 静态断言：确保BSP_PWM_DUTY_MAX不大于BSP_PWM_ARR(编译期检查)
static_assert(
        (BSP_PWM_DUTY_MAX <= BSP_PWM_ARR),
        "BSP_PWM_DUTY_MAX must be less than or equal to BSP_PWM_ARR"
);

// 静态断言：确保BSP定时器通道枚举与HAL库TIM_CHANNEL_t兼容(编译期检查)
static_assert(
        (int)BSP_TIM_CHANNEL_1   == (int)TIM_CHANNEL_1 &&
        (int)BSP_TIM_CHANNEL_2   == (int)TIM_CHANNEL_2 &&
        (int)BSP_TIM_CHANNEL_3   == (int)TIM_CHANNEL_3 &&
        (int)BSP_TIM_CHANNEL_4   == (int)TIM_CHANNEL_4 &&
        (int)BSP_TIM_CHANNEL_5   == (int)TIM_CHANNEL_5 &&
        (int)BSP_TIM_CHANNEL_6   == (int)TIM_CHANNEL_6 &&
        (int)BSP_TIM_CHANNEL_All == (int)TIM_CHANNEL_ALL,
        "BSP_TIM_CHANNEL_t enum values don't match HAL library's TIM_CHANNEL_t!"
);
*/


/*-----------------------------------函数声明-----------------------------------*/
void BSP_TIM_Init(void);
void BSP_TIM_Start(BSP_TIMx_t TIMx);
void BSP_PWM_Start(BSP_TIMx_t TIMx, BSP_TIM_Channel_t Channel);
void BSP_PWM_Stop(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel);
void BSP_PWM_Start_DMA(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel, uint32_t *duty, uint16_t len);
void BSP_PWM_Stop_DMA(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel);
void BSP_PWM_SetDuty(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel, float duty);
uint16_t BSP_PWM_GetDuty(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel);
void BSP_Encoder_Init(BSP_TIMx_t TIMx);
int16_t BSP_Encoder_GetValue(BSP_TIMx_t TIMx);
void BSP_Encoder_Reset(BSP_TIMx_t TIMx);
void BSP_TIM_RegisterPeriodElapsedCallback(BSP_TIMx_t tim, BSP_TIM_PeriodElapsedCallback callback);


#endif //__BSP_TIM_H__
