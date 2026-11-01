/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: curve acceleration
********************************************************************************/
#include "../Inc/curve_accel.h"
#include "../../bases/Inc/algorithms_math.h"

static char CurveAccel_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CurveAccel_Connect Input Error\n", 29);
        assert(0 && "Invalid parameter");
        return 0;
    }

    CurveAccel_t *curve = (CurveAccel_t *)self;
    switch(param_id)
    {
        case CURVEACCEL_PORT_INPUT:
            curve->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case CURVEACCEL_PORT_ACCEL_GAIN:
            curve->accel_gain_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case CURVEACCEL_PORT_DECEL_GAIN:
            curve->decel_gain_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case CURVEACCEL_PORT_MAX_STEP:
            curve->max_step_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CurveAccel_Connect Input Error\n", 29);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    curve->is_wired_ = 0;
    return 1;
}

static char CurveAccel_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CurveAccel_SetStaticParam Input Error\n", 36);
        assert(0 && "Invalid parameter");
        return 0;
    }

    CurveAccel_t *curve = (CurveAccel_t *)self;
    signal_t temp = 0;
    switch(param_id)
    {
        case CURVEACCEL_PORT_ACCEL_GAIN:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            curve->accel_gain_static_ = temp > 0 ? temp : -temp;
            break;
        case CURVEACCEL_PORT_DECEL_GAIN:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            curve->decel_gain_static_ = temp > 0 ? temp : -temp;
            break;
        case CURVEACCEL_PORT_MAX_STEP:
            temp = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.signal_t_;
            curve->max_step_static_ = temp > 0 ? temp : -temp;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CurveAccel_SetStaticParam Input Error\n", 36);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    curve->is_wired_ = 0;
    return 1;
}

static void CurveAccel_Process(void *self)
{
    CurveAccel_t *curve = (CurveAccel_t *)self;

    if(!curve->is_wired_)
    {
        if(curve->input_ == NULL || curve->accel_gain_ == NULL ||
            curve->decel_gain_ == NULL || curve->max_step_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"CurveAccel_Process Input Error\n", 29);
            assert(0);
            curve->base_.output_ = 0;
            return;
        }
        curve->is_wired_ = 1;
    }

    signal_t input = *curve->input_;
    signal_t error = input - curve->base_.output_;
    if(error == 0)
    {
        return;
    }

    signal_t gain = error > 0 ? *curve->accel_gain_ : *curve->decel_gain_;
    signal_t max_step = *curve->max_step_;

    gain = gain > 0 ? gain : -gain;
    max_step = max_step > 0 ? max_step : -max_step;

    signal_t step = gain * error * algorithms_abs(error);
    if(step > max_step)
    {
        step = max_step;
    }
    else if(step < -max_step)
    {
        step = -max_step;
    }

    if(algorithms_abs(error) <= algorithms_abs(step))
    {
        curve->base_.output_ = input;
    }
    else
    {
        curve->base_.output_ += step;
    }
}

void CurveAccel_Init(void *self)
{
    CurveAccel_t *curve = (CurveAccel_t *)self;

    curve->accel_gain_static_ = 0;
    curve->decel_gain_static_ = 0;
    curve->max_step_static_ = 0;

    curve->input_ = NULL;
    curve->accel_gain_ = &curve->accel_gain_static_;
    curve->decel_gain_ = &curve->decel_gain_static_;
    curve->max_step_ = &curve->max_step_static_;

    curve->base_.Process = CurveAccel_Process;
    curve->base_.Connect = CurveAccel_Connect;
    curve->base_.SetStaticParam = CurveAccel_SetStaticParam;
    curve->base_.type_ = MODULE_CURVE_ACCEL;
    curve->base_.output_ = 0;

    curve->is_wired_ = 0;

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"CurveAccel_Init Success\n", 24);
}

