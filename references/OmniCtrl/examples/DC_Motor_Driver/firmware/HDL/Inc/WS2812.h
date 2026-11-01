/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 23:45
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef WS2812_H_
#define WS2812_H_

#include "bsp_common.h"
#include "bsp_tim.h"
#include <vector>

class WS2812{
private:
    BSP_TIMx_t TIMx_;                // 定时器实例
    BSP_TIM_Channel_t Channel_;      // 定时器通道
    uint16_t Number_;                // 灯的数量
    std::vector<std::vector<uint16_t>> Buf_; // 动态缓冲区，存储LED颜色数据
    uint16_t CCR_1_;                 // 发送1时的CCR值(控制在66%的占空比)
    uint16_t CCR_0_;                 // 发送0时的CCR值(控制在33%的占空比)

    void Reset_Load();
    void Send_Array();

public:
    WS2812(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel, uint16_t number);
    ~WS2812();

    static uint32_t GRB888_Brightness(uint32_t GRB888, float Brightness);
    void Flush();
    void Set_One(uint8_t LedID, uint32_t GRB888);
    void Set_More(uint8_t startID, uint8_t endID, uint32_t GRB888);
};

#endif // WS2812_H_
