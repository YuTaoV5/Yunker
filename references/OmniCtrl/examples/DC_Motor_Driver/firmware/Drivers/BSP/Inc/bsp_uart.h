/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-23 22:16
* @version: v1.0.0
* @description: UART 板级支持
********************************************************************************/
#ifndef __BSP_UART_H
#define __BSP_UART_H

#include "bsp_common.h"

/*-----------------------------------常量定义-----------------------------------*/
#define BSP_UART_BUFFER_SIZE 128


/*-----------------------------------枚举定义-----------------------------------*/
/**
 * @brief UART实例枚举
 */
typedef enum
{
    BSP_UART1 = 0,
    BSP_UART2,
    BSP_UART_NUM,
}BSP_UARTx_t;


/*-----------------------------------类型定义-----------------------------------*/
// UART接收实例结构体前向声明
typedef struct BSP_UART_RxHandle_t BSP_UART_RxHandle_t;

/**
 * @brief UART接收回调函数类型
 * @param self 接收实例指针
 * @param data 接收数据指针
 * @param size 接收数据大小
 */
typedef void BSP_UART_RxCallback_t(BSP_UART_RxHandle_t *self);

/**
 * @brief UART接收实例结构体
 */
struct BSP_UART_RxHandle_t{
    BSP_UARTx_t uartx_;                         // UART实例
    uint32_t baudrate_;                         // 波特率
    uint8_t rx_buffer_[BSP_UART_BUFFER_SIZE];   // 接收缓冲区
    volatile uint8_t frame_ready_;              // 接收帧是否就绪
    volatile uint16_t frame_size_;              // 接收帧大小
    BSP_UART_RxCallback_t *rx_callback_;        // 接收回调函数
    void (*Start_Rx)(void *self);               // 启动接收
    void (*Stop_Rx)(void *self);                // 停止接收
};


/*-----------------------------------函数声明-----------------------------------*/
BSP_UART_RxHandle_t *BSP_UART_GetRxHandle(BSP_UARTx_t uartx);
void BSP_UART_Init(BSP_UARTx_t uartx, uint32_t baudrate);
void BSP_UART_Transmit(BSP_UARTx_t uartx, uint8_t *data, uint16_t size);
void BSP_UART_RxHandle_Init(void *handle, BSP_UARTx_t uartx, uint32_t baudrate,
                            BSP_UART_RxCallback_t *rx_callback);

#endif //__BSP_UART_H
