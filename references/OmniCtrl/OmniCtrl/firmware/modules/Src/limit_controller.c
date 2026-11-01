/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-11-12 22:47
* @version: v1.0.0
* @description: 限幅控制器类
********************************************************************************/
#include "../Inc/limit_controller.h"

/**
 * @brief: 限幅控制器连接函数
 * @description: 用于将限幅控制器的输入、输出最小值和最大值连接到外部信号源
 * @param self 限幅控制器实例指针
 * @param param_id 参数ID（如INPUT、OUTPUT_MIN、OUTPUT_MAX等）
 * @param source_ptr 指向信号源的指针（如signal_t *input_ptr）
 * @return char 连接状态，1表示成功，0表示失败
 */
static char LimitController_Connect(void *self, char param_id, 
            CtrlModule_Param_t param)
{
    if(self == NULL){
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"LimitController_Connect Input Error\n", 37);
        assert(0 && "Invalid parameter");
        return 0;
    }

    LimitController_t *limit = (LimitController_t *)self;
    switch(param_id)
    {
        case LIMIT_PORT_INPUT:
            limit->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case LIMIT_PORT_OUTPUT_MIN:
            limit->output_min_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case LIMIT_PORT_OUTPUT_MAX:
            limit->output_max_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"LimitController_Connect Input Error\n", 37);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    limit->is_wired_ = 0;
    return 1;
}

/**
 * @brief: 设置限幅控制器的最大输出值
 * @description: 更新输出的最大值
 * @param self 限幅控制器实例指针
 * @param param_id 参数ID（如OUTPUT_MIN、OUTPUT_MAX等）
 * @param value_ptr 指向参数值的指针（如signal_t *min_ptr）
 * @note 该函数仅在初始化时调用，用于设置静态参数。输入参数与要设置的参数ID数据类型需匹配。
 */
static char LimitController_SetStaticParam(void *self, char param_id, 
            CtrlModule_Param_t param)
{
    if(self == NULL || param.type_ >= CTRL_PARAM_NUM)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"LimitController_SetStaticParam Input Error\n", 44);
        assert(0 && "Invalid parameter");
        return 0;
    }

    LimitController_t *limit = (LimitController_t *)self;
    switch(param_id)
    {
        case LIMIT_PORT_OUTPUT_MIN:
            limit->output_min_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        case LIMIT_PORT_OUTPUT_MAX:
            limit->output_max_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"LimitController_SetStaticParam Input Error\n", 44);
            assert(0 && "Invalid parameter ID");
            return 0; // 无效参数ID
    }
    limit->is_wired_ = 0;
    return 1;
}

/**
 * @brief: 限制控制器处理函数
 * @description: 对输入进行限制，确保输出在指定范围内
 * @param self 限幅控制器实例指针
 */
static void Limit_Process(void *self)
{
    LimitController_t *limit = (LimitController_t *)self;

    // 确保输入指针有效
    if(!limit->is_wired_)
    {
        if (limit->input_ == NULL || limit->output_min_ == NULL 
            || limit->output_max_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"LimitController_Process Input Error\n", 37);
            limit->base_.output_ = *limit->output_min_;
            assert(0);
            return;
        }
        limit->is_wired_ = 1;
    }
    

    // 确保最小值不大于最大值
    signal_t temp_input = *limit->input_;
    signal_t temp_min = *limit->output_min_;
    signal_t temp_max = *limit->output_max_;
    if (temp_min >= temp_max)
    {
        signal_t temp = temp_min;
        temp_min = temp_max;
        temp_max = temp;
    }

    // 处理NaN值
    if(temp_input != temp_input)
    {
        limit->base_.output_ = *limit->output_min_;
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"LimitController NaN value detected\n", 36);
        assert(0 && "NaN value detected");
        return;
    }

    // 输入值超出范围，返回边界值
    limit->base_.output_ = temp_input > temp_max ? temp_max : temp_input;
    limit->base_.output_ = temp_input < temp_min ? temp_min : limit->base_.output_;
}

/**
 * @brief: 限制控制器构造函数
 * @description: 初始化输出范围
 * @param self 限幅控制器实例指针
 */
void LimitController_Init(void *self)
{
    LimitController_t *limit = (LimitController_t *)self;

    // 初始化静态存储和指针
    limit->output_min_ = &limit->output_min_static_;
    limit->output_max_ = &limit->output_max_static_;
    
    limit->output_min_static_ = 0;
    limit->output_max_static_ = 0;
    limit->input_ = NULL;
    limit->base_.Process = Limit_Process;
    limit->base_.Connect = LimitController_Connect;
    limit->base_.SetStaticParam = LimitController_SetStaticParam;
    limit->base_.type_ = MODULE_LIMIT;

    limit->is_wired_ = 0;
    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"LimitController_Init\n", 22);
}
