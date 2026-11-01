/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:50
* @version: v1.0.0
* @description:位置式PID
********************************************************************************/
#include "../Inc/positional_pid.h"
#include "../../bases/Inc/algorithms_math.h"

/**
 * @brief 设置目标控制量
 * @param self PID控制器实例指针
 * @param setpoint 目标值
 * @param setpoint_index 目标值指针（动态调整用，可为NULL）
 * @note 若使能自动重置（SetAutoReset），当设定值变化量超过阈值时：
 *       - 积分项（integral_）清零，防止积分饱和
 *       - 前次误差（prev_error_）清零，避免微分冲击
 */
static void PositionalPID_Set_Target(void *self, signal_t setpoint, signal_t *setpoint_index)
{
    PositionalPID_t *pid = (PositionalPID_t *)self;
    // 1. 检查必要参数指针有效性
    if(pid->setpoint_ == NULL || pid->auto_reset_enable_ == NULL ||
    pid->auto_reset_threshold_ == NULL)
    {
        // 参数指针无效，触发断言
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"PositionalPID_Set_Target Input Error\n", 38);
        assert(0);
        return;
    }
    // 2. 自动重置检测
    if (*pid->auto_reset_enable_ &&
    algorithms_abs(setpoint - *pid->setpoint_) > *pid->auto_reset_threshold_)
    {
        // 设定值突变时，自动重置积分项和微分项
        pid->integral_ = 0;       // 重置积分项
        pid->prev_error_ = 0;     // 重置微分参考误差
    }
    // 3. 更新设定值指针或静态值
    pid->setpoint_static_ = setpoint;
    pid->setpoint_ = setpoint_index != NULL ? setpoint_index : &pid->setpoint_static_;
    pid->is_wired_ = 0;
}

/**
 * @brief 连接PID控制器参数到外部信号源
 * @param self PID控制器实例指针
 * @param param_id 参数ID（如KP、KI等）
 * @param source_ptr 指向外部信号源的指针（如float *kp_ptr）
 * @return char 连接成功返回1，失败返回0
 * @note 该函数用于将PID控制器的参数（如输入、比例系数、积分限幅等）连接到外部信号源。
 *       输入参数与要连接的参数ID数据类型需匹配。
 */
static char PositionalPID_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"PositionalPID_Connect Input Error\n", 35);
        assert(0 && "Invalid parameter ID");
        return 0;
    }

    PositionalPID_t *pid = (PositionalPID_t *)self;
    switch(param_id)
    {
        case POSITIONALPID_PORT_INPUT:
            pid->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_KP:
            pid->kp_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_KI:
            pid->ki_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_KD:
            pid->kd_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_SETPOINT:
            pid->setpoint_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_INTEGRAL_LIMIT:
            pid->integral_limit_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_AUTO_RESET_ENABLE:
            pid->auto_reset_enable_ = CtrlModule_Param_Transform(CTRL_PARAM_CHAR, param).value_.ptr_;
            break;
        case POSITIONALPID_PORT_AUTO_RESET_THRESHOLD:
            pid->auto_reset_threshold_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"PositionalPID_Connect Input Error\n", 35);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    pid->is_wired_ = 0;
    return 1; // 设置成功
}

/**
 * @brief 设置静态参数（如比例系数、积分限幅等）
 * @param self 指向IncrementalPID_t结构体的指针
 * @param param_id 参数ID（如KP、KI等）
 * @param value_ptr 指向参数值的指针（如float *kp_ptr）
 * @note 该函数仅在初始化时调用，用于设置静态参数。输入参数与要设置的参数ID数据类型需匹配。
 */
static char PositionalPID_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"PositionalPID_SetStaticParam Input Error\n", 42);
        assert(0 && "Invalid parameter");
        return 0;
    }

    PositionalPID_t *pid = (PositionalPID_t *)self;
    signal_t temp;
    switch(param_id)
    {
        case POSITIONALPID_PORT_KP:
            pid->kp_static_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.float_;
            break;
        case POSITIONALPID_PORT_KI:
            pid->ki_static_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.float_;
            break;
        case POSITIONALPID_PORT_KD:
            pid->kd_static_ = CtrlModule_Param_Transform(CTRL_PARAM_FLOAT, param).value_.float_;
            break;
        case POSITIONALPID_PORT_SETPOINT:
            pid->setpoint_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        case POSITIONALPID_PORT_INTEGRAL_LIMIT:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            pid->integral_limit_static_ = temp > 0 ? temp : -temp;
            break;
        case POSITIONALPID_PORT_AUTO_RESET_ENABLE:
            pid->auto_reset_enable_static_ = CtrlModule_Param_Transform(CTRL_PARAM_CHAR, param).value_.char_;
            break;
        case POSITIONALPID_PORT_AUTO_RESET_THRESHOLD:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            pid->auto_reset_threshold_static_ = temp > 0 ? temp : -temp;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"PositionalPID_SetStaticParam Input Error\n", 42);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    pid->is_wired_ = 0;
    return 1; // 设置成功
}

/**
 * @brief PID核心控制算法
 * @param self PID控制器实例指针
 * @note 调用周期应固定（建议1ms~10ms），输入/输出单位需与硬件匹配
 */
static void PositionalPID_Process(void *self)
{
    PositionalPID_t *pid = (PositionalPID_t *)self;

    // 确保所有必要的参数指针有效
    if(!pid->is_wired_){
        if(pid->input_ == NULL || pid->setpoint_ == NULL ||
        pid->kp_ == NULL || pid->ki_ == NULL || pid->kd_ == NULL ||
        pid->integral_limit_ == NULL || pid->auto_reset_enable_ == NULL ||
        pid->auto_reset_threshold_ == NULL)
        {
            // 参数指针无效，触发断言
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"PositionalPID_Process Input Error\n", 35);
            assert(0);
            pid->base_.output_ = 0;
            return;
        }
        pid->is_wired_ = 1;
    }
    
    // 1. 计算当前误差（设定值 - 反馈值）
    signal_t error = *pid->setpoint_ - *pid->input_;

    // 2. 积分项计算
    pid->integral_ += *pid->ki_ * error;
    // 积分限幅：防止积分饱和（积分项超过限幅时不再累加）
    if (pid->integral_ > *pid->integral_limit_){
        pid->integral_ = *pid->integral_limit_;
    }
    else if (pid->integral_ < -*pid->integral_limit_){
        pid->integral_ = -*pid->integral_limit_;
    }

    // 3. 微分项计算（当前误差 - 前次误差，反映误差变化率）
    signal_t derivative = error - pid->prev_error_;
    pid->prev_error_ = error;  // 更新前次误差，供下次微分计算

    // 4. 位置式PID公式：输出 = Kp*e(k) + Ki*Σe(i) + Kd*(e(k)-e(k-1))
    signal_t output = 
        *pid->kp_ * error +
        pid->integral_ +
        *pid->kd_ * derivative;

    // 5. 返回PID计算结果
    pid->base_.output_ = output;
}

/**
 * @brief 构造函数：初始化PID参数及状态变量
 * @param self PID控制器实例指针
 */
void PositionalPID_Init(void *self)
{
    PositionalPID_t *pid = (PositionalPID_t *)self;
    // 1. 初始化静态参数
    pid->kp_static_ = 0;
    pid->ki_static_ = 0;
    pid->kd_static_ = 0;
    pid->setpoint_static_ = 0;
    pid->integral_limit_static_ = 0;
    pid->auto_reset_enable_static_ = 0;
    pid->auto_reset_threshold_static_ = 0;
    // 2. 绑定动态参数指针
    pid->kp_ = &pid->kp_static_;
    pid->ki_ = &pid->ki_static_;
    pid->kd_ = &pid->kd_static_;
    pid->setpoint_ = &pid->setpoint_static_;
    pid->integral_limit_ = &pid->integral_limit_static_;
    pid->auto_reset_enable_ = &pid->auto_reset_enable_static_;
    pid->auto_reset_threshold_ = &pid->auto_reset_threshold_static_;
    // 3. 初始化状态参数
    pid->integral_ = 0;
    pid->prev_error_ = 0;
    pid->is_wired_ = 0;
    // 4. 绑定处理函数指针
    pid->base_.Process = PositionalPID_Process;
    pid->base_.Connect = PositionalPID_Connect;
    pid->base_.SetStaticParam = PositionalPID_SetStaticParam;
    pid->base_.type_ = MODULE_POSITIONAL_PID;

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"PositionalPID_Init Success\n", 28);
}
