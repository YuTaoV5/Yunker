/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-06 15:02
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "app_main.h"
#include "app_oled.h"
#include "app_key.h"
#include "app_ctrl.h"
#include "app_comm.h"
#include "app_system.h"
#include "log.h"
#include "SysTimer.h"

char app_log_buf[30];

void APP_Main(void)
{
    // 系统初始化
    Log_Init();     // 初始化日志模块
    strcpy(app_log_buf, "Start Init!");     // 打印初始化信息
    Log_Info((uint8_t *)app_log_buf, strlen(app_log_buf));

    System_Status_Init();   // 初始化系统状态
    APP_OLED_Init();        // 初始化OLED
    APP_Key_Init();         // 初始化按键
    APP_Comm_Init();        // 初始化通信模块
    SysTimer_Init();        // 初始化系统定时器
    APP_Enter_Boot();       // 检查是否进入Boot模式
    APP_Ctrl_Init();        // 控制器初始化
    
    SysTimer_RegisterCallback(&APP_Ctrl_Process);
    
    strcpy(app_log_buf, "Init OK!");
    Log_Info((uint8_t *)app_log_buf, strlen(app_log_buf));
    while(1)
    {
        APP_Key_Process();
        APP_Comm_Process();
        APP_Process();
        g_system_status.update();
    }
}
