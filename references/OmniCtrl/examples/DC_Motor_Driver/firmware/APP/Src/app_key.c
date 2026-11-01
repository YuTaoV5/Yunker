/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-26 07:07
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "app_key.h"
#include "key.h"
#include "app_oled.h"
#include "control_comm.h"

static Key_Handle_t key1_handle;       // 按键1句柄
static Key_Handle_t key2_handle;       // 按键2句柄

/**
 * @brief 按键初始化
 * @param void
 * @return void
 */
void APP_Key_Init(void)
{
    Key_Init(&key1_handle, &key1_config);
    Key_Init(&key2_handle, &key2_config);
}

/**
 * @brief 按键处理函数
 * @param void
 * @return void
 */
void APP_Key_Process(void)
{
    Key_Scan(&key1_handle);
    Key_Scan(&key2_handle);

    if(Key_GetEvent(&key1_handle) == KEY_EVENT_PRESSED)
    {
        if(APP_UI == APP_UI_MAIN)
        {
            // 处理主界面按键
        }
        else if(APP_UI == APP_UI_SETTING)
        {
            UI_Menu.switch_next(&UI_Menu);
            APP_UI_Refresh_Flag = 1;    // 刷新OLED界面
        }
    }
    else if (Key_GetEvent(&key1_handle) == KEY_EVENT_LONG_PRESSED)
    {
        // 长按按键1, 切换OLED界面(设置 -> 主界面)   
        if(APP_UI == APP_UI_SETTING)
        {
            APP_UI = APP_UI_MAIN;
            APP_UI_Refresh_Flag = 1;    // 刷新OLED界面
        }
    }
    else if (Key_GetEvent(&key2_handle) == KEY_EVENT_PRESSED)
    {
        // 切换OLED界面(主界面 -> 设置)
        if(APP_UI == APP_UI_MAIN)
        {
            // 切换到设置界面
            APP_UI = APP_UI_SETTING;
            UI_Menu.set_current(&UI_Menu, &UI_Setting);
            APP_UI_Refresh_Flag = 1;
        }
        // 切换OLED界面(设置 -> 主界面)(处于设置界面, 点击退出设置项)
        else if(APP_UI == APP_UI_SETTING && UI_Menu.selected_child_ == &UI_Setting_Exit)
        {
            // 切换到主界面
            APP_UI = APP_UI_MAIN;
            APP_UI_Refresh_Flag = 1;
        }
        // 切换设置选项(处于设置界面, 点击其他设置项)
        else if(APP_UI == APP_UI_SETTING)
        {
            // 通过是否为最后一个子菜单, 决定切换到子菜单或父菜单
            if(UI_Menu.selected_child_->first_child_ != NULL)
            {
                UI_Menu.switch_child(&UI_Menu);
            }
            else
            {
                UI_Menu.switch_parent(&UI_Menu);
            }
            APP_UI_Refresh_Flag = 1;
        }
        // 未来考虑处理其他界面下的按键确认
    }
}

/**
 * @brief 进入引导模式
 * @param void
 * @return void
 */
void APP_Enter_Boot(void)
{
    Key_Scan(&key1_handle);
    Key_Scan(&key2_handle);

    // 同时按下按按键1和按键2, 进入引导模式
    if(key1_handle.State_ == KEY_STATE_PRESSED &&
        key2_handle.State_ == KEY_STATE_PRESSED)
    {
        // 进入Boot模式
        control_into_bootloader = 1;
    }
    else
        control_into_bootloader = 0;
}
