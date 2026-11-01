/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-29 22:48
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "comm.h"
#include "bsp_interface.h"
#include <string.h>

#define G_COMM_NUM_MAX 4        // 最大通信模块数量

Comm_t *g_comm[G_COMM_NUM_MAX] = {NULL};    // 通信模块实例数组
uint8_t comm_num = 0;    // 通信模块实例数量
Comm_t comm_ctrl;       // 控制通信模块实例
Comm_t comm_boot;       // 引导通信模块实例

/**
 * @brief: 接收处理函数
 * @param: self 接收句柄指针
 * @return: 无
 * @note: 该函数作为BSP层与APP层的桥梁，用于处理接收到的数据
 */
static void Rx_Handle(BSP_UART_RxHandle_t *self)
{
    for (int i = 0; i < comm_num; i++)
    {
        if (g_comm[i] != NULL && g_comm[i]->rx_callback_ != NULL 
            && g_comm[i]->rx_handle_ == self)
        {
            g_comm[i]->rx_callback_();
        }
    }
}

/**
 * @brief: 获取接收缓冲区数据
 * @param: buffer 接收数据存储缓冲区指针
 * @return: 无
 * @note: 若接收数据后需要进行处理，应在此函数中实现
 *        确保传入的缓冲区大小足够存储接收数据
 */
static void Comm_GetRxBuffer(Comm_t *self, uint8_t *buffer)
{
    memcpy(buffer, self->rx_handle_->rx_buffer_, self->rx_handle_->frame_size_);
}

/**
 * @brief: 获取接收数据长度
 * @param: None
 * @return: 接收数据长度
 * @note: 无
 */
static uint16_t Comm_GetFrameSize(Comm_t *self)
{
    return self->rx_handle_->frame_size_;
}

/**
 * @brief: 初始化通信模块
 * @param: rx_callback 接收回调函数指针
 * @return: 无
 * @note: 初始化UART接收句柄，配置接收回调函数和获取接收缓冲区数据函数
 */
void Comm_Init(Comm_t *self, uint8_t uartx, uint32_t baudrate, void *rx_callback)
{
    // 1.参数检查
    if (uartx >= BSP_UART_NUM)
    {
        assert(0 && "comm_init: invalid uartx");
    }

    // 2.检查是否重复注册
    for (int i = 0; i < comm_num; i++)
    {
        if (g_comm[i] == self)
        {
            assert(0 && "comm_init: duplicate registration");
        }
    }
    
    // 3.检查是否超出最大通信模块数量
    if (comm_num >= G_COMM_NUM_MAX)
    {
        assert(0 && "comm_num overflow");
    }

    // 4.初始化通信模块实例
    self->rx_handle_ = BSP_UART_GetRxHandle(uartx);
    self->rx_callback_ = rx_callback;
    self->get_rx_buffer = Comm_GetRxBuffer;
    self->get_frame_size = Comm_GetFrameSize;
    BSP_UART_RxHandle_Init(self->rx_handle_, uartx, baudrate, Rx_Handle);

    // 4.注册通信模块实例
    g_comm[comm_num++] = self;
}

void Comm_DeInit(Comm_t *self)
{
    // 1.检查是否注册
    for (int i = 0; i < comm_num; i++)
    {
        if (g_comm[i] == self)
        {
            // 2.注销通信模块实例
            g_comm[i] = NULL;
            // 3. 移动数组中后续元素到当前位置
            for (int j = i; j < comm_num - 1; j++)
            {
                g_comm[j] = g_comm[j + 1];
            }
            g_comm[comm_num - 1] = NULL;
            comm_num--;
            break;
        }
    }
    assert(0 && "comm_deinit: not registered");
}

/**
 * @brief: 发送字节数据
 * @param: bytes 待发送字节数据指针
 * @param: size 待发送字节数据长度
 * @return: 无
 * @note: 无
 */
void Comm_SendBytes(Comm_t *self, uint8_t *bytes, uint16_t size)
{
    BSP_UART_Transmit(self->rx_handle_->uartx_, bytes, size);
}
