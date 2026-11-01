/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2026-03-12 14:50
* @version: v1.0.0
* @description: mean filter
********************************************************************************/
#include "../Inc/mean_filter.h"
#include <string.h>

static char MeanFilter_Connect(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"MeanFilter_Connect Input Error\n", 29);
        assert(0 && "Invalid parameter");
        return 0;
    }

    MeanFilter_t *filter = (MeanFilter_t *)self;
    switch(param_id)
    {
        case MEANFILTER_PORT_INPUT:
            filter->input_ = CtrlModule_Param_Transform(CTRL_PARAM_SIGNAL_T, param).value_.ptr_;
            break;
        case MEANFILTER_PORT_WINDOW_SIZE:
            filter->window_size_ = CtrlModule_Param_Transform(CTRL_PARAM_SIZE_T, param).value_.ptr_;
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"MeanFilter_Connect Input Error\n", 29);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    filter->is_wired_ = 0;
    return 1;
}

static char MeanFilter_SetStaticParam(void *self, char param_id, CtrlModule_Param_t param)
{
    if(self == NULL)
    {
        Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"MeanFilter_SetStaticParam Input Error\n", 36);
        assert(0 && "Invalid parameter");
        return 0;
    }

    MeanFilter_t *filter = (MeanFilter_t *)self;
    switch(param_id)
    {
        case MEANFILTER_PORT_WINDOW_SIZE:
            filter->window_size_static_ = CtrlModule_Param_Transform(CTRL_PARAM_SIZE_T, param).value_.size_t_;
            if(filter->window_size_static_ == 0)
            {
                filter->window_size_static_ = 1;
            }
            break;
        default:
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"MeanFilter_SetStaticParam Input Error\n", 36);
            assert(0 && "Invalid parameter ID");
            return 0;
    }
    filter->is_wired_ = 0;
    return 1;
}

static void MeanFilter_ResetState(MeanFilter_t *filter, size_t window_size)
{
    memset(filter->buffer_, 0, sizeof(filter->buffer_));
    filter->sum_ = 0;
    filter->index_ = 0;
    filter->count_ = 0;
    filter->active_window_ = window_size;
}

static void MeanFilter_Process(void *self)
{
    MeanFilter_t *filter = (MeanFilter_t *)self;

    if(!filter->is_wired_)
    {
        if(filter->input_ == NULL || filter->window_size_ == NULL)
        {
            Control_Log(CONTROL_LOG_ERROR, (uint8_t *)"MeanFilter_Process Input Error\n", 29);
            assert(0);
            filter->base_.output_ = 0;
            return;
        }
        filter->is_wired_ = 1;
    }

    size_t window_size = *filter->window_size_;
    if(window_size == 0)
    {
        window_size = 1;
    }
    else if(window_size > MEANFILTER_WINDOW_MAX)
    {
        window_size = MEANFILTER_WINDOW_MAX;
    }

    if(filter->active_window_ != window_size)
    {
        MeanFilter_ResetState(filter, window_size);
    }

    signal_t sample = *filter->input_;
    if(filter->count_ < filter->active_window_)
    {
        filter->buffer_[filter->index_] = sample;
        filter->sum_ += sample;
        filter->index_ = (filter->index_ + 1) % filter->active_window_;
        filter->count_++;
    }
    else
    {
        filter->sum_ -= filter->buffer_[filter->index_];
        filter->buffer_[filter->index_] = sample;
        filter->sum_ += sample;
        filter->index_ = (filter->index_ + 1) % filter->active_window_;
    }

    if(filter->count_ == 0)
    {
        filter->base_.output_ = 0;
    }
    else
    {
        filter->base_.output_ = filter->sum_ / (signal_t)filter->count_;
    }
}

void MeanFilter_Init(void *self)
{
    MeanFilter_t *filter = (MeanFilter_t *)self;

    filter->window_size_static_ = 1;
    filter->input_ = NULL;
    filter->window_size_ = &filter->window_size_static_;

    filter->base_.Process = MeanFilter_Process;
    filter->base_.Connect = MeanFilter_Connect;
    filter->base_.SetStaticParam = MeanFilter_SetStaticParam;
    filter->base_.type_ = MODULE_MEAN_FILTER;
    filter->base_.output_ = 0;
    filter->is_wired_ = 0;

    MeanFilter_ResetState(filter, 1);

    Control_Log(CONTROL_LOG_INFO, (uint8_t *)"MeanFilter_Init Success\n", 24);
}

