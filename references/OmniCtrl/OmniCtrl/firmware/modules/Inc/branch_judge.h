/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: branch judge
********************************************************************************/
#ifndef __BRANCH_JUDGE_H
#define __BRANCH_JUDGE_H

#include "../Inc/control_module.h"

/*-----------------------------------enum------------------------------------*/
typedef enum{
    BRANCHJUDGE_PORT_CONDITION = 0,
    BRANCHJUDGE_PORT_TRUE_INPUT,
    BRANCHJUDGE_PORT_FALSE_INPUT,
    BRANCHJUDGE_PORT_THRESHOLD,
    BRANCHJUDGE_PORT_HYSTERESIS,
} BranchJudge_Ports;

/*-----------------------------------struct-----------------------------------*/
typedef struct{
    ControlModule_t base_;

    signal_t threshold_static_;
    signal_t hysteresis_static_;

    signal_t *condition_;
    signal_t *true_input_;
    signal_t *false_input_;
    signal_t *threshold_;
    signal_t *hysteresis_;

    char branch_state_;
    char is_wired_;
} BranchJudge_t;

/*-----------------------------------api-----------------------------------*/
void BranchJudge_Init(void *self);

#endif // __BRANCH_JUDGE_H

