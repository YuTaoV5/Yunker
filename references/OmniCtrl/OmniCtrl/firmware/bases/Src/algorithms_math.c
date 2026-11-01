/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-17 17:35
* @version: v1.0.0
* @description: 数学库
********************************************************************************/
#include "../Inc/algorithms_math.h"

/*
 * @brief 计算信号的绝对值
 * @param in 输入信号
 * @return 信号的绝对值
*/
signal_t algorithms_abs(signal_t in)
{
    // 后续检查是否需要处理最小值溢出问题
    return (signal_t)(in>0 ? in: -in);
}
