/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-26 01:30
* @version: v1.0.0
* @description: OLED显示模块
********************************************************************************/
#include "app_oled.h"
#include "app_system.h"
#include <stdio.h>
#include "motor.h"

uint8_t APP_UI_Refresh_Flag = 1;    // 刷新标志位
APP_UI_t APP_UI = APP_UI_SETTING;   // 当前OLED界面
static uint8_t APP_UI_Buffer[30];   // 用于存储OLED显示字符串的缓冲区

/*------------------------------显示模块实例------------------------------*/
// 菜单显示实例声明
UI_Menu_Display_t UI_Menu;
// 设置菜单实例声明
UI_Menu_Item_t UI_Setting;
UI_Menu_Item_t UI_Setting_ID;
UI_Menu_Item_t UI_Setting_Serial;
UI_Menu_Item_t UI_Setting_Baud;
UI_Menu_Item_t UI_Setting_Parity;
UI_Menu_Item_t UI_Setting_Response;
UI_Menu_Item_t UI_Setting_Dir;
UI_Menu_Item_t UI_Setting_DispSleep;
UI_Menu_Item_t UI_Setting_DispSleepTime;
UI_Menu_Item_t UI_Setting_Reset;
UI_Menu_Item_t UI_Setting_Exit;
// ID子菜单实例声明
UI_Menu_Item_t UI_ID_0;
UI_Menu_Item_t UI_ID_1;
UI_Menu_Item_t UI_ID_2;
UI_Menu_Item_t UI_ID_3;
UI_Menu_Item_t UI_ID_4;
UI_Menu_Item_t UI_ID_5;
UI_Menu_Item_t UI_ID_6;
UI_Menu_Item_t UI_ID_7;
// 串口子菜单实例声明
UI_Menu_Item_t UI_Serial_UART;
UI_Menu_Item_t UI_Serial_RS485;
// 波特率子菜单实例声明
UI_Menu_Item_t UI_Baud_9600;
UI_Menu_Item_t UI_Baud_19200;
UI_Menu_Item_t UI_Baud_38400;
UI_Menu_Item_t UI_Baud_57600;
UI_Menu_Item_t UI_Baud_115200;
// 校验位子菜单实例声明
UI_Menu_Item_t UI_Parity_None;
UI_Menu_Item_t UI_Parity_CRC;
UI_Menu_Item_t UI_Parity_0x4B;
// 响应子菜单实例声明
UI_Menu_Item_t UI_Response_None;
UI_Menu_Item_t UI_Response_Done;
UI_Menu_Item_t UI_Response_Repeat;
// 方向子菜单实例声明
UI_Menu_Item_t UI_Dir_CW;
UI_Menu_Item_t UI_Dir_CCW;
// 自动休眠子菜单实例声明
UI_Menu_Item_t UI_DispSleep_On;
UI_Menu_Item_t UI_DispSleep_Off;
// 自动休眠时间子菜单实例声明
UI_Menu_Item_t UI_DispSleepTime_10s;
UI_Menu_Item_t UI_DispSleepTime_30s;
UI_Menu_Item_t UI_DispSleepTime_60s;

/**
 * @brief 获取ID
 */
static inline void APP_OLED_Get_ID(void)
{
    uint8_t id = g_system_status.get_id();
    while(UI_Menu.selected_child_->sibling_id_ != id)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置ID
 * @param id ID值
 */
static inline void APP_OLED_Set_ID(void)
{
    g_system_status.set_id(UI_Menu.selected_child_->sibling_id_);
}

/**
 * @brief 获取串口子菜单
 */
static inline void APP_OLED_Get_Serial(void)
{
    System_Serial_t serial = g_system_status.get_serial();
    while(UI_Menu.selected_child_->sibling_id_ != serial)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置串口子菜单
 */
static inline void APP_OLED_Set_Serial(void)
{
    g_system_status.set_serial(UI_Menu.selected_child_->sibling_id_);
}

static inline void APP_OLED_Get_Baud(void)
{
    System_Baud_t baud = g_system_status.get_baud();
    while(UI_Menu.selected_child_->sibling_id_ != baud)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置波特率
 */
static inline void APP_OLED_Set_Baud(void)
{
    g_system_status.set_baud(UI_Menu.selected_child_->sibling_id_);
}

/**
 * @brief 获取校验位
 */
static inline void APP_OLED_Get_Parity(void)
{
    System_Parity_t parity = g_system_status.get_parity();
    while(UI_Menu.selected_child_->sibling_id_ != parity)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置校验位
 */
static inline void APP_OLED_Set_Parity(void)
{
    // 需要添加真实的校验位设置
    g_system_status.set_parity(UI_Menu.selected_child_->sibling_id_);
}

/**
 * @brief 获取响应位
 */
static inline void APP_OLED_Get_Response(void)
{
    System_Response_t response = g_system_status.get_response();
    while(UI_Menu.selected_child_->sibling_id_ != response)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置响应位
 */
static inline void APP_OLED_Set_Response(void)
{
    // 需要添加真实的响应设置
    g_system_status.set_response(UI_Menu.selected_child_->sibling_id_);
}

/**
 * @brief 获取方向
 */
static inline void APP_OLED_Get_Dir(void)
{
    System_Dir_t dir = g_system_status.get_dir();
    while(UI_Menu.selected_child_->sibling_id_ != dir)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置方向
 */
static inline void APP_OLED_Set_Dir(void)
{
    // 需要添加真实的方向设置
    g_system_status.set_dir(UI_Menu.selected_child_->sibling_id_);
}

/**
 * @brief 获取自动休眠
 */
static inline void APP_OLED_Get_Display_Auto_Sleep(void)
{
    System_Display_Auto_Sleep_t display_auto_sleep = g_system_status.get_display_auto_sleep();
    while(UI_Menu.selected_child_->sibling_id_ != display_auto_sleep)
    {
        UI_Menu.switch_next(&UI_Menu);
        if(UI_Menu.selected_child_ == NULL || UI_Menu.selected_child_->sibling_id_ == 0)
        {
            break;
        }
    }
}

/**
 * @brief 设置自动休眠
 */
static inline void APP_OLED_Set_Display_Auto_Sleep(void)
{
    g_system_status.set_display_auto_sleep(UI_Menu.selected_child_->sibling_id_);
}

/**
 * @brief 显示字符串
 * @param x 字符串起始横坐标（字符坐标非像素坐标）
 * @param y 字符串起始纵坐标
 * @param str 要显示的字符串
 */
static inline void UI_Show_String(unsigned char x, unsigned char y, char *str)
{
    OLED_ShowString(&oled, x*OLED_Word_Width, y*OLED_Word_Height, (uint8_t *)str, OLED_Word_Height, 1);
}

/**
 * @brief 初始化设置菜单
 */
static void UI_Setting_Menu_Init(void)
{
    // 初始化设置菜单
    UI_Menu_Item_Init(&UI_Setting, "Setting", NULL, NULL, NULL);
    UI_Menu_Item_Init(&UI_Setting_ID, "ID        ", &UI_Setting, APP_OLED_Get_ID, APP_OLED_Set_ID);
    UI_Menu_Item_Init(&UI_Setting_Serial, "Serial    ", &UI_Setting, APP_OLED_Get_Serial, APP_OLED_Set_Serial);
    UI_Menu_Item_Init(&UI_Setting_Baud, "Baud      ", &UI_Setting, APP_OLED_Get_Baud, APP_OLED_Set_Baud);
    UI_Menu_Item_Init(&UI_Setting_Parity, "Parity    ", &UI_Setting, APP_OLED_Get_Parity, APP_OLED_Set_Parity);
    UI_Menu_Item_Init(&UI_Setting_Response, "Response  ", &UI_Setting, APP_OLED_Get_Response, APP_OLED_Set_Response);
    UI_Menu_Item_Init(&UI_Setting_Dir, "Dir       ", &UI_Setting, APP_OLED_Get_Dir, APP_OLED_Set_Dir);
    UI_Menu_Item_Init(&UI_Setting_DispSleep, "Disp Sleep", &UI_Setting, APP_OLED_Get_Display_Auto_Sleep, APP_OLED_Set_Display_Auto_Sleep);
    UI_Menu_Item_Init(&UI_Setting_DispSleepTime, "DSLP Time ", &UI_Setting, NULL, NULL);
    UI_Menu_Item_Init(&UI_Setting_Reset, "Reset     ", &UI_Setting, NULL, NULL);
    UI_Menu_Item_Init(&UI_Setting_Exit, "Exit      ", &UI_Setting, NULL, NULL);

    // 初始化ID子菜单
    UI_Menu_Item_Init(&UI_ID_0, "0         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_1, "1         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_2, "2         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_3, "3         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_4, "4         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_5, "5         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_6, "6         ", &UI_Setting_ID, NULL, NULL);
    UI_Menu_Item_Init(&UI_ID_7, "7         ", &UI_Setting_ID, NULL, NULL);

    // 初始化串口子菜单
    UI_Menu_Item_Init(&UI_Serial_UART, "UART      ", &UI_Setting_Serial, NULL, NULL);
    UI_Menu_Item_Init(&UI_Serial_RS485, "RS485     ", &UI_Setting_Serial, NULL, NULL);
    
    // 初始化波特率子菜单
    UI_Menu_Item_Init(&UI_Baud_9600, "9600      ", &UI_Setting_Baud, NULL, NULL);
    UI_Menu_Item_Init(&UI_Baud_19200, "19200     ", &UI_Setting_Baud, NULL, NULL);
    UI_Menu_Item_Init(&UI_Baud_38400, "38400     ", &UI_Setting_Baud, NULL, NULL);
    UI_Menu_Item_Init(&UI_Baud_57600, "57600     ", &UI_Setting_Baud, NULL, NULL);
    UI_Menu_Item_Init(&UI_Baud_115200, "115200    ", &UI_Setting_Baud, NULL, NULL);
    
    // 初始化校验位子菜单
    UI_Menu_Item_Init(&UI_Parity_None, "None      ", &UI_Setting_Parity, NULL, NULL);
    UI_Menu_Item_Init(&UI_Parity_CRC, "CRC       ", &UI_Setting_Parity, NULL, NULL);
    UI_Menu_Item_Init(&UI_Parity_0x4B, "0x4B      ", &UI_Setting_Parity, NULL, NULL);
    
    // 初始化响应子菜单
    UI_Menu_Item_Init(&UI_Response_None, "None      ", &UI_Setting_Response, NULL, NULL);
    UI_Menu_Item_Init(&UI_Response_Done, "Done      ", &UI_Setting_Response, NULL, NULL);
    UI_Menu_Item_Init(&UI_Response_Repeat, "Repeat    ", &UI_Setting_Response, NULL, NULL);
    
    // 初始化方向子菜单
    UI_Menu_Item_Init(&UI_Dir_CW, "CW        ", &UI_Setting_Dir, NULL, NULL);
    UI_Menu_Item_Init(&UI_Dir_CCW, "CCW       ", &UI_Setting_Dir, NULL, NULL);
    
    // 初始化自动休眠子菜单
    UI_Menu_Item_Init(&UI_DispSleep_On, "On        ", &UI_Setting_DispSleep, NULL, NULL);
    UI_Menu_Item_Init(&UI_DispSleep_Off, "Off       ", &UI_Setting_DispSleep, NULL, NULL);
    
    // 初始化自动休眠时间子菜单
    UI_Menu_Item_Init(&UI_DispSleepTime_10s, "10s       ", &UI_Setting_DispSleepTime, NULL, NULL);
    UI_Menu_Item_Init(&UI_DispSleepTime_30s, "30s       ", &UI_Setting_DispSleepTime, NULL, NULL);
    UI_Menu_Item_Init(&UI_DispSleepTime_60s, "60s       ", &UI_Setting_DispSleepTime, NULL, NULL);

    // 初始化菜单显示
    UI_Menu_Display_Init(&UI_Menu, APP_OLED_LINE_NUM, (void *)UI_Show_String);
    UI_Menu.set_current(&UI_Menu, &UI_Setting);
}

/**
 * @brief 初始化OLED
 */
void APP_OLED_Init(void)
{
    OLED_Init(&oled);
    OLED_DisplayTurn(&oled, 1);
    OLED_Clear(&oled);

    // 初始化设置菜单
    UI_Setting_Menu_Init();
}

/**
 * @brief 处理OLED界面
 */
void APP_Process(void)
{
    // 根据当前OLED界面进行显示
    switch (APP_UI)
    {
        // 主界面显示电机状态
        case APP_UI_MAIN:
        {
            sprintf((char *)APP_UI_Buffer, "T_A: %d     ", Motor_GetTarget(&Motor_A));
            OLED_ShowString(&oled, 0, 0, APP_UI_Buffer, OLED_Word_Height, 1);
            sprintf((char *)APP_UI_Buffer, "S_A: %d     ", Motor_GetSpeed(&Motor_A));
            OLED_ShowString(&oled, 0, OLED_Word_Height, APP_UI_Buffer, OLED_Word_Height, 1);
            sprintf((char *)APP_UI_Buffer, "            ");
            OLED_ShowString(&oled, 0, OLED_Word_Height*2, APP_UI_Buffer, OLED_Word_Height, 1);
            sprintf((char *)APP_UI_Buffer, "T_B: %d     ", Motor_GetTarget(&Motor_B));
            OLED_ShowString(&oled, 0, OLED_Word_Height*3, APP_UI_Buffer, OLED_Word_Height, 1);
            sprintf((char *)APP_UI_Buffer, "S_B: %d     ", Motor_GetSpeed(&Motor_B));
            OLED_ShowString(&oled, 0, OLED_Word_Height*4, APP_UI_Buffer, OLED_Word_Height, 1);
        } break;
        // 设置界面显示设置菜单
        case APP_UI_SETTING:
        {
            // 检查刷新标志位
            if(APP_UI_Refresh_Flag == 0) return;
            OLED_Clear(&oled);
            APP_UI_Refresh_Flag = 0;
            
            UI_Menu.display(&UI_Menu);
        } break;
    }
    OLED_Refresh(&oled);
}
