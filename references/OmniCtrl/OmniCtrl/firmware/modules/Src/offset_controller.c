/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 23:00
* @version: v1.0.0
* @description: 偏移控制器实现
********************************************************************************/
#include "../Inc/offset_controller.h"

/**
 * @brief: 偏移控制器连接函数
 * @param self 偏移控制器实例指针
 * @param param_id 参数ID
 * @param source_ptr 源指针
 * @return char 连接成功返回1，失败返回0
 */
static char OffsetController_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"OffsetController_Connect Input Error\n", 38);
        assert(0 && "Invalid parameter"); // 无效参数，触发断言
        return 0; // 连接失败
    }

    OffsetController_t *offset = (OffsetController_t *)self;
    switch(param_id)
    {
        case OFFSET_PORT_INPUT:
            offset->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case OFFSET_PORT_OFFSET:
            offset->offset_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"OffsetController_Connect Input Error\n", 38);
            assert(0 && "Invalid parameter ID"); // 无效参数，触发断言
            return 0; // 连接失败
    }
    offset->is_wired_ = 0;
    return 1; // 连接成功
}

/**
 * @brief: 偏移控制器设置静态参数函数
 * @param self 偏移控制器实例指针
 * @param param_id 参数ID
 * @param value_ptr 值指针
 * @return char 设置成功返回1，失败返回0
 */
static char OffsetController_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"OffsetController_SetStaticParam Input Error\n", 45);
        assert(0 && "Invalid parameter"); // 无效参数，触发断言
        return 0; // 连接失败
    }

    OffsetController_t *offset = (OffsetController_t *)self;
    switch(param_id)
    {
        case OFFSET_PORT_OFFSET:
            offset->offset_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"OffsetController_SetStaticParam Input Error\n", 45);
            assert(0 && "Invalid parameter ID"); // 无效参数，触发断言
            return 0; // 连接失败
    }
    offset->is_wired_ = 0;
    return 1; // 连接成功
}

/**
 * @brief: 偏移控制器处理函数
 * @param ctrl 偏移控制器实例指针
 */
static void OffsetController_Process(void *self)
{
    OffsetController_t *ctrl = (OffsetController_t *)self;
    if(!ctrl->is_wired_)
    {
        if(ctrl->input_ == NULL || ctrl->offset_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"OffsetController_Process Input Error\n", 38);
            assert(0); // 输入或偏移量未绑定，触发断言
            ctrl->base_.output_ = 0;
            return;
        }
        ctrl->is_wired_ = 1;
    }
    ctrl->base_.output_ = (*(ctrl->input_)) + (*(ctrl->offset_));
}

/**
 * @brief: 偏移控制器构造函数
 * @param self 偏移控制器实例指针
 * @param offset 偏移量
 * @param input 输入信号指针
 * @param offset_index 偏移量索引指针，若为NULL则使用静态偏移量
 */
void OffsetController_Init(void *self)
{
    OffsetController_t *ctrl = (OffsetController_t *)self;
    
    ctrl->input_ = NULL;
    ctrl->offset_static_ = 0;
    ctrl->offset_ = &ctrl->offset_static_;
    ctrl->base_.Process = OffsetController_Process;
    ctrl->base_.Connect = OffsetController_Connect;
    ctrl->base_.SetStaticParam = OffsetController_SetStaticParam;
    ctrl->base_.type_ = MODULE_OFFSET;
    ctrl->is_wired_ = 0;

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"OffsetController_Init\n", 23);
}
