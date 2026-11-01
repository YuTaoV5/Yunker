/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: curve acceleration
********************************************************************************/
#ifndef __CURVE_ACCEL_H
#define __CURVE_ACCEL_H

#include "../Inc/control_module.h"

/*-----------------------------------enum------------------------------------*/
typedef enum{
    CURVEACCEL_PORT_INPUT = 0,
    CURVEACCEL_PORT_ACCEL_GAIN,
    CURVEACCEL_PORT_DECEL_GAIN,
    CURVEACCEL_PORT_MAX_STEP,
} CurveAccel_Ports;

/*-----------------------------------struct-----------------------------------*/
typedef struct{
    ControlModule_t base_;

    signal_t accel_gain_static_;
    signal_t decel_gain_static_;
    signal_t max_step_static_;

    signal_t *input_;
    signal_t *accel_gain_;
    signal_t *decel_gain_;
    signal_t *max_step_;

    char is_wired_;
} CurveAccel_t;

/*-----------------------------------api-----------------------------------*/
void CurveAccel_Init(void *self);

#endif // __CURVE_ACCEL_H

