/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:50
* @version: v1.0.0
* @description: 增量式PID
********************************************************************************/
#include "../Inc/incremental_pid.h"
#include "../../bases/Inc/algorithms_math.h"

/**
 * @brief 设置目标控制量（设定值）
 * @param self 指向IncrementalPID_t结构体的指针
 * @param setpoint 目标值（如电机目标位置/速度，单位与输入一致）
 * @param setpoint_index 目标值指针（NULL=不绑定）
 * @note 若使能自动重置（SetAutoReset），当设定值变化量超过阈值时：
 *       - 积分项（integral_）清零，防止积分饱和
 *       - 前次误差（prev_error_）清零，避免微分冲击
 */
static void IncrementalPID_Set_Target(void *self, signal_t setpoint, signal_t *setpoint_index)
{
    IncrementalPID_t *pid = (IncrementalPID_t *)self;
    // 1. 检查必要参数指针有效性
    if(pid->setpoint_ == NULL || pid->auto_reset_enable_ == NULL ||
    pid->auto_reset_threshold_ == NULL)
    {
        // 参数指针无效，触发断言
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"IncrementalPID_Set_Target Input Error\n", 39);
        assert(0);
        return;
    }
    // 2. 自动重置检测
    if(pid->auto_reset_enable_ &&
        algorithms_abs(setpoint - *pid->setpoint_) > *pid->auto_reset_threshold_)
    {
        // 设定值突变时，自动重置微分项
        pid->prev_error_ = 0;     // 重置微分参考误差
        pid->prev_prev_error_ = 0; // 重置前次微分参考误差
    }
    // 3. 更新目标设定值
    pid->setpoint_static_ = setpoint;    // 更新目标设定值
    pid->setpoint_ = setpoint_index != NULL ? setpoint_index : &pid->setpoint_static_;
    pid->is_wired_ = 0; // 重置绑定状态，确保下次处理函数调用时重新检查指针有效性
}

/**
 * @brief PID核心控制算法（增量式）
 * @param self 指向IncrementalPID_t结构体的指针
 * @note 调用周期应固定（建议1ms~10ms），输入/输出单位需与硬件匹配
 */
static void IncrementalPID_Process(void *self)
{
    // 未来考虑添加error、output的NaN处理
    IncrementalPID_t *pid = (IncrementalPID_t *)self;

    // 确保所有必要的参数指针有效
    if(!pid->is_wired_)
    {
        if(pid->input_ == NULL || pid->setpoint_ == NULL || pid->integral_limit_ == NULL ||
        pid->kp_ == NULL || pid->ki_ == NULL || pid->kd_ == NULL ||
        pid->auto_reset_enable_ == NULL || pid->auto_reset_threshold_ == NULL)
        {
            // 参数指针无效，触发断言
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"IncrementalPID_Process Input Error\n", 36);
            assert(0);
            pid->base_.output_ = 0;
            return;
        }
        pid->is_wired_ = 1;
    }

    // 未来考虑添加动态目标值突变处理
    // 1. 计算当前误差（设定值 - 反馈值）
    signal_t error = *pid->setpoint_ - *pid->input_;
    // 2. 计算增量式PID的三个组成部分并求和得到输出增量
    pid->base_.output_ += (
        *pid->kp_ * (error - pid->prev_error_) +
        *pid->ki_ * (error) +
        *pid->kd_ * (error - 2 * pid->prev_error_ + pid->prev_prev_error_));
    // 3. 输出限幅处理
    if(pid->base_.output_ > *pid->integral_limit_){
        pid->base_.output_ = *pid->integral_limit_;
    } else if (pid->base_.output_ < -(*pid->integral_limit_)){
        pid->base_.output_ = -(*pid->integral_limit_);
    }
    // 4. 更新误差历史，供下次计算使用
    pid->prev_prev_error_ = pid->prev_error_;
    pid->prev_error_ = error;
}

/**
 * @brief 连接信号端口（如输入、输出、设定值等）
 * @param self 指向IncrementalPID_t结构体的指针
 * @param param_id 参数ID（如INPUT、KP等）
 * @param source_ptr 指向信号值的指针（如signal_t *input_ptr）
 * @note 该函数仅在初始化时调用，用于设置动态参数。输入参数与要设置的参数ID数据类型需匹配。
 */
static char IncrementalPID_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"IncrementalPID_Connect Input Error\n", 36);
        assert(0 && "Invalid parameter");
        return 0; // 无效参数
    }

    IncrementalPID_t *pid = (IncrementalPID_t *)self;
    switch(param_id)
    {
        case INCREMENTALPID_PORT_INPUT:
            pid->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_KP:
            pid->kp_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_KI:
            pid->ki_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_KD:
            pid->kd_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_SETPOINT:
            pid->setpoint_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_INTEGRAL_LIMIT:
            pid->integral_limit_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_AUTO_RESET_ENABLE:
            pid->auto_reset_enable_ = CtrlModule_Param_Transform(CTRL_PARAM_CHAR, param).value_.ptr_;
            break;
        case INCREMENTALPID_PORT_AUTO_RESET_THRESHOLD:
            pid->auto_reset_threshold_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"IncrementalPID_Connect Input Error\n", 36);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    pid->is_wired_ = 0;
    return 1; // 连接成功
}

/**
 * @brief 设置静态参数（如比例系数、积分限幅等）
 * @param self 指向IncrementalPID_t结构体的指针
 * @param param_id 参数ID（如KP、KI等）
 * @param value_ptr 指向参数值的指针（如float *kp_ptr）
 * @note 该函数仅在初始化时调用，用于设置静态参数。输入参数与要设置的参数ID数据类型需匹配。
 */
static char IncrementalPID_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL){
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"IncrementalPID_SetStaticParam Input Error\n", 43);
        assert(0 && "Invalid parameter");
        return 0;
    }

    IncrementalPID_t *pid = (IncrementalPID_t *)self;
    signal_t temp;
    switch(param_id)
    {
        case INCREMENTALPID_PORT_KP:
            pid->kp_static_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.float_;
            break;
        case INCREMENTALPID_PORT_KI:
            pid->ki_static_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.float_;
            break;
        case INCREMENTALPID_PORT_KD:
            pid->kd_static_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.float_;
            break;
        case INCREMENTALPID_PORT_SETPOINT:
            pid->setpoint_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        case INCREMENTALPID_PORT_INTEGRAL_LIMIT:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            pid->integral_limit_static_ = temp > 0 ? temp : -temp;
            break;
        case INCREMENTALPID_PORT_AUTO_RESET_ENABLE:
            pid->auto_reset_enable_static_ = CtrlModule_Param_Transform(CTRL_PARAM_CHAR, param).value_.char_;
            break;
        case INCREMENTALPID_PORT_AUTO_RESET_THRESHOLD:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            pid->auto_reset_threshold_static_ = temp > 0 ? temp : -temp;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"IncrementalPID_SetStaticParam Input Error\n", 43);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    pid->is_wired_ = 0;
    return 1; // 设置成功
}

/**
 * @brief 构造函数：初始化PID参数及状态变量
 * @param self 指向IncrementalPID_t结构体的指针
 */
void IncrementalPID_Init(void *self)
{
    IncrementalPID_t *pid = (IncrementalPID_t *)self;
    // 1. 初始化静态参数
    pid->kp_static_ = 0;
    pid->ki_static_ = 0;
    pid->kd_static_ = 0;
    pid->setpoint_static_ = 0;
    pid->integral_limit_static_ = 0;
    pid->auto_reset_enable_static_ = 0;
    pid->auto_reset_threshold_static_ = 0;
    // 2. 绑定动态参数指针
    pid->input_ = NULL;
    pid->kp_ = &pid->kp_static_;
    pid->ki_ = &pid->ki_static_;
    pid->kd_ = &pid->kd_static_;
    pid->setpoint_ = &pid->setpoint_static_;
    pid->integral_limit_ = &pid->integral_limit_static_;
    pid->auto_reset_enable_ = &pid->auto_reset_enable_static_;
    pid->auto_reset_threshold_ = &pid->auto_reset_threshold_static_;
    // 3. 初始化状态参数
    pid->prev_error_ = 0;
    pid->prev_prev_error_ = 0;
    pid->is_wired_ = 0;
    // 4. 绑定处理函数指针
    pid->base_.Process = IncrementalPID_Process;
    pid->base_.Connect = IncrementalPID_Connect;
    pid->base_.SetStaticParam = IncrementalPID_SetStaticParam;
    pid->base_.type_ = MODULE_INCREMENTAL_PID;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"IncrementalPID_Init Success\n", 29);
}
