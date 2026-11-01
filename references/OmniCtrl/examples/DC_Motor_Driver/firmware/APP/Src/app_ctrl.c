/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-15 00:39
* @version: v1.0.0
* @description: 
********************************************************************************/
#include "app_ctrl.h"
#include "app_boot.h"
#include "app_comm.h"
#include "Flash.h"
#include "app_system.h"
#include "control_core.h"
#include "control_comm.h"

/**
 * @brief 初始化控制器
 * @param None
 * @return None
 */
void APP_Ctrl_Init(void)
{
    // 初始化电机、编码器
    Motor_Init();

    // 初始化控制核心
    Control_Comm_Register_Bootloader(Boot_Process);
    Control_Log_Tx_Register(Ctrl_Tx);
    Flash_Read(sizeof(System_Setting_t), graph, CONTROL_COMM_GRAPH_SIZE);
    ControlCore_Init();
}

/**
 * @brief 控制器处理函数
 * @param None
 * @return None
 */
void APP_Ctrl_Process(void)
{
    // 获取电机速度
    Encoder_Update(Motor_A.encoder_);
    Motor_A.encoder_->Count_ *= -1;
    Encoder_Update(Motor_B.encoder_);
    Motor_B.encoder_->Count_ *= -1;
    APP_Comm_OnCtrlTick();

    ControlCore_Update();
    Motor_SetSpeed(&Motor_A, ctrl_output_signal[0]);
    Motor_SetSpeed(&Motor_B, ctrl_output_signal[1]);
}
