/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: branch judge
********************************************************************************/
#include "../Inc/branch_judge.h"
#include "../../bases/Inc/algorithms_math.h"

static char BranchJudge_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"BranchJudge_Connect Input Error\n", 30);
        assert(0 && "Invalid parameter");
        return 0;
    }

    BranchJudge_t *judge = (BranchJudge_t *)self;
    switch(param_id)
    {
        case BRANCHJUDGE_PORT_CONDITION:
            judge->condition_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case BRANCHJUDGE_PORT_TRUE_INPUT:
            judge->true_input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case BRANCHJUDGE_PORT_FALSE_INPUT:
            judge->false_input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case BRANCHJUDGE_PORT_THRESHOLD:
            judge->threshold_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case BRANCHJUDGE_PORT_HYSTERESIS:
            judge->hysteresis_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"BranchJudge_Connect Input Error\n", 30);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    judge->is_wired_ = 0;
    return 1;
}

static char BranchJudge_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"BranchJudge_SetStaticParam Input Error\n", 37);
        assert(0 && "Invalid parameter");
        return 0;
    }

    BranchJudge_t *judge = (BranchJudge_t *)self;
    signal_t temp = 0;
    switch(param_id)
    {
        case BRANCHJUDGE_PORT_THRESHOLD:
            judge->threshold_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            break;
        case BRANCHJUDGE_PORT_HYSTERESIS:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            judge->hysteresis_static_ = temp > 0 ? temp : -temp;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"BranchJudge_SetStaticParam Input Error\n", 37);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    judge->is_wired_ = 0;
    return 1;
}

static void BranchJudge_Process(void *self)
{
    BranchJudge_t *judge = (BranchJudge_t *)self;

    if(!judge->is_wired_)
    {
        if(judge->condition_ == NULL || judge->true_input_ == NULL ||
            judge->false_input_ == NULL || judge->threshold_ == NULL ||
            judge->hysteresis_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"BranchJudge_Process Input Error\n", 30);
            assert(0);
            judge->base_.output_ = 0;
            return;
        }
        judge->is_wired_ = 1;
    }

    signal_t condition = *judge->condition_;
    signal_t threshold = *judge->threshold_;
    signal_t hysteresis = *judge->hysteresis_;
    hysteresis = hysteresis > 0 ? hysteresis : -hysteresis;

    if(judge->branch_state_)
    {
        if(condition <= threshold - hysteresis)
        {
            judge->branch_state_ = 0;
        }
    }
    else
    {
        if(condition >= threshold + hysteresis)
        {
            judge->branch_state_ = 1;
        }
    }

    judge->base_.output_ = judge->branch_state_ ? *judge->true_input_ : *judge->false_input_;
}

void BranchJudge_Init(void *self)
{
    BranchJudge_t *judge = (BranchJudge_t *)self;

    judge->threshold_static_ = 0;
    judge->hysteresis_static_ = 0;
    judge->condition_ = NULL;
    judge->true_input_ = NULL;
    judge->false_input_ = NULL;
    judge->threshold_ = &judge->threshold_static_;
    judge->hysteresis_ = &judge->hysteresis_static_;
    judge->branch_state_ = 0;
    judge->is_wired_ = 0;

    judge->base_.Process = BranchJudge_Process;
    judge->base_.Connect = BranchJudge_Connect;
    judge->base_.SetStaticParam = BranchJudge_SetStaticParam;
    judge->base_.type_ = MODULE_BRANCH_JUDGE;
    judge->base_.output_ = 0;

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"BranchJudge_Init Success\n", 25);
}

