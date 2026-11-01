/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-23 22:16
* @version: v1.0.0
* @description: UART 板级支持
********************************************************************************/
#include "bsp_uart.h"
#include "bsp_gpio.h"
#include "bsp_interface.h"
#include "usart.h"
#include "dma.h"
#include "gpio.h"
#include <string.h>

BSP_UART_RxHandle_t g_uart_rx_handle[BSP_UART_NUM] = {NULL};


/**
 * @brief 获取UART句柄
 * @param uartx UART实例枚举
 * @return UART_HandleTypeDef* UART句柄指针
 */
static inline UART_HandleTypeDef *BSP_UART_GetHandle(BSP_UARTx_t uartx)
{
// 建立端口映射表
    static const UART_HandleTypeDef *port_table[] = {
            [BSP_UART1] = &huart1,    // 枚举值0 → UART1
            [BSP_UART2] = &huart2,    // 枚举值1 → UART2
            // 扩展端口时在此添加(如[BSP_UART3] = &huart3)
    };

    // 检查端口枚举值是否在有效范围内
    if (uartx < sizeof(port_table) / sizeof(port_table[0])) {
        return (UART_HandleTypeDef *)port_table[uartx];
    }
    assert(0);
    return NULL;
}

/**
 * @brief 获取UART实例枚举从句柄
 * @param huart UART句柄指针
 * @return BSP_UARTx_t UART实例枚举
 */
BSP_UARTx_t BSP_UART_FromHandle(UART_HandleTypeDef *huart)
{
    if (huart == &huart1) return BSP_UART1;
    else if (huart == &huart2) return BSP_UART2;
    else assert(0);
}

/**
 * @brief 获取UART接收句柄
 * @param uartx UART实例枚举
 * @return BSP_UART_RxHandle_t* UART接收句柄指针
 */
BSP_UART_RxHandle_t *BSP_UART_GetRxHandle(BSP_UARTx_t uartx)
{
    if(uartx < BSP_UART_NUM)
    {
        return &g_uart_rx_handle[uartx];
    }
    assert(0);
}

/**
 * @brief 初始化UART
 * @param None
 * @return None
 */
void BSP_UART_Init(BSP_UARTx_t uartx, uint32_t baudrate)
{
    // DMA初始化
    static uint8_t dma_started = 0;
    if(dma_started == 0)
    {
        MX_DMA_Init();
        dma_started = 1;
    }

    // UART初始化
    UART_HandleTypeDef *huart = BSP_UART_GetHandle(uartx);
    switch (uartx)
    {
    case BSP_UART1:
        huart->Instance = USART1;
        break;
    case BSP_UART2:
        huart->Instance = USART2;
        break;
    default:
        break;
    }
    huart->Init.BaudRate = baudrate;
    huart->Init.WordLength = UART_WORDLENGTH_8B;
    huart->Init.StopBits = UART_STOPBITS_1;
    huart->Init.Parity = UART_PARITY_NONE;
    huart->Init.Mode = UART_MODE_TX_RX;
    huart->Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart->Init.OverSampling = UART_OVERSAMPLING_16;
    huart->Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    huart->Init.ClockPrescaler = UART_PRESCALER_DIV1;
    huart->AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(huart) != HAL_OK)
    {
        Error_Handler();
    }
    if (HAL_UARTEx_SetTxFifoThreshold(huart, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
    {
        Error_Handler();
    }
    if (HAL_UARTEx_SetRxFifoThreshold(huart, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
    {
        Error_Handler();
    }
    if (HAL_UARTEx_DisableFifoMode(huart) != HAL_OK)
    {
        Error_Handler();
    }
}

/**
 * @brief 发送数据
 * @param uartx UART实例枚举
 * @param data 数据指针
 * @param size 数据大小
 * @return None
 */
void BSP_UART_Transmit(BSP_UARTx_t uartx, uint8_t *data, uint16_t size)
{
    if (uartx == Comm_UART_UARTx)
    {
        HAL_UART_Transmit(BSP_UART_GetHandle(uartx), data, size, 0xFFFF);
    }
    else if (uartx == Comm_485_UARTx)
    {
        //切换发送模式
        BSP_GPIO_SetPin(Comm_485_GPIO_PORT, Comm_485_GPIO_PIN);
        //发送数据
        HAL_UART_Transmit(BSP_UART_GetHandle(uartx), data, size, 0xFFFF);
        // HAL_Delay(100);
        //切换接收模式
        BSP_GPIO_ResetPin(Comm_485_GPIO_PORT, Comm_485_GPIO_PIN);
    }
}

/**
 * @brief 停止UART接收
 * @param self UART接收句柄指针
 * @return None
 */
static void BSP_UART_RxHandle_Stop_Rx(void *self)
{
    BSP_UART_RxHandle_t *rx_handle = (BSP_UART_RxHandle_t *)self;
    HAL_UART_Abort(BSP_UART_GetHandle(rx_handle->uartx_));
}

/**
 * @brief 启动UART接收
 * @param self UART接收句柄指针
 * @return None
 */
static void BSP_UART_RxHandle_Start_Rx(void *self)
{
    BSP_UART_RxHandle_t *rx_handle = (BSP_UART_RxHandle_t *)self;
    if(rx_handle == NULL) return;

    UART_HandleTypeDef *huart = BSP_UART_GetHandle(rx_handle->uartx_);
    if(huart == NULL) return;

    // 停止当前接收
    HAL_UART_Abort(huart);

    // 重置接收状态
    rx_handle->frame_ready_ = 0;
    rx_handle->frame_size_ = 0;
    memset(rx_handle->rx_buffer_, 0, BSP_UART_BUFFER_SIZE);

    // 启动DMA接收
    if (HAL_UARTEx_ReceiveToIdle_DMA(huart, rx_handle->rx_buffer_, BSP_UART_BUFFER_SIZE) == HAL_OK)
    {
        // 清除标志位
        __HAL_UART_CLEAR_FLAG(huart, UART_CLEAR_IDLEF);
        // 开启IDLE中断
        __HAL_UART_ENABLE_IT(huart, UART_IT_IDLE);
    }
}

/**
 * @brief 初始化UART接收句柄
 * @param handle UART接收句柄指针
 * @param uartx UART实例枚举
 * @param rx_callback 接收回调函数指针
 * @return None
 */
void BSP_UART_RxHandle_Init(void *handle, BSP_UARTx_t uartx, uint32_t baudrate,
                            BSP_UART_RxCallback_t *rx_callback)
{
    if (g_uart_rx_handle[uartx].rx_callback_ != NULL) return;   // 已初始化

    // 初始化UART
    BSP_UART_Init(uartx, baudrate);

    BSP_UART_RxHandle_t *rx_handle = (BSP_UART_RxHandle_t *)handle;
    rx_handle->uartx_ = uartx;
    rx_handle->baudrate_ = baudrate;
    rx_handle->rx_callback_ = rx_callback;
    rx_handle->frame_ready_ = 0;
    rx_handle->frame_size_ = 0;
    memset(rx_handle->rx_buffer_, 0, BSP_UART_BUFFER_SIZE);
    rx_handle->Start_Rx = BSP_UART_RxHandle_Start_Rx;
    rx_handle->Stop_Rx = BSP_UART_RxHandle_Stop_Rx;
    g_uart_rx_handle[uartx] = *rx_handle;

    rx_handle->Start_Rx(rx_handle);
}

/**
 * @brief UART接收事件回调函数
 * @param huart UART句柄指针
 * @param Size 接收到的数据长度
 * @return None
 * @note 该函数在UART接收完成时被调用，用于处理接收到的数据。
 */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    // 1. 清除IDLE中断标志位
    // 读取ISR寄存器
    volatile uint32_t temp = huart->Instance->ISR;
    // 读取RDR寄存器（必须先读ISR再读RDR才能清除IDLE标志）
    temp = huart->Instance->RDR;
    
    // 2. 存储接收到的数据长度
    BSP_UART_RxHandle_t *rx_handle = BSP_UART_GetRxHandle(BSP_UART_FromHandle(huart));
    if (rx_handle != NULL)
    {
        // 计算接收到的数据量
        rx_handle->frame_size_ = Size;
        rx_handle->frame_ready_ = 1;
        
        // 如果用户注册了回调函数，则调用它
        if (rx_handle->rx_callback_ != NULL)
        {
            rx_handle->rx_callback_(rx_handle);
        }
        
        // 3. 清除标志位
        rx_handle->frame_ready_ = 0;
        rx_handle->frame_size_ = 0;

        // 4. 启动DMA接收
        HAL_UARTEx_ReceiveToIdle_DMA(huart, rx_handle->rx_buffer_, BSP_UART_BUFFER_SIZE);
    }
}
