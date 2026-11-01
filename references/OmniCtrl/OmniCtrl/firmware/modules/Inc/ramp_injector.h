/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: ramp injector
********************************************************************************/
#ifndef __RAMP_INJECTOR_H
#define __RAMP_INJECTOR_H

#include "../Inc/control_module.h"

/*-----------------------------------enum------------------------------------*/
typedef enum{
    RAMPINJECT_PORT_INPUT = 0,
    RAMPINJECT_PORT_RISE_STEP,
    RAMPINJECT_PORT_FALL_STEP,
} RampInjector_Ports;

/*-----------------------------------struct-----------------------------------*/
typedef struct{
    ControlModule_t base_;

    signal_t rise_step_static_;
    signal_t fall_step_static_;

    signal_t *input_;
    signal_t *rise_step_;
    signal_t *fall_step_;

    char is_wired_;
} RampInjector_t;

/*-----------------------------------api-----------------------------------*/
void RampInjector_Init(void *self);

#endif // __RAMP_INJECTOR_H

