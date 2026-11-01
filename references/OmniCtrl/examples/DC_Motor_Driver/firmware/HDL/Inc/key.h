/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 01:57
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __KEY_H
#define __KEY_H

#include "bsp_gpio.h"


/*-----------------------------------类型定义-----------------------------------*/
/**
 * @brief 按键状态枚举
 */
typedef enum {
    KEY_STATE_RELEASED = 0,    // 按键释放状态
    KEY_STATE_PRESSED,         // 按键按下状态
} Key_State_t;

/**
 * @brief 按键事件枚举
 */
typedef enum {
    KEY_EVENT_NONE = 0,        // 无按键事件
    KEY_EVENT_PRESSED,         // 按键按下事件
    KEY_EVENT_RELEASED,        // 按键释放事件
    KEY_EVENT_LONG_PRESSED,    // 按键长按事件
} Key_Event_t;

/**
 * @brief 按键配置结构体
 */
typedef struct {
    BSP_GPIO_Port_t Port_;      // 按键连接的GPIO端口
    BSP_GPIO_Pin_t Pin_;        // 按键连接的GPIO引脚
    BSP_GPIO_PinState_t Active_Level_; // 按键有效电平
} Key_Config_t;

/**
 * @brief 按键句柄结构体
 */
typedef struct {
    Key_Config_t Config_;            // 按键配置
    Key_State_t State_;              // 当前按键状态
    Key_Event_t Event_;              // 当前按键事件
    uint32_t Press_Time_;            // 按键按下时的系统时间(ms)
    uint32_t Long_Press_Threshold_;  // 长按时间阈值(ms)
} Key_Handle_t;


/*-----------------------------------变量定义-----------------------------------*/
extern Key_Config_t key1_config, key2_config;


/*-----------------------------------宏定义-----------------------------------*/
#define KEY_DEFAULT_LONG_PRESS_THRESHOLD 400


/*-----------------------------------函数声明-----------------------------------*/
void Key_Init(Key_Handle_t *key, const Key_Config_t *config);
void Key_SetLongPressThreshold(Key_Handle_t *key, uint32_t threshold);
void Key_Scan(Key_Handle_t *key);
Key_Event_t Key_GetEvent(Key_Handle_t *key);

#endif /* __KEY_H */
