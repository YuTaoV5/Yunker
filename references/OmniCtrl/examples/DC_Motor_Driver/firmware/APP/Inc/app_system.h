/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-28 23:11
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __APP_SYSTEM_H
#define __APP_SYSTEM_H


/*-----------------------------------枚举声明-----------------------------------*/
typedef enum
{
    System_Serial_UART = 0,
    System_Serial_RS485,
}System_Serial_t;

typedef enum
{
    System_Baud_9600 = 0,
    System_Baud_19200,
    System_Baud_38400,
    System_Baud_57600,
    System_Baud_115200,
}System_Baud_t;

typedef enum
{
    System_Parity_None = 0,
    System_Parity_CRC,
    System_Parity_0x4B,
}System_Parity_t;

typedef enum
{
    // 需要完善响应形式
    System_Response_None = 0,   // 无响应
    System_Response_Done,       // 正常接收内容
    System_Response_Repeat,     // 重复接收内容
}System_Response_t;

typedef enum
{
    System_Dir_CW = 0,      // 顺时针转
    System_Dir_CCW,         // 逆时针转
}System_Dir_t;

typedef enum
{
    System_Display_Auto_Sleep_On = 0,
    System_Display_Auto_Sleep_Off,
}System_Display_Auto_Sleep_t;


/*----------------------------------结构体声明----------------------------------*/
/**
 * @brief: 系统设置结构体
 * @param id_: 系统ID
 * @param serial_: 串口类型
 * @param baud_: 波特率
 * @param parity_: 校验位
 * @param response_: 响应形式
 * @param dir_: 电机方向
 * @param display_auto_sleep_: 显示自动休眠
 * @param auto_sleep_time_: 自动休眠时间
 */
typedef struct
{
    unsigned char id_;
    System_Serial_t serial_;
    System_Baud_t baud_;
    System_Parity_t parity_;
    System_Response_t response_;
    System_Dir_t dir_;
    System_Display_Auto_Sleep_t display_auto_sleep_;
    unsigned long int auto_sleep_time_;
    unsigned char need_save_;   // 0: 不需要保存，1: 需要保存
}System_Setting_t;

/**
 * @brief: 系统状态结构体
 * @param setting_: 系统设置
 * @note: 这里的所以方法直接操作全局变量g_system_status，因此不传入self.
 *        本系统状态类全局仅可以有一个实例，且应符合上述命名。
 */
typedef struct
{
    System_Setting_t setting_;

    // 系统设置更改方法
    void (*set_id)(char id);
    void (*set_serial)(System_Serial_t serial);
    void (*set_baud)(System_Baud_t baud);
    void (*set_parity)(System_Parity_t parity);
    void (*set_response)(System_Response_t response);
    void (*set_dir)(System_Dir_t dir);
    void (*set_display_auto_sleep)(System_Display_Auto_Sleep_t display_auto_sleep);
    void (*set_auto_sleep_time)(unsigned long int auto_sleep_time);
    void (*set_need_save)(unsigned char need_save);
    void (*update)(void);   // 更新系统状态
    void (*reset)(void);    // 重置系统状态

    // 系统设置获取方法
    char (*get_id)(void);
    System_Serial_t (*get_serial)(void);
    System_Baud_t (*get_baud)(void);
    System_Parity_t (*get_parity)(void);
    System_Response_t (*get_response)(void);
    System_Dir_t (*get_dir)(void);
    System_Display_Auto_Sleep_t (*get_display_auto_sleep)(void);
    unsigned long int (*get_auto_sleep_time)(void);
    unsigned char (*get_need_save)(void);
}System_Status_t;

/*-----------------------------------变量声明-----------------------------------*/
extern System_Status_t g_system_status;

/*-----------------------------------函数声明-----------------------------------*/
void System_Status_Init(void);

#endif  // __APP_SYSTEM_H
