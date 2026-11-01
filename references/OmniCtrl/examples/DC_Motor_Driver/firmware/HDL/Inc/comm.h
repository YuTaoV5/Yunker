/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-29 22:48
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __COMM_H
#define __COMM_H

#include "bsp_common.h"
#include "bsp_uart.h"

/**
 * @brief: 通信模块结构体
 * @param: rx_handle_ UART接收句柄
 * @param: use_uartx_ 使用的UART实例
 * @param: rx_callback_ 接收回调函数指针
 * @param: get_rx_buffer 获取接收缓冲区数据函数指针
 * @return: 无
 * @note: 该结构体用于存储通信模块的配置和状态信息
 */
typedef struct Comm_t
{
    BSP_UART_RxHandle_t *rx_handle_;
    void (*rx_callback_)(void);
    void (*get_rx_buffer)(struct Comm_t *self, uint8_t *buffer);
    uint16_t (*get_frame_size)(struct Comm_t *self);
}Comm_t;


/*-----------------------------------变量声明-----------------------------------*/
extern Comm_t comm_ctrl;    // 控制通信模块实例
extern Comm_t comm_boot;    // 引导通信模块实例


/*-----------------------------------函数声明-----------------------------------*/
void Comm_Init(Comm_t *self, uint8_t use_uartx, uint32_t baudrate, void *rx_callback);
void Comm_Deinit(Comm_t *self);
void Comm_SendBytes(Comm_t *self, uint8_t *bytes, uint16_t size);

#endif // __COMM_H