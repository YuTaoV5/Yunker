/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-06 16:30
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __BSP_INTERFACE_H
#define __BSP_INTERFACE_H

#include "bsp_common.h"
#include "bsp_gpio.h"
#include "bsp_spi.h"
#include "bsp_tim.h"
#include "bsp_uart.h"

// OLED
#define OLED_SPI BSP_SPI1
#define OLED_RES_PORT BSP_GPIO_PORT_A
#define OLED_RES_PIN BSP_GPIO_PIN_8
#define OLED_DC_PORT BSP_GPIO_PORT_B
#define OLED_DC_PIN BSP_GPIO_PIN_0
#define OLED_Width  128 // OLED宽度（不与初始化绑定）
#define OLED_Height 64  // OLED高度
#define OLED_Word_Height 8 // OLED默认字高
#define OLED_Word_Width 6 // OLED默认字宽

// KEY
#define KEY1_GPIO_PORT BSP_GPIO_PORT_A
#define KEY1_GPIO_PIN BSP_GPIO_PIN_11
#define KEY2_GPIO_PORT BSP_GPIO_PORT_A
#define KEY2_GPIO_PIN BSP_GPIO_PIN_12
#define KEY_ACTIVE_LEVEL BSP_GPIO_PIN_RESET

// A4950
#define A4950A_TIMx_1 BSP_TIM2
#define A4950A_TIMx_2 BSP_TIM2
#define A4950A_TIM_CHANNEL_1 BSP_TIM_CHANNEL_3
#define A4950A_TIM_CHANNEL_2 BSP_TIM_CHANNEL_4
#define A4950B_TIMx_1 BSP_TIM2
#define A4950B_TIMx_2 BSP_TIM2
#define A4950B_TIM_CHANNEL_1 BSP_TIM_CHANNEL_1
#define A4950B_TIM_CHANNEL_2 BSP_TIM_CHANNEL_2

// Encoder
#define EncoderA_TIMx BSP_TIM3
#define EncoderB_TIMx BSP_TIM4

// Sys_Timer
#define Sys_Timer_TIMx BSP_TIM6

// LOG
#define LOG_UART BSP_UART1

// Comm
#define Comm_UART_UARTx BSP_UART1
#define Comm_485_UARTx BSP_UART2
#define Comm_485_GPIO_PORT BSP_GPIO_PORT_B
#define Comm_485_GPIO_PIN BSP_GPIO_PIN_4

#endif // __BSP_INTERFACE_H
