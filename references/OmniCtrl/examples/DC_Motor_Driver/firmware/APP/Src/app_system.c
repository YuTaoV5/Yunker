/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-28 23:11
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "app_system.h"
#include "Flash.h"
#include "control_comm.h"

System_Status_t g_system_status;    // 系统状态

/**
 * @brief: 设置系统ID
 * @param id: 系统ID
 */
static inline void System_Set_ID(char id)
{
    if (g_system_status.setting_.id_ != id)
    {
        g_system_status.setting_.id_ = id;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统ID
 * @return char: 系统ID
 */
static inline char System_Get_ID(void)
{
    return g_system_status.setting_.id_;
}

/**
 * @brief: 设置系统串口
 * @param serial: 系统串口
 */
static inline void System_Set_Serial(System_Serial_t serial)
{
    if (g_system_status.setting_.serial_ != serial)
    {
        g_system_status.setting_.serial_ = serial;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统串口
 * @return System_Serial_t: 系统串口
 */
static inline System_Serial_t System_Get_Serial(void)
{
    return g_system_status.setting_.serial_;
}

/**
 * @brief: 设置系统波特率
 * @param baud: 系统波特率
 */
static inline void System_Set_Baud(System_Baud_t baud)
{
    if (g_system_status.setting_.baud_ != baud)
    {
        g_system_status.setting_.baud_ = baud;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统波特率
 * @return System_Baud_t: 系统波特率
 */
static inline System_Baud_t System_Get_Baud(void)
{
    return g_system_status.setting_.baud_;
}

/**
 * @brief: 设置系统校验位
 * @param parity: 系统校验位
 */
static inline void System_Set_Parity(System_Parity_t parity)
{
    if (g_system_status.setting_.parity_ != parity)
    {
        g_system_status.setting_.parity_ = parity;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统校验位
 * @return System_Parity_t: 系统校验位
 */
static inline System_Parity_t System_Get_Parity(void)
{
    return g_system_status.setting_.parity_;
}

/**
 * @brief: 设置系统响应
 * @param response: 系统响应
 */
static inline void System_Set_Response(System_Response_t response)
{
    if (g_system_status.setting_.response_ != response)
    {
        g_system_status.setting_.response_ = response;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统响应
 * @return System_Response_t: 系统响应
 */
static inline System_Response_t System_Get_Response(void)
{
    return g_system_status.setting_.response_;
}

/**
 * @brief: 设置系统方向
 * @param dir: 系统方向
 */
static inline void System_Set_Dir(System_Dir_t dir)
{
    if (g_system_status.setting_.dir_ != dir)
    {
        g_system_status.setting_.dir_ = dir;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统方向
 * @return System_Dir_t: 系统方向
 */
static inline System_Dir_t System_Get_Dir(void)
{
    return g_system_status.setting_.dir_;
}

/**
 * @brief: 设置系统显示自动休眠
 * @param display_auto_sleep: 系统显示自动休眠
 */
static inline void System_Set_Display_Auto_Sleep(System_Display_Auto_Sleep_t display_auto_sleep)
{
    if (g_system_status.setting_.display_auto_sleep_ != display_auto_sleep)
    {
        g_system_status.setting_.display_auto_sleep_ = display_auto_sleep;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统显示自动休眠
 * @return System_Display_Auto_Sleep_t: 系统显示自动休眠
 */
static inline System_Display_Auto_Sleep_t System_Get_Display_Auto_Sleep(void)
{
    return g_system_status.setting_.display_auto_sleep_;
}

/**
 * @brief: 设置系统自动休眠时间
 * @param auto_sleep_time: 系统自动休眠时间(ms)
 */
static inline void System_Set_Auto_Sleep_Time(unsigned long int auto_sleep_time)
{
    if (g_system_status.setting_.auto_sleep_time_ != auto_sleep_time)
    {
        g_system_status.setting_.auto_sleep_time_ = auto_sleep_time;
        // 设置需要保存
        g_system_status.set_need_save(1);
    }
}

/**
 * @brief: 获取系统自动休眠时间
 * @return unsigned long int: 系统自动休眠时间(ms)
 */
static inline unsigned long int System_Get_Auto_Sleep_Time(void)
{
    return g_system_status.setting_.auto_sleep_time_;
}

/**
 * @brief: 设置系统是否需要保存
 * @param need_save: 是否需要保存
 */
static inline void System_Set_Need_Save(unsigned char need_save)
{
    g_system_status.setting_.need_save_ = need_save;
}

/**
 * @brief: 获取系统是否需要保存
 * @return unsigned char: 是否需要保存
 */
static inline unsigned char System_Get_Need_Save(void)
{
    return g_system_status.setting_.need_save_;
}

/**
 * @brief: 更新系统状态
 */
static inline void System_Status_Update(void)
{
    // 更新系统参数
    if(g_system_status.get_need_save() == 0) return;
    uint32_t data_addrs[] = {(uint32_t)&g_system_status.setting_, (uint32_t)&graph};
    uint32_t data_lens[] = {sizeof(System_Setting_t), CONTROL_COMM_GRAPH_SIZE};
    Flash_Write(0x00, data_addrs, data_lens, 2);
    g_system_status.set_need_save(0);
}

/**
 * @brief: 重置系统状态
 */
static void System_Status_Reset(void)
{
    // 重置系统参数
    g_system_status.set_id(0);
    g_system_status.set_serial(System_Serial_RS485);
    g_system_status.set_baud(System_Baud_115200);
    g_system_status.set_parity(System_Parity_0x4B);
    g_system_status.set_response(System_Response_None);
    g_system_status.set_dir(System_Dir_CW);
    g_system_status.set_display_auto_sleep(System_Display_Auto_Sleep_Off);
    g_system_status.set_auto_sleep_time(1000);
    g_system_status.set_need_save(1);
}

/**
 * @brief: 初始化系统状态
 */
void System_Status_Init(void)
{
    // 初始化系统参数
    Flash_Read(0x00, (uint8_t *)&g_system_status.setting_, sizeof(System_Setting_t));
    g_system_status.setting_.need_save_ = 0;
    // 绑定系统设置方法
    g_system_status.set_id = System_Set_ID;
    g_system_status.set_serial = System_Set_Serial;
    g_system_status.set_baud = System_Set_Baud;
    g_system_status.set_parity = System_Set_Parity;
    g_system_status.set_response = System_Set_Response;
    g_system_status.set_dir = System_Set_Dir;
    g_system_status.set_display_auto_sleep = System_Set_Display_Auto_Sleep;
    g_system_status.set_auto_sleep_time = System_Set_Auto_Sleep_Time;
    g_system_status.set_need_save = System_Set_Need_Save;
    g_system_status.update = System_Status_Update;
    g_system_status.reset = System_Status_Reset;

    // 绑定系统获取方法
    g_system_status.get_id = System_Get_ID;
    g_system_status.get_serial = System_Get_Serial;
    g_system_status.get_baud = System_Get_Baud;
    g_system_status.get_parity = System_Get_Parity;
    g_system_status.get_response = System_Get_Response;
    g_system_status.get_dir = System_Get_Dir;
    g_system_status.get_display_auto_sleep = System_Get_Display_Auto_Sleep;
    g_system_status.get_auto_sleep_time = System_Get_Auto_Sleep_Time;
    g_system_status.get_need_save = System_Get_Need_Save;
}
