/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-26 07:39
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "key.h"
#include "log.h"
#include "bsp_interface.h"
#include "bsp_gpio.h"
#include "bsp_rtc.h"

// 按键1配置
Key_Config_t key1_config = {
    .Port_ = KEY1_GPIO_PORT,
    .Pin_ = KEY1_GPIO_PIN,
    .Active_Level_ = KEY_ACTIVE_LEVEL,
};

// 按键2配置
Key_Config_t key2_config = {
    .Port_ = KEY2_GPIO_PORT,
    .Pin_ = KEY2_GPIO_PIN,
    .Active_Level_ = KEY_ACTIVE_LEVEL,
};

/**
 * @brief 初始化按键
 * @param key 按键句柄
 * @param config 按键配置
 */
void Key_Init(Key_Handle_t *key, const Key_Config_t *config)
{
    if (key == NULL || config == NULL) {
        return;
    }
    
    key->Config_ = *config;
    key->State_ = KEY_STATE_RELEASED;
    key->Event_ = KEY_EVENT_NONE;
    key->Press_Time_ = 0;
    key->Long_Press_Threshold_ = KEY_DEFAULT_LONG_PRESS_THRESHOLD;
}

/**
 * @brief 设置长按时间阈值
 * @param key 按键句柄
 * @param threshold 长按时间阈值
 * @note 此函数应放在主循环中调用
 */
void Key_SetLongPressThreshold(Key_Handle_t *key, uint32_t threshold)
{
    if (key != NULL) {
        key->Long_Press_Threshold_ = threshold;
    }
}

/**
 * @brief 扫描按键状态
 * @param key 按键句柄
 */
void Key_Scan(Key_Handle_t *key)
{
    if (key == NULL) {
        return;
    }
    
    // 读取当前引脚电平
    BSP_GPIO_PinState_t current_state = BSP_GPIO_ReadPin(key->Config_.Port_, key->Config_.Pin_);
    
    // 判断按键是否有效
    uint8_t is_active = (current_state == key->Config_.Active_Level_);

    // 清空上次的事件
    if (key->Event_ != KEY_EVENT_NONE) {
        key->Event_ = KEY_EVENT_NONE;
    }
    
    // 处理按键状态机
    switch (key->State_) {
        case KEY_STATE_RELEASED:
            if (is_active) {
                // 按键按下(触发短按事件, 记录按下时间)
                key->State_ = KEY_STATE_PRESSED;
                key->Press_Time_ = BSP_RTC_GetSysTime_ms();
            }
            break;
            
        case KEY_STATE_PRESSED:
            // 按键释放
            if((BSP_RTC_GetSysTime_ms() - key->Press_Time_) >= key->Long_Press_Threshold_
                && key->Event_ != KEY_EVENT_LONG_PRESSED)
            {
                // 按键长按(触发长按事件)
                Log_Debug((uint8_t *)"Key Long Pressed!", 17);
                key->Event_ = KEY_EVENT_LONG_PRESSED;
            }
            if (!is_active)
            {
                // 按键松开
                if(key->Event_ == KEY_EVENT_LONG_PRESSED)
                {
                    // 长按事件已触发, 不处理短按事件
                }
                else
                {
                    // 按键短按(触发短按事件)
                    Log_Debug((uint8_t *)"Key Short Pressed!", 18);
                    key->Event_ = KEY_EVENT_PRESSED;
                }
                key->State_ = KEY_STATE_RELEASED;
            }
            break;
    }
}

/**
 * @brief 获取按键事件
 * @param key 按键句柄
 * @return 按键事件
 * @note 此函数应当在按键状态机每次更新后都予调用，否则可能错过事件
 */
Key_Event_t Key_GetEvent(Key_Handle_t *key)
{
    return (key != NULL) ? key->Event_ : KEY_EVENT_NONE;
}
