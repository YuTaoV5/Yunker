/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 12:55
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "A4950.h"
#include "bsp_interface.h"


A4950_t A4950_A = {
    .TIMx_1_ = A4950A_TIMx_1,
    .TIMx_2_ = A4950A_TIMx_2,
    .Channel_1_ = A4950A_TIM_CHANNEL_1,
    .Channel_2_ = A4950A_TIM_CHANNEL_2,
    .Speed_Max_ = A4950_SPEED_DEFAULT,
};
A4950_t A4950_B = {
    .TIMx_1_ = A4950B_TIMx_1,
    .TIMx_2_ = A4950B_TIMx_2,
    .Channel_1_ = A4950B_TIM_CHANNEL_1,
    .Channel_2_ = A4950B_TIM_CHANNEL_2,
    .Speed_Max_ = A4950_SPEED_DEFAULT,
};


/**
 * @brief: 构造函数
 * @param {BSP_TIMx_t} TIMx_1 定时器1
 * @param {BSP_TIM_Channel_t} channel_1 通道1
 * @param {BSP_TIMx_t} TIMx_2 定时器2
 * @param {BSP_TIM_Channel_t} channel_2 通道2
 * @param {uint16_t} speed_max 最大速度
 */
void A4950_Init(A4950_t *A4950)
{
    A4950->Speed_Max_ = A4950->Speed_Max_ < BSP_PWM_DUTY_MAX ? 
        A4950->Speed_Max_ : BSP_PWM_DUTY_MAX;
    A4950->Mode_ = A4950_COAST; 
    BSP_PWM_Start(A4950->TIMx_1_, A4950->Channel_1_);
    BSP_PWM_Start(A4950->TIMx_2_, A4950->Channel_2_);
}

/**
 * @brief: 设置最大速度
 * @param {uint16_t} speed_max 最大速度
 * @description: 最大速度不能超过BSP_PWM_DUTY_MAX
 */
void A4950_SetSpeedMax(A4950_t *A4950, float speed_max)
{
    A4950->Speed_Max_ = A4950->Speed_Max_ < BSP_PWM_DUTY_MAX ? 
        A4950->Speed_Max_ : BSP_PWM_DUTY_MAX;
}

/**
 * @brief: 设置模式
 * @param {A4950_Mode_t} mode 模式
 * @description: 模式为A4950_Brake时，电机刹车；模式为A4950_Coast时，电机滑行
 */
void A4950_SetMode(A4950_t *A4950, A4950_Mode_t mode)
{
    A4950->Mode_ = mode;
}

/**
 * @brief: 设置速度
 * @param {int32_t} speed 速度
 * @description: 速度为正时，电机正转；速度为负时，电机反转；速度为0时，电机停止
 * @note: 速度的绝对值不能超过BSP_PWM_DUTY_MAX
 */
void A4950_SetSpeed(A4950_t *A4950, float speed)
{
    /* 速度范围限制 */
    if(speed > A4950->Speed_Max_) speed = A4950->Speed_Max_;
    else if(speed < -A4950->Speed_Max_) speed = -A4950->Speed_Max_;

    /* 速度设置 */
    if(speed > 0){
        BSP_PWM_SetDuty(A4950->TIMx_1_, A4950->Channel_1_, speed);
        BSP_PWM_SetDuty(A4950->TIMx_2_, A4950->Channel_2_, 0);
    }
    else if(speed < 0){
        BSP_PWM_SetDuty(A4950->TIMx_1_, A4950->Channel_1_, 0);
        BSP_PWM_SetDuty(A4950->TIMx_2_, A4950->Channel_2_, -speed);
    }
    else{
        if(A4950->Mode_ == A4950_BREAK){
            BSP_PWM_SetDuty(A4950->TIMx_1_, A4950->Channel_1_, A4950->Speed_Max_);
            BSP_PWM_SetDuty(A4950->TIMx_2_, A4950->Channel_2_, A4950->Speed_Max_);
        }
        else{
            BSP_PWM_SetDuty(A4950->TIMx_1_, A4950->Channel_1_, 0);
            BSP_PWM_SetDuty(A4950->TIMx_2_, A4950->Channel_2_, 0);
        }
    }
}
