/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-26 01:30
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __APP_OLED_H
#define __APP_OLED_H

#include "OLED.h"
#include "ui_menu.h"

/*-----------------------------------宏定义-----------------------------------*/
#define APP_OLED_LINE_NUM 5   // OLED显示行数


/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief OLED界面枚举
 */
typedef enum
{
    APP_UI_MAIN = 0,
    APP_UI_SETTING,
} APP_UI_t;


/*-----------------------------------变量声明-----------------------------------*/
extern uint8_t APP_UI_Refresh_Flag;         // 刷新标志位
extern APP_UI_t APP_UI;                     // 当前OLED界面

extern UI_Menu_Item_t UI_Setting;            // 设置菜单
extern UI_Menu_Item_t UI_Setting_Exit;       // 设置菜单退出项
extern UI_Menu_Display_t UI_Menu;            // 菜单显示实例


/*-----------------------------------函数声明-----------------------------------*/
void APP_OLED_Init(void);
void APP_Process(void);

#endif
