/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-08-24 12:04
* @version: v1.0.0
* @description:
********************************************************************************/
#ifndef OLED_H_
#define OLED_H_

#include "bsp_gpio.h"
#include "bsp_spi.h"
#include "bsp_interface.h"


/*-----------------------------------宏定义-----------------------------------*/
#define OLED_CMD  0	//写命令
#define OLED_DATA 1	//写数据


/*-----------------------------------类型定义-----------------------------------*/
typedef struct{
    BSP_SPIx_t SPIx_;
    BSP_GPIO_Port_t RES_Port_;
    BSP_GPIO_Pin_t RES_Pin_;
    BSP_GPIO_Port_t DC_Port_;
    BSP_GPIO_Pin_t DC_Pin_;
    uint8_t GRAM_[72][5];
    uint16_t Width_;
    uint16_t Height_;
}OLED_t;

/*-----------------------------------变量声明-----------------------------------*/
extern OLED_t oled;


/*-----------------------------------函数声明-----------------------------------*/
void OLED_Init(OLED_t *oled);
void OLED_ClearPoint(OLED_t *oled,uint8_t x,uint8_t y);
void OLED_ColorTurn(OLED_t *oled,uint8_t i);
void OLED_DisplayTurn(OLED_t *oled,uint8_t i);
void OLED_DisPlay_On(OLED_t *oled);
void OLED_DisPlay_Off(OLED_t *oled);
void OLED_Refresh(OLED_t *oled);
void OLED_Clear(OLED_t *oled);
void OLED_DrawPoint(OLED_t *oled,uint8_t x,uint8_t y,uint8_t t);
void OLED_DrawLine(OLED_t *oled,uint8_t x1,uint8_t y1,uint8_t x2,uint8_t y2,uint8_t mode);
void OLED_DrawCircle(OLED_t *oled,uint8_t x,uint8_t y,uint8_t r);
void OLED_ShowChar(OLED_t *oled,uint8_t x,uint8_t y,uint8_t chr,uint8_t size1,uint8_t mode);
void OLED_ShowString(OLED_t *oled,uint8_t x,uint8_t y,uint8_t *chr,uint8_t size1,uint8_t mode);
void OLED_ShowNum(OLED_t *oled,uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t size1,uint8_t mode);

#endif
