/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-18 10:47
* @version: v1.0.0
* @description: SPI驱动
-------------------------------------移植说明-------------------------------------
* 1.根据实际启用SPI数量更改bsp_spi.h中 ‘BSP_SPIx_t’ 枚举
* 2.更改函数 SPI_HandleTypeDef* BSP_SPI_GetHandle(BSP_SPIx_t SPIx) 以匹配 1中更改
* 3.重写函数
********************************************************************************/
#include "bsp_spi.h"
#include "spi.h"

/**
 * @brief 获取SPI句柄
 * @param SPIx: SPI外设实例（BSP_SPIx_t）
 * @return SPI_HandleTypeDef*: SPI句柄指针
 */
static inline SPI_HandleTypeDef *BSP_SPI_GetHandle(BSP_SPIx_t SPIx)
{
    // 建立SPI映射表(索引与BSP_SPIx_t枚举值对应)
    static const SPI_HandleTypeDef *spi_handle_table[] = {
            [BSP_SPI1] = &hspi1,  // 枚举值0 → SPI1句柄
            // 扩展端口时在此添加(如[BSP_SPI2] = &hspi2)
    };

    // 检查实例合法性
    if(SPIx < sizeof(spi_handle_table)/sizeof(spi_handle_table[0]))
    {
        return (SPI_HandleTypeDef*)spi_handle_table[SPIx];
    }
    assert(0);  // 无效实例断言
}

/**
 * @brief: 初始化指定SPI外设
 * @param SPIx: SPI外设实例(BSP_SPIx_t)
 * @return: None
 */
void BSP_SPI_Init(BSP_SPIx_t SPIx)
{
    switch (SPIx)
    {
        case BSP_SPI1:
            MX_SPI1_Init();  // SPI1初始化
            break;
        default:
            assert(0);  // 无效实例断言
            break;
    }
}

/**
 * @brief: 通过指定SPI外设发送数据
 * @param SPIx: SPI外设实例(BSP_SPIx_t)
 * @param data: 数据指针
 * @param size: 数据大小(字节)
 * @return: None
 */
void BSP_SPI_Transmit(BSP_SPIx_t SPIx, uint8_t *data, uint16_t size)
{
    assert(data != NULL && size > 0);   // 断言参数合法性
    HAL_StatusTypeDef status = HAL_SPI_Transmit(BSP_SPI_GetHandle(SPIx), data, size, BSP_SPI_TIMEOUT);
    assert(status == HAL_OK);
}

/**
 * @brief: 通过指定SPI外设DMA发送数据
 * @param SPIx: SPI外设实例(BSP_SPIx_t)
 * @param data: 数据指针
 * @param size: 数据大小(字节)
 * @param timeout: 超时时间(ms)
 * @return: None
 */
void BSP_SPI_Transmit_DMA(BSP_SPIx_t SPIx, uint8_t *data, uint16_t size, uint32_t timeout)
{
    assert(data != NULL && size > 0 && timeout > 0);    // 断言参数合法性
    SPI_HandleTypeDef *hspi = BSP_SPI_GetHandle(SPIx);

    // 等待指定SPI外设就绪
    while(HAL_SPI_GetState(hspi) != HAL_SPI_STATE_READY)
    {
        if(--timeout == 0)
        {
            assert(0);  // 触发断言提示超时
            return;
        }
        HAL_Delay(1);  // 降低CPU占用率
    }

    // 启动指定SPI外设的DMA发送
    HAL_StatusTypeDef status = HAL_SPI_Transmit_DMA(hspi, data, size);
    assert(status == HAL_OK);
}
