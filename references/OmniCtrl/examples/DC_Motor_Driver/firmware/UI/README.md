# UI模块说明
## 一、Menu模块说明
### 1. 模块功能
* 提供菜单显示功能
* 支持多级菜单切换
### 2. 模块架构
#### 2.1 结构体定义
* `UI_Menu_Item_t`：菜单项结构体
* `UI_Menu_Display_t`：菜单显示实例结构体
#### 2.2 函数定义
-> UI_Menu_Item_t
* `UI_Menu_Item_Init`：初始化菜单项

-> UI_Menu_Display_t
* `UI_Menu_Display_Init`：初始化菜单显示实例
* `.display`：显示菜单
* `.set_current`：切换当前显示菜单
* `.switch_next`：切换到下一个菜单项
* `.switch_child`：切换到子菜单（进入选项/设置）
* `.switch_parent`：切换到父菜单（返回上一级/确认）
#### 2.3 使用说明
-> 1. 定义菜单项、菜单显示实例（每一个选项都需要一个实例）
```C
// 菜单显示实例声明
UI_Menu_Display_t UI_Menu;
// 设置菜单实例声明
UI_Menu_Item_t UI_Setting;
UI_Menu_Item_t UI_Setting_ID;
UI_Menu_Item_t UI_Setting_Exit;
// ID子菜单实例声明
UI_Menu_Item_t UI_ID_0;
UI_Menu_Item_t UI_ID_1;
```

-> 2. 初始化菜单项、菜单显示实例
* 调用`UI_Menu_Item_Init`初始化菜单项（实现菜单架构）
* 调用`UI_Menu_Display_Init`初始化菜单显示实例
```C
// 初始化设置菜单
UI_Menu_Item_Init(&UI_Setting, "Setting", NULL, NULL, NULL);
UI_Menu_Item_Init(&UI_Setting_ID, "ID        ", &UI_Setting, APP_OLED_Get_ID, APP_OLED_Set_ID);
UI_Menu_Item_Init(&UI_Setting_Exit, "Exit      ", &UI_Setting, NULL, NULL);

// 初始化ID子菜单
UI_Menu_Item_Init(&UI_ID_0, "0         ", &UI_Setting_ID, NULL, NULL);
UI_Menu_Item_Init(&UI_ID_1, "1         ", &UI_Setting_ID, NULL, NULL);

// 初始化菜单显示
UI_Menu_Display_Init(&UI_Menu, APP_OLED_LINE_NUM, (void *)UI_Show_String);
UI_Menu.set_current(&UI_Menu, &UI_Setting);
```

-> 3. 使用菜单显示实例
* 调用`.display`显示菜单
* 调用`.set_current`切换当前显示菜单
* 调用`.switch_next`切换到下一个菜单项
* 调用`.switch_child`切换到子菜单（进入选项/设置）
* 调用`.switch_parent`切换到父菜单（返回上一级/确认）
#### 2.4 注意事项
* 在使用时，根据需要创建好菜单项结构后，只需要调用显示实例即可。
* 在执行`UI_Menu_Item_Init`函数时，需要根据需要传入`enter`、`exit`函数指针。会在调用`.switch_child`和`.switch_parent`时自动调用。
* 一般情况下，只需要调用显示实例的接口函数即可实现全部功能，不需要直接操作菜单项结构体，但可用作条件判断(如判断当前是否为最深子菜单等)。