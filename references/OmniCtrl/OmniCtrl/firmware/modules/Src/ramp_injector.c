/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: ramp injector
********************************************************************************/
#include "../Inc/ramp_injector.h"
#include "../../bases/Inc/algorithms_math.h"

static char RampInjector_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"RampInjector_Connect Input Error\n", 32);
        assert(0 && "Invalid parameter");
        return 0;
    }

    RampInjector_t *ramp = (RampInjector_t *)self;
    switch(param_id)
    {
        case RAMPINJECT_PORT_INPUT:
            ramp->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case RAMPINJECT_PORT_RISE_STEP:
            ramp->rise_step_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case RAMPINJECT_PORT_FALL_STEP:
            ramp->fall_step_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"RampInjector_Connect Input Error\n", 32);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    ramp->is_wired_ = 0;
    return 1;
}

static char RampInjector_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"RampInjector_SetStaticParam Input Error\n", 39);
        assert(0 && "Invalid parameter");
        return 0;
    }

    RampInjector_t *ramp = (RampInjector_t *)self;
    signal_t temp = 0;
    switch(param_id)
    {
        case RAMPINJECT_PORT_RISE_STEP:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            ramp->rise_step_static_ = temp > 0 ? temp : -temp;
            break;
        case RAMPINJECT_PORT_FALL_STEP:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            ramp->fall_step_static_ = temp > 0 ? temp : -temp;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"RampInjector_SetStaticParam Input Error\n", 39);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    ramp->is_wired_ = 0;
    return 1;
}

static void RampInjector_Process(void *self)
{
    RampInjector_t *ramp = (RampInjector_t *)self;

    if(!ramp->is_wired_)
    {
        if(ramp->input_ == NULL || ramp->rise_step_ == NULL || ramp->fall_step_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"RampInjector_Process Input Error\n", 32);
            assert(0);
            ramp->base_.output_ = 0;
            return;
        }
        ramp->is_wired_ = 1;
    }

    signal_t input = *ramp->input_;
    signal_t rise_step = *ramp->rise_step_;
    signal_t fall_step = *ramp->fall_step_;

    rise_step = rise_step > 0 ? rise_step : -rise_step;
    fall_step = fall_step > 0 ? fall_step : -fall_step;

    if(input > ramp->base_.output_)
    {
        signal_t diff = input - ramp->base_.output_;
        signal_t step = diff < rise_step ? diff : rise_step;
        ramp->base_.output_ += step;
    }
    else if(input < ramp->base_.output_)
    {
        signal_t diff = ramp->base_.output_ - input;
        signal_t step = diff < fall_step ? diff : fall_step;
        ramp->base_.output_ -= step;
    }
}

void RampInjector_Init(void *self)
{
    RampInjector_t *ramp = (RampInjector_t *)self;

    ramp->rise_step_static_ = 0;
    ramp->fall_step_static_ = 0;

    ramp->input_ = NULL;
    ramp->rise_step_ = &ramp->rise_step_static_;
    ramp->fall_step_ = &ramp->fall_step_static_;

    ramp->base_.Process = RampInjector_Process;
    ramp->base_.Connect = RampInjector_Connect;
    ramp->base_.SetStaticParam = RampInjector_SetStaticParam;
    ramp->base_.type_ = MODULE_RAMP_INJECTOR;
    ramp->base_.output_ = 0;
    ramp->is_wired_ = 0;

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"RampInjector_Init Success\n", 27);
}

