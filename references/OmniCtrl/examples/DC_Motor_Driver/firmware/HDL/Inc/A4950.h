/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 12:55
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef A4950_H_
#define A4950_H_

#include "bsp_common.h"
#include "bsp_tim.h"

/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief: 电机模式枚举
 * @description: 模式为A4950_Brake时，电机刹车；模式为A4950_Coast时，电机滑行
 */
typedef enum
{
    A4950_BREAK = 0,
    A4950_COAST
}A4950_Mode_t;


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief: A4950电机驱动类
 * @description: 该类用于控制A4950电机驱动模块
 */
typedef struct {
    BSP_TIMx_t TIMx_1_;
    BSP_TIM_Channel_t Channel_1_;
    BSP_TIMx_t TIMx_2_;
    BSP_TIM_Channel_t Channel_2_;
    float Speed_Max_;     // 最大速度
    A4950_Mode_t Mode_;      // 模式
}A4950_t;


/*-----------------------------------宏声明-----------------------------------*/
#define A4950_SPEED_DEFAULT (BSP_PWM_DUTY_MAX / 2)


/*-----------------------------------全局变量-----------------------------------*/
extern A4950_t A4950_A, A4950_B;


/*-----------------------------------函数声明-----------------------------------*/
void A4950_Init(A4950_t *a4950);
void A4950_SetSpeedMax(A4950_t *a4950, float speed_max);
void A4950_SetMode(A4950_t *a4950, A4950_Mode_t mode);
void A4950_SetSpeed(A4950_t *a4950, float speed);

#endif // A4950_H_
