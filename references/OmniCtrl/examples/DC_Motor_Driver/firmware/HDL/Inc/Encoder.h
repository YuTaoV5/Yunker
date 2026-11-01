/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-15 0:15
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __ENCODER_H
#define __ENCODER_H

#include "bsp_common.h"
#include "bsp_tim.h"


/*-----------------------------------类定义------------------------------------*/
/**
 * @brief: 编码器类
 * @description: 该类用于控制编码器模块
 */
typedef struct {
    BSP_TIMx_t TIMx_;
    float Count_;    // 编码器计数
}Encoder_t;


/*-----------------------------------全局变量-----------------------------------*/
extern Encoder_t Encoder_A, Encoder_B;


/*-----------------------------------函数声明-----------------------------------*/
void Encoder_Init(Encoder_t *encoder);
void Encoder_Update(Encoder_t *encoder);
void Encoder_Reset(Encoder_t *encoder);
float Encoder_GetCount(Encoder_t *encoder);

#endif  // __ENCODER_H
