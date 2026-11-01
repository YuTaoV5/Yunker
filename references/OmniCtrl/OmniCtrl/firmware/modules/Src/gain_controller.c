/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:50
* @version: v1.0.0
* @description: 增益控制器
********************************************************************************/
#include "../Inc/gain_controller.h"

/**
 * @brief 处理输入，根据增益系数进行缩放
 * @param self 增益控制器实例指针
 */
static void GainController_Process(void *self)
{
    GainController_t *gain = (GainController_t *)self;
    if(!gain->is_wired_)
    {
        if(gain->input_ == NULL || gain->gain_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"GainController_Process Input Error\n", 36);
            gain->base_.output_ = 0;
            assert(0); // 输入或增益未绑定，触发断言
            return;
        }
        gain->is_wired_ = 1;
    }
    gain->base_.output_ = (*(gain->input_)) * (*(gain->gain_));
}

/**
 * @brief 连接输入信号
 * @param self 增益控制器实例指针
 * @param param_id 端口ID
 * @param source_ptr 输入信号指针
 * @return 连接成功返回1，否则返回0
 * @note 该函数仅在初始化时调用，用于设置动态参数。输入参数与要设置的参数ID数据类型需匹配。
 */
static char GainController_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"GainController_Connect Input Error\n", 36);
        assert(0 && "Invalid parameter");
        return 0; // 无效参数
    }

    GainController_t *gain_ctrl = (GainController_t *)self;
    switch(param_id)
    {
        case GAIN_PORT_INPUT:
            gain_ctrl->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case GAIN_PORT_GAIN:
            gain_ctrl->gain_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"GainController_Connect Input Error\n", 36);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    gain_ctrl->is_wired_ = 0; // 标记为未连接，等待下一次连接
    return 1; // 成功连接
}

/**
 * @brief 设置静态参数
 * @param self 增益控制器实例指针
 * @param param_id 参数ID
 * @param value_ptr 参数值指针
 * @return 设置成功返回1，否则返回0
 * @note 该函数仅在初始化时调用，用于设置静态参数。输入参数与要设置的参数ID数据类型需匹配。
 */
static char GainController_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"GainController_SetStaticParam Input Error\n", 43);
        assert(0 && "Invalid parameter");
        return 0; // 无效参数
    }

    GainController_t *gain_ctrl = (GainController_t *)self;
    switch(param_id)
    {
        case GAIN_PORT_GAIN:
            gain_ctrl->gain_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"GainController_SetStaticParam Input Error\n", 43);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    gain_ctrl->is_wired_ = 0; // 标记为未连接，等待下一次连接
    return 1; // 成功设置静态参数
}

/**
 * @brief 构造函数
 * @param self 增益控制器实例指针
 */
void GainController_Init(void *self)
{
    GainController_t *ctrl = (GainController_t *)self;
    ctrl->base_.type_ = MODULE_GAIN;
    ctrl->base_.Process = GainController_Process;
    ctrl->base_.Connect = GainController_Connect;
    ctrl->base_.SetStaticParam = GainController_SetStaticParam;

    ctrl->input_ = NULL;
    ctrl->gain_static_ = 1;
    ctrl->gain_ = &ctrl->gain_static_;
    ctrl->is_wired_ = 0;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"GainController_Init Success\n", 29);
}
