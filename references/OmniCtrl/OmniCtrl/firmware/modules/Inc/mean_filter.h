/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: mean filter
********************************************************************************/
#ifndef __MEAN_FILTER_H
#define __MEAN_FILTER_H

#include "../Inc/control_module.h"

#define MEANFILTER_WINDOW_MAX 32

/*-----------------------------------enum------------------------------------*/
typedef enum{
    MEANFILTER_PORT_INPUT = 0,
    MEANFILTER_PORT_WINDOW_SIZE,
} MeanFilter_Ports;

/*-----------------------------------struct-----------------------------------*/
typedef struct{
    ControlModule_t base_;

    size_t window_size_static_;

    signal_t *input_;
    size_t *window_size_;

    signal_t buffer_[MEANFILTER_WINDOW_MAX];
    signal_t sum_;
    size_t index_;
    size_t count_;
    size_t active_window_;

    char is_wired_;
} MeanFilter_t;

/*-----------------------------------api-----------------------------------*/
void MeanFilter_Init(void *self);

#endif // __MEAN_FILTER_H

