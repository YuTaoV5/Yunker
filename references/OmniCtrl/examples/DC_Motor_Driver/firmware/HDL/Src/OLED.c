/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-09-06 15:02
* @version: v1.0.0
* @description: OLED显示屏驱动
********************************************************************************/
#include "OLED.h"
#include "OLEDFont.h"
#include "BSP_RTC.h"

OLED_t oled={
    OLED_SPI,
    OLED_RES_PORT,
    OLED_RES_PIN,
    OLED_DC_PORT,
    OLED_DC_PIN,
    OLED_Width,
    OLED_Height,
};

/**
 * @brief OLED写入字节
 * @param oled OLED结构体指针
 * @param dat 要写入的字节数据
 * @param cmd 0: 数据, 1: 命令
 * @return None
 */
static void OLED_WR_Byte(OLED_t *oled,uint8_t dat,uint8_t cmd)
{
	if(cmd)
        BSP_GPIO_SetPin(oled->DC_Port_,oled->DC_Pin_);
	else 
        BSP_GPIO_ResetPin(oled->DC_Port_,oled->DC_Pin_);
    BSP_SPI_Transmit(oled->SPIx_, &dat,1);
	BSP_GPIO_SetPin(oled->DC_Port_,oled->DC_Pin_);
}

/**
 * @brief OLED计算m的n次方
 * @param m 底数
 * @param n 指数
 * @return m的n次方结果
 */
static uint32_t OLED_Pow(uint8_t m,uint8_t n)
{
	uint32_t result=1;
	while(n--)
	{
	  result*=m;
	}
	return result;
}

/**
 * @brief OLED初始化
 * @param oled OLED结构体指针
 * @return None
 */
void OLED_Init(OLED_t *oled)
{
    BSP_GPIO_ResetPin(oled->RES_Port_, oled->RES_Pin_);
    BSP_RTC_Delay_ms(200); // 延时200ms
    BSP_GPIO_SetPin(oled->RES_Port_, oled->RES_Pin_);

    OLED_WR_Byte(oled,0xAE,OLED_CMD); /*display off*/
    OLED_WR_Byte(oled,0xD5,OLED_CMD); /*set osc division*/
    OLED_WR_Byte(oled,0xF0,OLED_CMD);
    OLED_WR_Byte(oled,0xA8,OLED_CMD); /*multiplex ratio*/
    OLED_WR_Byte(oled,0x27,OLED_CMD); /*duty = 1/40*/
    OLED_WR_Byte(oled,0xD3,OLED_CMD); /*set display offset*/
    OLED_WR_Byte(oled,0x00,OLED_CMD);
    OLED_WR_Byte(oled,0x40,OLED_CMD); /*Set Display Start Line */
    OLED_WR_Byte(oled,0x8d,OLED_CMD); /*set charge pump enable*/
    OLED_WR_Byte(oled,0x14,OLED_CMD);
    OLED_WR_Byte(oled,0x20,OLED_CMD); /*Set page address mode*/
    OLED_WR_Byte(oled,0x02,OLED_CMD); /*set lower column address*/
    OLED_WR_Byte(oled,0xA1,OLED_CMD); /*set segment remap*/
    OLED_WR_Byte(oled,0xC8,OLED_CMD); /*Com scan direction*/
    OLED_WR_Byte(oled,0xDA,OLED_CMD); /*set COM pins*/
    OLED_WR_Byte(oled,0x12,OLED_CMD);
    OLED_WR_Byte(oled,0xAD,OLED_CMD); /*Internal IREF Setting*/
    OLED_WR_Byte(oled,0x30,OLED_CMD);
    OLED_WR_Byte(oled,0x81,OLED_CMD); /*contract control*/
    OLED_WR_Byte(oled,0xfF,OLED_CMD); /*128*/
    OLED_WR_Byte(oled,0xD9,OLED_CMD); /*set pre-charge period*/
    OLED_WR_Byte(oled,0x22,OLED_CMD);
    OLED_WR_Byte(oled,0xdb,OLED_CMD); /*set vcomh*/
    OLED_WR_Byte(oled,0x20,OLED_CMD);
    OLED_WR_Byte(oled,0xA4,OLED_CMD); /*Set Entire Display On/Off*/
    OLED_WR_Byte(oled,0xA6,OLED_CMD); /*normal / reverse*/
    OLED_WR_Byte(oled,0x0C,OLED_CMD); /*set lower column address*/
    OLED_WR_Byte(oled,0x11,OLED_CMD); /*set higher column address*/
    OLED_Clear(oled);
    OLED_WR_Byte(oled,0xAF,OLED_CMD); /*display ON*/
}

/**
 * @brief OLED反显
 * @param oled OLED结构体指针
 * @param i 0: 正常显示, 1: 反色显示
 * @return None
 */
void OLED_ColorTurn(OLED_t *oled, uint8_t i)
{
	if(i==0)
	{
		OLED_WR_Byte(oled, 0xA6, OLED_CMD);//正常显示
	}
	else if(i==1)
	{
		OLED_WR_Byte(oled, 0xA7, OLED_CMD);//反色显示
	}
}

/**
 * @brief OLED屏幕旋转180度
 * @param oled OLED结构体指针
 * @param i 0: 正常显示, 1: 旋转180度显示
 * @return None
 */
void OLED_DisplayTurn(OLED_t *oled, uint8_t i)
{
	if(i==0)
	{
		OLED_WR_Byte(oled, 0xC8, OLED_CMD);//正常显示
		OLED_WR_Byte(oled, 0xA1, OLED_CMD);
	}
	else if(i==1)
	{
		OLED_WR_Byte(oled, 0xC0, OLED_CMD);//反转显示
		OLED_WR_Byte(oled, 0xA0, OLED_CMD);
	}
}

/**
 * @brief OLED开启显示
 * @param oled OLED结构体指针
 * @return None
 */
void OLED_DisPlay_On(OLED_t *oled)
{
	OLED_WR_Byte(oled, 0x8D, OLED_CMD);//电荷泵使能
	OLED_WR_Byte(oled, 0x14, OLED_CMD);//开启电荷泵
	OLED_WR_Byte(oled, 0xAF, OLED_CMD);//点亮屏幕
}

/**
 * @brief OLED关闭显示
 * @param oled OLED结构体指针
 * @return None
 */
void OLED_DisPlay_Off(OLED_t *oled)
{
	OLED_WR_Byte(oled, 0x8D, OLED_CMD);//电荷泵使能
	OLED_WR_Byte(oled, 0x10, OLED_CMD);//关闭电荷泵
	OLED_WR_Byte(oled, 0xAE, OLED_CMD);//关闭屏幕
}

/**
 * @brief OLED更新显存到OLED屏幕
 * @param oled OLED结构体指针
 * @return None
 */
void OLED_Refresh(OLED_t *oled)
{
	uint8_t i,n;
	for(i=0;i<5;i++)
	{
		OLED_WR_Byte(oled, 0xb0+i, OLED_CMD); //设置行起始地址
		OLED_WR_Byte(oled, 0x0c, OLED_CMD);   //设置低列起始地址
		OLED_WR_Byte(oled, 0x11, OLED_CMD);   //设置高列起始地址
		for(n=0;n<72;n++)
			OLED_WR_Byte(oled, oled->GRAM_[n][i], OLED_DATA);
	}
}

/**
 * @brief OLED清屏
 * @param oled OLED结构体指针
 * @return None
 */
void OLED_Clear(OLED_t *oled)
{
	uint8_t i,n;
	for(i=0;i<5;i++)
	{
		for(n=0;n<72;n++)
		{
			oled->GRAM_[n][i]=0;//清除所有数据
		}
	}
	OLED_Refresh(oled);//更新显示
}

/**
 * @brief OLED画点
 * @param oled OLED结构体指针
 * @param x 点的横坐标 (0~127)
 * @param y 点的纵坐标 (0~63)
 * @param t 1: 填充点, 0: 清空点
 * @return None
 */
void OLED_DrawPoint(OLED_t *oled, uint8_t x, uint8_t y, uint8_t t)
{
	uint8_t i,m,n;
	i=y/8;
	m=y%8;
	n=1<<m;
	if(t){oled->GRAM_[x][i]|=n;}
	else
	{
		oled->GRAM_[x][i]=~oled->GRAM_[x][i];
		oled->GRAM_[x][i]|=n;
		oled->GRAM_[x][i]=~oled->GRAM_[x][i];
	}
}

/**
 * @brief OLED画线
 * @param oled OLED结构体指针
 * @param x1 线的起点横坐标 (0~127)
 * @param y1 线的起点纵坐标 (0~63)
 * @param x2 线的结束横坐标 (0~127)
 * @param y2 线的结束纵坐标 (0~63)
 * @param mode 1: 填充线, 0: 清空线
 * @return None
 */
void OLED_DrawLine(OLED_t *oled,uint8_t x1,uint8_t y1,uint8_t x2,uint8_t y2,uint8_t mode)
{
	uint16_t t;
	int xerr=0,yerr=0,delta_x,delta_y,distance;
	int incx,incy,uRow,uCol;
	delta_x=x2-x1; //计算坐标增量 
	delta_y=y2-y1;
	uRow=x1;//画线起点坐标
	uCol=y1;
	if(delta_x>0)incx=1; //设置单步方向 
	else if (delta_x==0)incx=0;//垂直线 
	else {incx=-1;delta_x=-delta_x;}
	if(delta_y>0)incy=1;
	else if (delta_y==0)incy=0;//水平线 
	else {incy=-1;delta_y=-delta_x;}
	if(delta_x>delta_y)distance=delta_x; //选取基本增量坐标轴 
	else distance=delta_y;
	for(t=0;t<distance+1;t++)
	{
		OLED_DrawPoint(oled,uRow,uCol,mode);//画点
		xerr+=delta_x;
		yerr+=delta_y;
		if(xerr>distance)
		{
			xerr-=distance;
			uRow+=incx;
		}
		if(yerr>distance)
		{
			yerr-=distance;
			uCol+=incy;
		}
	}
}

/**
 * @brief OLED画圆
 * @param oled OLED结构体指针
 * @param x 圆的圆心横坐标 (0~127)
 * @param y 圆的圆心纵坐标 (0~63)
 * @param r 圆的半径
 * @return None
 */
void OLED_DrawCircle(OLED_t *oled,uint8_t x,uint8_t y,uint8_t r)
{
	int a, b,num;
    a = 0;
    b = r;
    while(2 * b * b >= r * r)
    {
        OLED_DrawPoint(oled,x + a, y - b,1);
        OLED_DrawPoint(oled,x - a, y - b,1);
        OLED_DrawPoint(oled,x - a, y + b,1);
        OLED_DrawPoint(oled,x + a, y + b,1);

        OLED_DrawPoint(oled,x + b, y + a,1);
        OLED_DrawPoint(oled,x + b, y - a,1);
        OLED_DrawPoint(oled,x - b, y - a,1);
        OLED_DrawPoint(oled,x - b, y + a,1);

        a++;
        num = (a * a + b * b) - r*r;//计算画的点离圆心的距离
        if(num > 0)
        {
            b--;
            a--;
        }
    }
}
	
/**
 * @brief OLED在指定位置显示一个字符,包括部分字符
 * @param oled OLED结构体指针
 * @param x 字符的起点横坐标 (0~127)
 * @param y 字符的起点纵坐标 (0~63)
 * @param chr 要显示的字符
 * @param size1 字体大小 6x8/6x12/8x16/12x24
 * @param mode 0: 反色显示, 1: 正常显示
 * @return None
 */
void OLED_ShowChar(OLED_t *oled,uint8_t x,uint8_t y,uint8_t chr,uint8_t size1,uint8_t mode)
{
	uint8_t i,m,temp,size2,chr1;
	uint8_t x0=x,y0=y;
	size1=8; size2=6;
	chr1=chr-' ';  //计算偏移后的值
	for(i=0;i<size2;i++)
	{
		temp=asc2_0806[chr1][i];
		for(m=0;m<8;m++)
		{
			if(temp&0x01)OLED_DrawPoint(oled,x,y,mode);
			else OLED_DrawPoint(oled,x,y,!mode);
			temp>>=1;
			y++;
		}
		x++;
		if((size1!=8)&&((x-x0)==size1/2))
		{x=x0;y0=y0+8;}
		y=y0;
  }
}


/**
 * @brief OLED在指定位置显示一个字符串,包括部分字符
 * @param oled OLED结构体指针
 * @param x 字符串的起点横坐标 (0~127)
 * @param y 字符串的起点纵坐标 (0~63)
 * @param chr 要显示的字符串
 * @param size1 字体大小 6x8/6x12/8x16/12x24
 * @param mode 0: 反色显示, 1: 正常显示
 * @return None
 */
void OLED_ShowString(OLED_t *oled,uint8_t x,uint8_t y,uint8_t *chr,uint8_t size1,uint8_t mode)
{
	while((*chr>=' ')&&(*chr<='~'))//判断是不是非法字符!
	{
		OLED_ShowChar(oled,x,y,*chr,size1,mode);
		if(size1==8)x+=6;
		else x+=size1/2;
		chr++;
  }
}

/**
 * @brief OLED在指定位置显示一个数字
 * @param oled OLED结构体指针
 * @param x 数字的起点横坐标 (0~127)
 * @param y 数字的起点纵坐标 (0~63)
 * @param num 要显示的数字
 * @param len 数字的位数
 * @param size1 字体大小 6x8/6x12/8x16/12x24
 * @param mode 0: 反色显示, 1: 正常显示
 * @return None
 */
void OLED_ShowNum(OLED_t *oled,uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t size1,uint8_t mode)
{
	uint8_t t,temp,m=0;
	if(size1==8)m=2;
	for(t=0;t<len;t++)
	{
		temp=(num/OLED_Pow(10,len-t-1))%10;
		if(temp==0)
		{
			OLED_ShowChar(oled,x+(size1/2+m)*t,y,'0',size1,mode);
		}
		else
		{
			OLED_ShowChar(oled,x+(size1/2+m)*t,y,temp+'0',size1,mode);
		}
  	}
}
