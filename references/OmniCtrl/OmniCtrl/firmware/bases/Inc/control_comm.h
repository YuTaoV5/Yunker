/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-18 18:21
* @version: v1.0.0
* @description: 
********************************************************************************/
#ifndef __CONTROL_COMM_H
#define __CONTROL_COMM_H

#include <stdint.h>

/*-----------------------------------宏定义-----------------------------------*/
#define CONTROL_COMM_GRAPH_SIZE 100   // 图最大尺寸


/*---------------------------------类型定义-----------------------------------*/
typedef void (*CTRL_Register_Bootloader_t)(void);    // 注册引导模式函数指针


/*---------------------------------变量声明-----------------------------------*/
extern uint8_t graph[];     // 控制通信图
extern CTRL_Register_Bootloader_t Control_Comm_Bootloader_Func;    // 控制通信引导模式函数指针
extern char control_into_bootloader;     // 控制通信是否进入引导模式标志位


/*---------------------------------函数声明-----------------------------------*/
void Control_Comm_Register_Bootloader(CTRL_Register_Bootloader_t func);
uint32_t Control_Comm_Get_Graph(uint8_t *rx_data, uint32_t size);


#endif
