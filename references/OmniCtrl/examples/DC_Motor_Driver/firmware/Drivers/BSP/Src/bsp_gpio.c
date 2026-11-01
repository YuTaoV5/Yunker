/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 0:18
* @version: v1.0.0
* @description: GPIO驱动
-------------------------------------移植说明-------------------------------------
* 1.根据实际芯片引脚数量更改bsp_gpio.h中 ‘BSP_GPIO_Port_t’ 及 ‘BSP_GPIO_Pin_t'枚举、断言
* 2.更改函数 GPIO_TypeDef* BSP_GPIO_GetPort(BSP_GPIO_Port_t port) 以匹配 1中更改
* 3.重写函数
********************************************************************************/
#include "bsp_gpio.h"
#include "gpio.h"

/**
 * @brief: 获取GPIO端口
 * @param: port: GPIO端口
 * @return: GPIO_TypeDef*: GPIO端口指针
 */
static inline GPIO_TypeDef* BSP_GPIO_GetPort(BSP_GPIO_Port_t port)
{
    // 建立端口映射表(索引与BSP_GPIO_Port_t枚举值对应)
    static const GPIO_TypeDef *port_table[] = {
            [BSP_GPIO_PORT_A] = GPIOA,  // 枚举值0 → GPIOA
            [BSP_GPIO_PORT_B] = GPIOB   // 枚举值1 → GPIOB
            // 扩展端口时在此添加(如[BSP_GPIO_PORT_C] = GPIOC)
    };

    // 检查端口枚举值是否在有效范围内
    if (port < sizeof(port_table) / sizeof(port_table[0])) {
        return (GPIO_TypeDef*)port_table[port];
    }
    assert(0);
}

/**
 * @brief: 初始化GPIO
 * @param: None
 * @return: None
 */
void BSP_GPIO_Init(void)
{
    MX_GPIO_Init();
}

/**
 * @brief: 读GPIO引脚
 * @param: GPIOx: GPIO端口(BSP_GPIO_Port_x)
 * @param: GPIO_Pin: GPIO引脚(BSP_GPIO_Pin_x)
 * @return: BSP_GPIO_PinState_t: GPIO引脚状态
 *      @arg BSP_GPIO_Pin_Set: 高电平
 *      @arg BSP_GPIO_Pin_Reset: 低电平
 */
BSP_GPIO_PinState_t BSP_GPIO_ReadPin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin)
{
    return (BSP_GPIO_PinState_t)HAL_GPIO_ReadPin(BSP_GPIO_GetPort(GPIOx), GPIO_Pin);
}

/**
 * @brief: 写GPIO引脚
 * @param: GPIOx: GPIO端口(BSP_GPIO_Port_x)
 * @param: GPIO_Pin: GPIO引脚(BSP_GPIO_Pin_x)
 * @param: PinState: GPIO引脚状态
 *      @arg BSP_GPIO_Pin_Set: 高电平
 *      @arg BSP_GPIO_Pin_Reset: 低电平
 * @return: None
 */
void BSP_GPIO_WritePin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin, BSP_GPIO_PinState_t PinState)
{
    HAL_GPIO_WritePin(BSP_GPIO_GetPort(GPIOx), GPIO_Pin, (GPIO_PinState)PinState);
}

/**
 * @brief: 设置GPIO引脚为高电平
 * @param: GPIOx: GPIO端口(BSP_GPIO_Port_x)
 * @param: GPIO_Pin: GPIO引脚(BSP_GPIO_Pin_x)
 * @return: None
 */
void BSP_GPIO_SetPin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin)
{
    HAL_GPIO_WritePin(BSP_GPIO_GetPort(GPIOx), GPIO_Pin, GPIO_PIN_SET);
}

/**
 * @brief: 设置GPIO引脚为低电平
 * @param: GPIOx: GPIO端口(BSP_GPIO_Port_x)
 * @param: GPIO_Pin: GPIO引脚(BSP_GPIO_Pin_x)
 * @return: None
 */
void BSP_GPIO_ResetPin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin)
{
    HAL_GPIO_WritePin(BSP_GPIO_GetPort(GPIOx), GPIO_Pin, GPIO_PIN_RESET);
}

/**
 * @brief: 翻转GPIO引脚电平
 * @param: GPIOx: GPIO端口(BSP_GPIO_Port_x)
 * @param: GPIO_Pin: GPIO引脚(BSP_GPIO_Pin_x)
 * @return: None
 */
void BSP_GPIO_TogglePin(BSP_GPIO_Port_t GPIOx, BSP_GPIO_Pin_t GPIO_Pin)
{
    HAL_GPIO_TogglePin(BSP_GPIO_GetPort(GPIOx), GPIO_Pin);
}
