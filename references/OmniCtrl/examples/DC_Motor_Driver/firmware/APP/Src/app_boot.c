/********************************************************************************
 * @author: Ternura_xiang
 * @email: ternura_xiang@foxmail.com
 * @date: 2026-01-14 21:11
 * @version: v1.0.0
 * @description:
 ********************************************************************************/
#include "control_comm.h"
#include "app_system.h"
#include "Flash.h"
#include "comm.h"
#include "SysTimer.h"
#include "OLED.h"
#include <string.h>

uint8_t boot_buf[100];
uint16_t boot_frame_size = 0;
uint32_t graph_size = 0;

static void Boot_RxCallback(void)
{
    comm_boot.get_rx_buffer(&comm_boot, boot_buf);
    boot_frame_size = comm_boot.get_frame_size(&comm_boot);
    Comm_SendBytes(&comm_boot, boot_buf, boot_frame_size);
}

/**
 * @brief: 引导模式发送数据
 * @param data: 数据指针
 * @param size: 数据大小
 */
void Ctrl_Tx(uint8_t *data, uint16_t size)
{
    Comm_SendBytes(&comm_ctrl, data, size);
}

/**
 * @brief: 引导模式处理函数
 * @description: 处理引导模式接收的数据，提取控制通信图
 */
void Boot_Process(void)
{
    Comm_Init(&comm_boot, 0, 115200, Boot_RxCallback);  // 0: UART1
    Comm_SendBytes(&comm_boot, (uint8_t *)"boot mode ready!", 17);
    SysTimer_DelayMs(10);
    Comm_SendBytes(&comm_boot, (uint8_t *)"current graph:", 14);
    SysTimer_DelayMs(10);
    Flash_Read(sizeof(System_Setting_t), graph, CONTROL_COMM_GRAPH_SIZE);
    Comm_SendBytes(&comm_boot, graph, CONTROL_COMM_GRAPH_SIZE);

    while (1)
    {
        if(boot_frame_size == 0) continue;

        // 提取控制通信图
        graph_size = Control_Comm_Get_Graph(boot_buf, boot_frame_size);
        SysTimer_DelayMs(10);   // 用于与重发的串口数据进行隔离
        if (graph_size != 0)
        {
            memset(graph, 0xFF, CONTROL_COMM_GRAPH_SIZE);   // 先将FLASH中的数据清空
            memcpy(graph, boot_buf, graph_size);            // 复制控制通信图到FLASH
            g_system_status.set_need_save(1);               // 保存到FLASH
            g_system_status.update();

            // 发送确认响应
            Comm_SendBytes(&comm_boot, (uint8_t *)"graph set success!", 19);
        }
        else
        {
            Comm_SendBytes(&comm_boot, (uint8_t *)"graph set failed!", 18);
        }

        boot_frame_size = 0;    // 重置接收缓冲区大小
    }
}
