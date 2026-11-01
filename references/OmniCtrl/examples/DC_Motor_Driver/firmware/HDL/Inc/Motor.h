/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 12:55
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __APP_MOTOR_H
#define __APP_MOTOR_H

#include "A4950.h"
#include "Encoder.h"


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief: 电机类
 * @description: 该类用于控制电机模块
 */
typedef struct
{
    A4950_t *a4950_;
    Encoder_t *encoder_;
    float target_speed_;
}Motor_t;


/*-----------------------------------全局变量-----------------------------------*/
extern Motor_t Motor_A, Motor_B;


/*-----------------------------------函数声明-----------------------------------*/
void Motor_Init(void);
void Motor_SetSpeed(Motor_t *motor, float speed);
int16_t Motor_GetSpeed(Motor_t *motor);
int16_t Motor_GetTarget(Motor_t *motor);
void Motor_SetTarget(Motor_t *motor, float target_speed);

#endif // __APP_MOTOR_H
