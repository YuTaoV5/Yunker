/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-07 14:47
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "app_comm.h"
#include "app_ctrl.h"
#include "app_system.h"
#include "comm.h"
#include <stdint.h>

// 逆序CRC表
unsigned char aucCRCHi[]={
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40
};

unsigned char aucCRCLo[]={
    0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7,
    0x05, 0xC5, 0xC4, 0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E,
    0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09, 0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9,
    0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD, 0x1D, 0x1C, 0xDC,
    0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
    0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32,
    0x36, 0xF6, 0xF7, 0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D,
    0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A, 0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38,
    0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE, 0x2E, 0x2F, 0xEF,
    0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
    0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1,
    0x63, 0xA3, 0xA2, 0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4,
    0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F, 0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB,
    0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB, 0x7B, 0x7A, 0xBA,
    0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
    0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0,
    0x50, 0x90, 0x91, 0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97,
    0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C, 0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E,
    0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88, 0x48, 0x49, 0x89,
    0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
    0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83,
    0x41, 0x81, 0x80, 0x40
};

#define COMM_BUF_SIZE 40    // 通信缓存大小
#define COMM_HOSTIF_CTRL_TICK_DIV 1U

uint8_t comm_hostif_en = 0;     // 向上位机发送使能(0: 不发送, 1: 发送)
uint8_t comm_hostif_motor_en = 1;  // 发送电机状态(0: 不发送, 1: 发送)
static uint8_t comm_rx_buf[COMM_BUF_SIZE];   // 通信缓存
static uint8_t comm_tx_buf[COMM_BUF_SIZE];
static volatile uint8_t comm_hostif_tx_pending = 0;
static uint8_t comm_hostif_tick_count = 0;
int16_t tmp_motorA_speed = 0;       // 电机A目标速度(用于同步运行)
int16_t tmp_motorB_speed = 0;       // 电机B目标速度(用于同步运行)
uint8_t tmp_speed_enable = 0;       // 标志临时数据有效(0: 无效, 1: 有效)

static inline void APP_Comm_ResetHostifTxState(void)
{
    comm_hostif_tx_pending = 0;
    comm_hostif_tick_count = 0;
}

/**
 * @brief: 计算Modbus校验位
 * @param: data 数据指针
 * @param: len 数据长度
 * @return: uint16_t 校验位
 * @note: 根据Modbus校验位算法计算校验位
 */
static uint16_t APP_Modbus_CRC(uint8_t *data, uint8_t len)
{
    unsigned char CRCHi = 0xFF;
    unsigned char CRCLo = 0xFF;
    unsigned char iIndex = 0;
    
    for (uint8_t i = 0; i < len; i++)
    {
        // 查表并更新 CRC 值
        iIndex = CRCHi ^ data[i];
        CRCHi = CRCLo ^ aucCRCHi[iIndex];
        CRCLo = aucCRCLo[iIndex];
    }
    
    return (unsigned int)( CRCHi << 8 | CRCLo);// CRC校验返回值 
}

/**
 * @brief: 发送Modbus校验位
 * @param: frame_size 数据帧长度
 * @return: None
 * @note: 根据校验位类型发送校验位
 */
static inline void APP_Modbus_Send_Parity(uint8_t frame_size)
{
    uint16_t crc;
    switch(g_system_status.setting_.parity_)
    {
        case System_Parity_None:
            Comm_SendBytes(&comm_ctrl, comm_tx_buf, frame_size);
            break;
        case System_Parity_0x4B:
            comm_tx_buf[frame_size] = 0x4B;
            Comm_SendBytes(&comm_ctrl, comm_tx_buf, frame_size+1);
            break;
        case System_Parity_CRC:
            crc = APP_Modbus_CRC(comm_tx_buf, frame_size);
            comm_tx_buf[frame_size] = crc;
            comm_tx_buf[frame_size+1] = crc>>8;
            Comm_SendBytes(&comm_ctrl, comm_tx_buf, frame_size+2);
            break;
        default:
            break;
    }
}

/**
 * @brief: Modbus指令0x03解析
 * @param: rx_buf 接收缓存
 * @return: None
 * @note: 查询寄存器参数
 */
static void APP_Modbus_0x03(void)
{
    /* 查询寄存器参数 */
    // 检查非广播地址
    if(comm_rx_buf[0] == 255) return;

    switch (comm_rx_buf[2])
    {
        case 0x01:
            /* 查询电机状态 */
                        comm_tx_buf[0] = g_system_status.setting_.id_;    // 板ID
            comm_tx_buf[1] = 0x03;             // 功能码
            comm_tx_buf[2] = 0x01;             // 电机状态
            comm_tx_buf[3] = Motor_GetSpeed(&Motor_A)>>8;
            comm_tx_buf[4] = Motor_GetSpeed(&Motor_A);
            comm_tx_buf[5] = Motor_GetSpeed(&Motor_B)>>8;
            comm_tx_buf[6] = Motor_GetSpeed(&Motor_B);
            APP_Modbus_Send_Parity(7);
            break;
        case 0x02:
            /* 查询目标速度 */
            comm_tx_buf[0] = g_system_status.setting_.id_;    // 板ID
            comm_tx_buf[1] = 0x03;             // 功能码
            comm_tx_buf[2] = 0x02;             // 目标速度
            comm_tx_buf[3] = Motor_GetTarget(&Motor_A)>>8;
            comm_tx_buf[4] = Motor_GetTarget(&Motor_A);
            comm_tx_buf[5] = Motor_GetTarget(&Motor_B)>>8;
            comm_tx_buf[6] = Motor_GetTarget(&Motor_B);
            APP_Modbus_Send_Parity(7);
            break;
        case 0x10:
            /* 查询系统参数块: serial baud parity response dir display_sleep sleep_hi sleep_lo hostif_en hostif_motor_en */
            {
                uint32_t t = g_system_status.setting_.auto_sleep_time_;
                comm_tx_buf[0]  = g_system_status.setting_.id_;
                comm_tx_buf[1]  = 0x03;
                comm_tx_buf[2]  = 0x10;
                comm_tx_buf[3]  = 0; comm_tx_buf[4]  = (uint8_t)g_system_status.setting_.serial_;
                comm_tx_buf[5]  = 0; comm_tx_buf[6]  = (uint8_t)g_system_status.setting_.baud_;
                comm_tx_buf[7]  = 0; comm_tx_buf[8]  = (uint8_t)g_system_status.setting_.parity_;
                comm_tx_buf[9]  = 0; comm_tx_buf[10] = (uint8_t)g_system_status.setting_.response_;
                comm_tx_buf[11] = 0; comm_tx_buf[12] = (uint8_t)g_system_status.setting_.dir_;
                comm_tx_buf[13] = 0; comm_tx_buf[14] = (uint8_t)g_system_status.setting_.display_auto_sleep_;
                comm_tx_buf[15] = (uint8_t)((t >> 24) & 0xFF);
                comm_tx_buf[16] = (uint8_t)((t >> 16) & 0xFF);
                comm_tx_buf[17] = (uint8_t)((t >>  8) & 0xFF);
                comm_tx_buf[18] = (uint8_t)( t        & 0xFF);
                comm_tx_buf[19] = 0; comm_tx_buf[20] = comm_hostif_en;
                comm_tx_buf[21] = 0; comm_tx_buf[22] = comm_hostif_motor_en;
                APP_Modbus_Send_Parity(23);
            }
            break;
        default:
            break;
    }
}

/**
 * @brief: Modbus指令0x06解析
 * @param: rx_buf 接收缓存
 * @return: None
 * @note: 设置单个寄存器参数
 */
static void APP_Modbus_0x06(void)
{
    /* 设置单个寄存器参数 */
    switch (comm_rx_buf[2])
    {
        case 0x01:
            /* 无法设置电机实际速度 */
            break;
        case 0x02:
            /* 设置电机目标速度 */
            Motor_SetTarget(&Motor_A, (int16_t)((comm_rx_buf[3]<<8)|comm_rx_buf[4]));
            Motor_SetTarget(&Motor_B, (int16_t)((comm_rx_buf[5]<<8)|comm_rx_buf[6]));
            break;
        case 0x10:
            /* 写入系统参数块 */
            g_system_status.set_serial(            (System_Serial_t)          comm_rx_buf[4]);
            g_system_status.set_baud(              (System_Baud_t)            comm_rx_buf[6]);
            g_system_status.set_parity(            (System_Parity_t)          comm_rx_buf[8]);
            g_system_status.set_response(          (System_Response_t)        comm_rx_buf[10]);
            g_system_status.set_dir(               (System_Dir_t)             comm_rx_buf[12]);
            g_system_status.set_display_auto_sleep((System_Display_Auto_Sleep_t)comm_rx_buf[14]);
            g_system_status.set_auto_sleep_time(
                ((unsigned long int)comm_rx_buf[15] << 24) |
                ((unsigned long int)comm_rx_buf[16] << 16) |
                ((unsigned long int)comm_rx_buf[17] <<  8) |
                 (unsigned long int)comm_rx_buf[18]);
            comm_hostif_en       = comm_rx_buf[20];
            comm_hostif_motor_en = comm_rx_buf[22];
            if(!comm_hostif_en || !comm_hostif_motor_en)
            {
                APP_Comm_ResetHostifTxState();
            }
            break;
        case 0x41:
            /* 设置同步目标速度 */
            tmp_motorA_speed = (comm_rx_buf[3]<<8)|comm_rx_buf[4];
            tmp_motorB_speed = (comm_rx_buf[5]<<8)|comm_rx_buf[6];
            tmp_speed_enable = 1;
            break;
        case 0x42:
            /* 确认同步目标速度 */
            if(tmp_speed_enable)
            {
                Motor_SetTarget(&Motor_A, tmp_motorA_speed);
                Motor_SetTarget(&Motor_B, tmp_motorB_speed);
                tmp_speed_enable = 0;
            }
            break;
        default:
            break;
    }
    if(g_system_status.get_response() != System_Response_Done)
    {
        // 回应设置指令
    }
}

/**
 * @brief: Modbus指令解析
 * @param: None
 * @return: None
 * @note: 解析Modbus指令，根据指令进行相应的处理
 */
static void APP_Comm_Modbus(void)
{
    // 检查是否为当前板ID或广播ID
    if(comm_rx_buf[0] != g_system_status.setting_.id_ && comm_rx_buf[0]!= 255) return;
    
    // 校验位检查
    uint16_t crc_compute, crc_recv;
    switch(g_system_status.get_parity())
    {
        case System_Parity_None:
            break;
        case System_Parity_0x4B:
            if(comm_rx_buf[comm_ctrl.get_frame_size(&comm_ctrl)-1] != 0x4B) return;
            break;
        case System_Parity_CRC:
            crc_compute = APP_Modbus_CRC(comm_rx_buf, comm_ctrl.get_frame_size(&comm_ctrl)-2);
            crc_recv = (comm_rx_buf[comm_ctrl.get_frame_size(&comm_ctrl)-1]<<8)|comm_rx_buf[comm_ctrl.get_frame_size(&comm_ctrl)-2];
            if(crc_compute != crc_recv) return;
            break;
        default:
            break;
    }

    switch (comm_rx_buf[1])
    {
        case 0x03:
            APP_Modbus_0x03();
            break;
        case 0x06:
            APP_Modbus_0x06();
            break;
        default:
            break;
    }
}

/**
 * @brief: 解析通信协议
 * @param: rx_buf 接收缓存
 * @return: None
 * @note: 解析通信协议，根据协议进行相应的处理
 */
static void APP_Comm_Parse(uint8_t *rx_buf)
{
    // 若为重复响应，则直接发送
    if(g_system_status.get_response() == System_Response_Repeat)
    {
        Comm_SendBytes(&comm_ctrl, rx_buf, comm_ctrl.get_frame_size(&comm_ctrl));
    }
    // 解析Modbus指令
    APP_Comm_Modbus();
}

/**
 * @brief: 接收回调函数
 * @param: None
 * @return: None
 * @note: 当UART接收到数据时调用，用于处理接收到的数据
 */
static void APP_Comm_RxCallback(void)
{
    comm_ctrl.get_rx_buffer(&comm_ctrl, comm_rx_buf);
    APP_Comm_Parse(comm_rx_buf);
}

/**
 * @brief 上位机接口
 * @param None
 * @return None
 */
static void APP_Comm_Hostif(void)
{
    if(!comm_hostif_tx_pending) return;

    comm_hostif_tx_pending = 0;

    // 发送电机状态
    comm_tx_buf[0] = g_system_status.setting_.id_;    // 板ID
    comm_tx_buf[1] = 0x11;             // 电机状态
    comm_tx_buf[2] = Motor_GetSpeed(&Motor_A)>>8;
    comm_tx_buf[3] = Motor_GetSpeed(&Motor_A);
    comm_tx_buf[4] = Motor_GetSpeed(&Motor_B)>>8;
    comm_tx_buf[5] = Motor_GetSpeed(&Motor_B);
    APP_Modbus_Send_Parity(6);
}

/**
 * @brief: 初始化通信模块
 * @param: None
 * @return: None
 * @note: 初始化UART接收句柄，配置接收回调函数和获取接收缓冲区数据函数
 */
void APP_Comm_Init(void)
{
    // 初始化通信模块
    uint8_t uartx = 0;
    uint32_t baud = 0;

    // 获取UART串口号及波特率
    switch (g_system_status.get_serial())
    {
    case System_Serial_UART:
        uartx = 0;
        break;
    case System_Serial_RS485:
        uartx = 1;
        break;
    default:
        break;
    }
    switch (g_system_status.get_baud())
    {
        case System_Baud_9600:  baud = 9600;    break;
        case System_Baud_19200: baud = 19200;   break;
        case System_Baud_38400: baud = 38400;   break;
        case System_Baud_57600: baud = 57600;   break;
        case System_Baud_115200:baud = 115200;  break;
        default: baud = 115200; break;
    }
    // 初始化UART接收句柄
    Comm_Init(&comm_ctrl, uartx, baud, APP_Comm_RxCallback);
    APP_Comm_ResetHostifTxState();
}

void APP_Comm_OnCtrlTick(void)
{
    if(!comm_hostif_en || !comm_hostif_motor_en)
    {
        APP_Comm_ResetHostifTxState();
        return;
    }

    comm_hostif_tick_count++;
    if(comm_hostif_tick_count < COMM_HOSTIF_CTRL_TICK_DIV)
    {
        return;
    }

    comm_hostif_tick_count = 0;
    comm_hostif_tx_pending = 1;
}

/**
 * @brief 通信处理函数
 * @param None
 * @return None
 */
void APP_Comm_Process(void)
{
    APP_Comm_Hostif();
}
