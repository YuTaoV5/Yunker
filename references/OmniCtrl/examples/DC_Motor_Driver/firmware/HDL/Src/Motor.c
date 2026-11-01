/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 12:55
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "Motor.h"


Motor_t Motor_A = {
    .a4950_ = &A4950_A,
    .encoder_ = &Encoder_A,
    .target_speed_ = 0,
};
Motor_t Motor_B = {
    .a4950_ = &A4950_B,
    .encoder_ = &Encoder_B,
    .target_speed_ = 0,
};


/**
 * @brief 电机初始化
 * @param None
 * @return None
 */
void Motor_Init(void)
{
    // 初始化A4950
    A4950_Init(&A4950_A);
    A4950_Init(&A4950_B);
    A4950_SetSpeed(&A4950_A, 0);
    A4950_SetSpeed(&A4950_B, 0);

    // 初始化编码器
    Encoder_Init(&Encoder_A);
    Encoder_Init(&Encoder_B);
}

/**
 * @brief 设置电机速度
 * @param motor 电机指针
 * @param speed 目标速度
 * @return None
 */
void Motor_SetSpeed(Motor_t *motor, float speed)
{
    A4950_SetSpeed(motor->a4950_, speed);
}

void Motor_SetTarget(Motor_t *motor, float target_speed)
{
    motor->target_speed_ = target_speed;
}

/**
 * @brief 获取电机速度
 * @param motor 电机指针
 * @return 电机当前速度
 */
int16_t Motor_GetSpeed(Motor_t *motor)
{
    float speed = motor->encoder_->Count_;
    return (int16_t)speed;
}

/**
 * @brief 获取电机目标速度
 * @param motor 电机指针
 * @return 电机目标速度
 */
int16_t Motor_GetTarget(Motor_t *motor)
{
    float target_speed = motor->target_speed_;
    return (int16_t)target_speed;
}
