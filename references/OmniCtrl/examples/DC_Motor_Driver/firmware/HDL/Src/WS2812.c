/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 23:45
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "WS2812.h"


/**
 * @brief 构造函数
 * @param TIMx 定时器句柄指针
 * @param channel 通道
 * @param number LED数量
 */
WS2812::WS2812(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel, uint16_t number) {
    TIMx_ = TIMx;
    Channel_ = channel;
    Number_ = number;

    // 初始化vector缓冲区：(number+1)个LED * 24位/LED，初始值0
    buf_.resize(number + 1);  // 外层vector大小：LED数量+1（含复位行）
    for (uint16_t i = 0; i <= Number_; i++) {
        buf_[i].resize(24, 0);  // 内层vector：24位/LED，初始化为0
    }
    // 计算CCR_1和CCR_0
    CCR_1_ = static_cast<uint16_t>(BSP_PWM_DUTY_MAX * 0.66f);
    CCR_0_ = static_cast<uint16_t>(BSP_PWM_DUTY_MAX * 0.33f);
}

/**
 * @brief 析构函数
 */
WS2812::~WS2812() {
    BSP_PWM_Stop_DMA(TIMx_, Channel_);
}

/**
  * @brief  两次发送间隔复位
  * @retval None
  * @note   延时应当大于24us, 这里为24*1.25=37.5us。
  *         如果此时无法满足复位需求，则再将Pixel_Buf再加一行并重写此函数。
  * @note   此函数仅供内部使用
  */
void WS2812::Reset_Load()
{
    for(uint8_t i=0; i<24; i++){
        Buf_[Number_][i] = 0;
    }
}

/**
  * @brief  发送显示数组
  * @retval None
  * @note   此函数仅供内部使用
  */
void WS2812::Send_Array()
{
    uint16_t* dma_ptr = &Buf_[0][0];
    BSP_PWM_Start_DMA(TIMx_, Channel_, reinterpret_cast<uint32_t*>(dma_ptr), (Number_+1)*24);
}

/**
 * @brief GRB888编码添加亮度控制
 * @param GRB888      颜色（格式：0xGGRRBB，G高8位，R中8位，B低8位）
 * @param Brightness  亮度值(0.0-1.0)
 * @return 带亮度控制的GRB888编码
 */
uint32_t WS2812::GRB888_Brightness(uint32_t GRB888, float Brightness)
{
    // 钳位亮度值到[0.0, 1.0]
    if (Brightness < 0.0f) Brightness = 0.0f;
    else if (Brightness > 1.0f) Brightness = 1.0f;

    // 提取各颜色分量（8位/通道）
    uint8_t G = (GRB888 >> 16) & 0xFF;  // 高8位：G通道
    uint8_t R = (GRB888 >> 8)  & 0xFF;  // 中8位：R通道
    uint8_t B = GRB888         & 0xFF;  // 低8位：B通道

    // 应用亮度并限制范围
    G = static_cast<uint8_t>(static_cast<float>(G) * Brightness);
    R = static_cast<uint8_t>(static_cast<float>(R) * Brightness);
    B = static_cast<uint8_t>(static_cast<float>(B) * Brightness);

    // 重新组合为GRB888格式
    return (G << 16) | (R << 8) | B;
}

/**
  * @brief  刷新显示
  * @retval None
  */
void WS2812::Flush()
{
    Reset_Load();   //复位
    Send_Array();    //发送数据
}

/**
  * @brief  WS2812设置单个灯珠颜色
  * @param LedID    灯珠的ID
  * @param GRB888   颜色
  * @retval None
  */
void WS2812::Set_One(uint8_t LedID, uint32_t GRB888)
{
    if(LedID > Number_ - 1) return;   // 防止数据溢出
    for(uint8_t i=0; i<24; i++){
        // 将RGB888转化为高低电平(CCR)
        Buf_[LedID][i] = ((GRB888 & (1 << (23-i)))? (CCR_1_):CCR_0_);
    }
}

/**
  * @brief  WS2812批量设置颜色
  * @param startID  第一个灯珠的ID
  * @param endID    最后一个灯珠的ID
  * @param GRB888   颜色
  * @retval None
  */
void WS2812::Set_More(uint8_t startID, uint8_t endID, uint32_t GRB888)
{
    if(startID > endID) return;

    for(uint8_t i=startID; i<=endID; i++){
        Set_One(i, GRB888);
    }
}
