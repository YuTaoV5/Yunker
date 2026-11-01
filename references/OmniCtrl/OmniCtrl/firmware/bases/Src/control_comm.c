/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-18 18:21
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "../Inc/control_comm.h"
#include "../Inc/control_log.h"
#include <stdio.h>
#include <assert.h>
#include <string.h> 


CTRL_Register_Bootloader_t Control_Comm_Bootloader_Func = NULL;
char control_into_bootloader;   // 标志是否进入引导模式（1为进入， 0为不进入）


// 格式：
// 0.帧头(0x201314)(4字节帧长度)
// ------------------ <情况1> ------------------
// 1.模块类型, 
// 2.参数ID, 参数类型(高六位为参数类型, 低两位为是否为指针), 参数值(4字节)
// ...(循环2.)
// 3.0xFF(模块结束标志)
// ------------------ <情况2> ------------------
// ->1.当最高位为1时，标志为输出参数。其余位为模块ID
// ->2.0xFF 

// ...(循环1.2.3.)
// 4.0xFF(参数结束标志)(与3.结合表现为0xFF 0xFF)
// -1.CRC32校验值(4字节)
uint8_t graph[CONTROL_COMM_GRAPH_SIZE];
// 示例如下：
// 20 13 14 00 00 00 13 03 00 01 C4 D3 51 1B FF FF 8E EB D1 E4
/*
{
    3, 
    0, 1, 0xC4, 0xD3, 0x51, 0x1B,
    1, 0x03<<4|0x02<<2, 0, 0, 0x20, 0x41,
    4, 1, 0x94, 0x2E, 0xFD, 0x99,
    0xFF, 0xFF
};*/


/**
 * @description: 获取CRC32校验值
 * @param data 数据指针
 * @param size 数据大小
 * @return uint32_t CRC32校验值
 */
static inline uint32_t Get_CRC32(uint8_t *data, uint32_t size)
{
    // 计算CRC32校验值
    uint32_t crc = 0xFFFFFFFF;
    for(uint32_t i = 0; i < size; i++)
    {
        crc ^= data[i];
        for(uint32_t j = 0; j < 8; j++)
        {
            if(crc & 0x01)
            {
                crc >>= 1;
                crc ^= 0xEDB88320;
            }
            else
            {
                crc >>= 1;
            }
        }
    }
    return crc;
}

/**
 * @description: 注册控制通信引导模式函数
 * @param func 控制通信引导模式函数指针
 * @return None
 */
void Control_Comm_Register_Bootloader(CTRL_Register_Bootloader_t func)
{
    Control_Comm_Bootloader_Func = func;
}

/**
 * @description: 进入引导模式
 * @return None
 * @note: 改函数仅标志进入引导模式, 实际在core中进行内存读取前进入。
 *          因此必须在ControlCore_Init前调用此函数
 */
void Control_Comm_Into_Bootloader(void)
{
    if(Control_Comm_Bootloader_Func != NULL)
    {
        control_into_bootloader = 1;
    }
    else
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"Into_Bootloader: Bootloader Func is NULL", 41);
        assert(0);
    }
}

/**
 * @description: 获取控制通信图
 * @return 控制通信图大小
 * @note: 该函数会修改rx_data数据, 因此在调用前应确保数据不会被修改。
 *        rx_data即为校验后的纯图结构
 */
uint32_t Control_Comm_Get_Graph(uint8_t *rx_data, uint32_t size)
{
    // 1. 检验发送标志位
    if(rx_data[0] == 0x20 && rx_data[1] == 0x13 && rx_data[2] == 0x14);
    else return 0;

    // 2. 获取数据帧长度
    uint32_t data_len = rx_data[3]<<24 | rx_data[4]<<16 | rx_data[5]<<8 | rx_data[6];
    if(data_len > size || size < 10) return 0;

    // 2. 对数据进行校验
    uint32_t crc;
    memcpy(&crc, rx_data+data_len-3, 4);
    uint32_t calc_crc = Get_CRC32(rx_data, data_len-3);
    if(calc_crc != crc) return 0;

    // 3. 重写数据
    if(data_len < 10) return 0;
    memmove(rx_data, rx_data+7, data_len-10);
    return data_len-10;
}
