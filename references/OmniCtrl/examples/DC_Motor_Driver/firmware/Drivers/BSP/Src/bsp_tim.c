/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 12:07
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "bsp_tim.h"
#include "tim.h"

BSP_TIM_PeriodElapsedCallback g_tim_callbacks[BSP_TIM_NUM] = {NULL};

/**
 * @brief 获取定时器句柄
 * @param TIMx 定时器实例枚举
 * @return TIM_HandleTypeDef* 定时器句柄指针
 */
static inline TIM_HandleTypeDef *BSP_TIM_GetHandle(BSP_TIMx_t TIMx)
{
    // 建立端口映射表
    static const TIM_HandleTypeDef *port_table[] = {
            [BSP_TIM2] = &htim2,    // 枚举值0 → TIM2
            [BSP_TIM3] = &htim3,    // 枚举值1 → TIM3
            [BSP_TIM4] = &htim4,    // 枚举值2 → TIM4
            [BSP_TIM6] = &htim6,    // 枚举值3 → TIM6
            [BSP_TIM17] = &htim17,  // 枚举值4 → TIM17
            // 扩展端口时在此添加(如[BSP_TIM1] = &htim1)
    };

    // 检查端口枚举值是否在有效范围内
    if (TIMx < sizeof(port_table) / sizeof(port_table[0])) {
        return (TIM_HandleTypeDef *)port_table[TIMx];
    }
    assert(0);
}

/**
 * @brief 将HAL定时器句柄转换为BSP_TIMx_t枚举
 * @param htim HAL定时器句柄
 * @return BSP_TIMx_t 对应的BSP定时器枚举
 */
static BSP_TIMx_t BSP_TIM_FromHandle(TIM_HandleTypeDef *htim) {
    if (htim == &htim2) return BSP_TIM2;
    else if (htim == &htim3) return BSP_TIM3;
    else if (htim == &htim4) return BSP_TIM4;
    else if (htim == &htim6) return BSP_TIM6;
    else if (htim == &htim17) return BSP_TIM17;
    else assert(0);
}

/**
 * @brief 初始化定时器
 * @param None
 * @return None
 */
void BSP_TIM_Init(void)
{
    MX_TIM2_Init();
    MX_TIM3_Init();
    MX_TIM4_Init();
    MX_TIM6_Init();
    MX_TIM17_Init();
}

/**
 * @brief 启动定时器
 * @param TIMx 定时器实例枚举
 * @return None
 */
void BSP_TIM_Start(BSP_TIMx_t TIMx)
{
    HAL_TIM_Base_Start_IT(BSP_TIM_GetHandle(TIMx));
} 

/**
 * @brief 启动PWM输出
 * @param TIMx 定时器实例枚举
 * @param channel 定时器通道枚举
 * @return None
 */
void BSP_PWM_Start(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel)
{
    BSP_TIM_GetHandle(TIMx)->Instance->ARR = BSP_PWM_ARR;
    HAL_TIM_PWM_Start(BSP_TIM_GetHandle(TIMx), channel);
}

/**
 * @brief 启动PWM输出(_DMA)
 * @param TIMx 定时器实例枚举
 * @param channel 定时器通道枚举
 * @param duty 占空比数组指针
 * @param len 占空比数组长度
 * @return None
 */
void BSP_PWM_Start_DMA(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel, uint32_t *duty, uint16_t len)
{
    HAL_TIM_PWM_Start_DMA(BSP_TIM_GetHandle(TIMx), channel, duty, len);
}

/**
 * @brief 停止PWM输出
 * @param TIMx 定时器实例枚举
 * @param channel 定时器通道枚举
 * @return None
 */
void BSP_PWM_Stop(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel)
{
    HAL_TIM_PWM_Stop(BSP_TIM_GetHandle(TIMx), channel);
}

/**
 * @brief 停止PWM输出(_DMA)
 * @param TIMx 定时器实例枚举
 * @param channel 定时器通道枚举
 */
void BSP_PWM_Stop_DMA(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel)
{
    HAL_TIM_PWM_Stop_DMA(BSP_TIM_GetHandle(TIMx), channel);
}

/**
 * @brief 设置PWM占空比
 * @param TIMx 定时器实例枚举
 * @param channel 定时器通道枚举
 * @param duty 占空比(0~BSP_PWM_DUTY_MAX)
 * @return None
 */
void BSP_PWM_SetDuty(BSP_TIMx_t TIMx, BSP_TIM_Channel_t channel, float duty)
{
    assert(duty <= BSP_PWM_DUTY_MAX);
    duty = duty * BSP_PWM_ARR / BSP_PWM_DUTY_MAX;
    __HAL_TIM_SET_COMPARE(BSP_TIM_GetHandle(TIMx), channel, (uint16_t)duty);
}

/**
 * @brief 获取PWM占空比
 * @param TIMx 定时器实例枚举
 * @param TIM_Channel 定时器通道枚举
 * @return uint16_t 占空比(0~BSP_PWM_DUTY_MAX)
 */
uint16_t BSP_PWM_GetDuty(BSP_TIMx_t TIMx, BSP_TIM_Channel_t TIM_Channel)
{
    return __HAL_TIM_GET_COMPARE(BSP_TIM_GetHandle(TIMx), TIM_Channel) * BSP_PWM_DUTY_MAX / BSP_PWM_ARR;
}

/**
 * @brief 初始化编码器
 * @param TIMx 定时器实例枚举
 * @return None
 */
void BSP_Encoder_Init(BSP_TIMx_t TIMx)
{
    HAL_TIM_Encoder_Start(BSP_TIM_GetHandle(TIMx), TIM_CHANNEL_ALL);
}

/**
 * @brief 获取编码器值
 * @param TIMx 定时器实例枚举
 * @return int16_t 编码器值
 */
int16_t BSP_Encoder_GetValue(BSP_TIMx_t TIMx)
{
    return __HAL_TIM_GET_COUNTER(BSP_TIM_GetHandle(TIMx));
}

/**
 * @brief 重置编码器值
 * @param TIMx 定时器实例枚举
 * @return None
 */
void BSP_Encoder_Reset(BSP_TIMx_t TIMx)
{
    __HAL_TIM_SET_COUNTER(BSP_TIM_GetHandle(TIMx), 0);
}

/**
 * @brief 注册定时器周期结束回调函数
 * @param tim 定时器实例枚举
 * @param callback 周期结束回调函数指针
 * @return None
 */
void BSP_TIM_RegisterPeriodElapsedCallback(BSP_TIMx_t tim, BSP_TIM_PeriodElapsedCallback callback)
{
    // 检查定时器实例是否有效
    if(tim >= BSP_TIM_NUM)
    {
        assert(0);
        return;
    }

    // 注册回调函数
    if(callback != NULL)
    {
        g_tim_callbacks[tim] = callback;
    }
}

/**
 * @brief 定时器周期结束回调函数
 * @param htim HAL定时器句柄
 * @return None
 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    BSP_TIMx_t tim = BSP_TIM_FromHandle(htim);
    
    // 参数有效性检查
    //if (tim < BSP_TIM_NUM)
    {
        // 如果用户注册了回调函数，则调用它
        if (g_tim_callbacks[tim] != NULL)
        {
            g_tim_callbacks[tim](tim);
        }
    }
}
