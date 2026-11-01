[TOC]
# 一、项目介绍
本项目基于STM32CubeMX生成工程基础搭建，在此基础上，项目目录如下：
```
├── Algorithms  -> 闭环控制算法
|   ├──bases
│       ├── Inc
│       ├── Src
|   ├──methods
│       ├── Inc
│       ├── Src
|   ├──models
│       ├── Inc
│       ├── Src
|   ├──config_c.py
|   ├──config.json
|   ├──control_core.c/.h
├── APP          -> 应用层
│   ├── Inc
│   ├── Src
├── Core
│   ├── Inc
│   ├── Src
│   ├── Startup
├── Drivers
│   ├── BSP      -> 板级支持包
|       ├──Inc
|       ├──Src
│   ├── CMSIS
│   ├── STM32G4xx_HAL_Driver
├── HDL          -> 硬件描述层
│   ├── Inc
│   ├── Src
├── MDK-ARM
├── .mxproject
├── DC_Motor_Driver.ioc
├── README.md
```
## 1.1 项目架构
* Algorithms：闭环控制算法，包含速度环、位置环等控制算法，用户可在此基础上进行二次开发；
* APP：应用层，包含系统初始化、各模块功能的实现；
* HDL：硬件描述层，包含电机驱动、编码器、OLED等硬件模块的驱动类；
* BSP：板级支持包，包含GPIO、UART、RS485等硬件模块的驱动，是上层代码与HAL库的接口；
* 注：本项目理论上实现对硬件的完全解耦，用户在更换芯片时，只需要修改BSP层的代码，即可实现对新芯片的支持；
## 1.2 开发环境
* IDE：Keil MDK-ARM 5.39
* 编译器：ARM Compiler V6.21
* C标准库：C99
* C++标准库：C++11
* HAL库版本：STM32Cube FW_G4 V1.6.1
* 代码生成工具：STM32CubeMX 6.14.0
* Python版本：3.10
## 1.3 命名规则
* BSP、APP层文件命名为：bsp_xx.c/.h、app_xx.c/.h , 其余直接命名为xx.c/.h
* 函数命名
    * C语言函数命名应采用如下结构：
        * 函数名 = 文件名_功能名
        * 函数名采用驼峰命名法，即第一个单词小写，后续单词首字母大写
        * 当存在相似功能的函数时，可添加一级 `_`，以示区分
        * 例如：BSP_UART_Init()、APP_OLED_Init()
    * C++类命名应采用如下结构：
        * 类名 = 文件名
        * 属性名 = xxx_
        * 方法名 = 功能名
        * 类名及方法名采用驼峰命名法，即第一个单词大写，后续单词首字母大写
        * 例如：OffsetController::SetOffset()
* 枚举、结构体命名应采用如下结构：
    * 枚举、结构体名 = 文件名_xxx_t
    * 枚举类型成员名采用全大写，使用_分隔
    * 结构体成员需以_结尾
    * 未特殊说明采用驼峰命名法，即第一个单词大写，后续单词首字母大写
    * 例如：
        * 枚举类型成员(`4950_Mode_t`)：`A4950_Brake`、`A4950_Coast`
        * 结构体成员(`A4950_t`)：`TIMx_1_`、`Channel_1_`、`Speed_`、`Mode_`
* 常量定义
    * 常量定义采用全大写，使用_分隔
    * 例如：`#define A4950_MAX_SPEED 2000`
* 变量命名
    * 变量命名采用全小写，使用_分隔
    * 例如：`int a4950_speed_1 = 0;`
* 注释
    * 应在函数、结构体、枚举类型、类前添加注释，说明其功能及使用方法
    * 注释采用Doxygen格式
# 二、BSP层
## 2.1 文件及功能
| 文件 | 功能 |
| :---: | :---: |
|bsp_common.c/.h||
|bsp_uart.c/.h|完成HAL库的封装，实现初始化及发送|
|bsp_tim.c/.h|完成HAL库的封装|
|bsp_gpio.c/.h|完成HAL库的封装|
|bsp_rtc.c/.h|完成HAL库的封装|
|bsp_spi.c/.h|完成HAL库的封装|
|bsp_interface.h|定义BSP层与HDL层的接口|

# 三、HDL层
该层是对BSP层的再次封装，实现对硬件的全部功能封装，包括电机驱动、编码器、LED等，并对硬件驱动实例进行声明。
## 3.1 文件及功能
| 文件 | 功能 |
| :---: | :---: |
|A4950.c/.h|A4950电机驱动初始化、速度、模式设置|
|Encoder.c/.h|编码器初始化、读取|
|Motor.c/.h|对电机及编码器进行二次封装，作为最终暴露给上层的接口|
|Flash.c/.h|完成flash读写|
|SysTimer.c/.h|APP层定时器初始化、延时|
|comm.c/.h|通信模块HDL封装|
|key.c/.h|完成按键状态机|
|WS2812.c/.h|LED初始化、颜色设置及刷新|
|GRB888.h|存储GRB888颜色编码|
|log.c/.h|日志初始化，各级别发送函数|
|OLED.c/.h|OLED初始化、字符显示及刷新|
|OLEDFont.h|存储OLED字体编码|

# 四、APP层
本层通过调用HDL层提供的硬件功能，及Algorithm层提供的控制算法，专注于实现业务逻辑和功能组合。
## 4.1 文件及功能
| 文件 | 功能 |
| :---: | :---: |
|app_comm.c/.h|通信逻辑|
|app_main.c/.h|主函数，包含系统循环|
|app_oled.c/.h|OLED显示及菜单功能|
|app_key.c/.h|按键交互逻辑|
|app_log.c/.h|日志逻辑|
|app_system.c/.h|系统参数状态控制接口|

# 五、Algorithm层
该层主要实现用户自定义控制算法的部分，每一个文件作为一个模块，供用户拼接。
## 5.1 文件及功能
```
├── Algorithms
|   ├──bases    -> 基础依赖(数据类型、硬件相关、数学函数等)
│       ├── Inc
│       ├── Src
|   ├──methods    -> 功能实现(节点创建、内存池、连线逻辑等)
│       ├── Inc
│       ├── Src
|   ├──models    -> 控制模块(PID、Offset等)
│       ├── Inc
│       ├── Src
|   ├──config_c.py  -> 根据config.json生成C配置文件
|   ├──config.json  -> 用户配置文件
|   ├──control_core.c/.h -> 算法逻辑、对外接口
```

| 文件 | 功能 |
| :---: | :---: |
|algorithms_math.c/.h|数学库|
|control_comm.c/.h|上位机通信接口(引导模式)|
|control_config.c/.h|用户配置文件(此文件通过脚本生成)|
|control_log.c/.h|日志接口|
|control_types.h|数据类型定义|

| 文件 | 功能 |
| :---: | :---: |
|ctrl_factory.c/.h|模块生成器|
|ctrl_hash.c/.h|哈希表|
|ctrl_pool.c/.h|内存池|
|ctrl_register.c/.h|模块注册|
|ctrl_wiring.c/.h|连线逻辑|

| 文件 | 功能 |
| :---: | :---: |
|control_module.h|模块基类|
|gain_controller.c/.h|增益控制器|
|incremental_pid.c/.h|增量PID|
|limit_controller.c/.h|限幅控制器|
|offset_controller.c/.h|偏移控制器|
|position_pid.c/.h|位置PID|

# 六、移植说明

# 七、写在最后

# 八、修改记录
| 日期 | 版本 | 修改人 | 修改内容 |
| :---: | :---: | :---: | :---: |
| 2025.10 | v1.0 | Ternura_xiang | 初始版本 |
| 2026.1 | v1.1 | Ternura_xiang | 完成基本功能 |