/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-15 0:15
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "Encoder.h"
#include "bsp_interface.h"


Encoder_t Encoder_A = {
    .TIMx_ = EncoderA_TIMx,
    .Count_ = 0,
};

Encoder_t Encoder_B = {
    .TIMx_ = EncoderB_TIMx,
    .Count_ = 0,
};


/**
 * @brief 初始化编码器
 * @param encoder 编码器指针
 * @return None
 */
void Encoder_Init(Encoder_t *encoder)
{
    BSP_Encoder_Init(encoder->TIMx_);
}

/**
 * @brief 更新编码器计数
 * @param encoder 编码器指针
 * @return None
 */
void Encoder_Update(Encoder_t *encoder)
{
    encoder->Count_ = (float)BSP_Encoder_GetValue(encoder->TIMx_);
    BSP_Encoder_Reset(encoder->TIMx_);
}

/**
 * @brief 重置编码器计数
 * @param encoder 编码器指针
 * @return None
 */
void Encoder_Reset(Encoder_t *encoder)
{
    encoder->Count_ = 0;
}

/**
 * @brief 获取编码器计数
 * @param encoder 编码器指针
 * @return int16_t 编码器计数
 */
float Encoder_GetCount(Encoder_t *encoder)
{
    return encoder->Count_;
}
