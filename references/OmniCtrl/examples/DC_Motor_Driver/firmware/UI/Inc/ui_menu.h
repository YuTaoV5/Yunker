/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-27 14:10
* @version: v1.0.0
* @description: 菜单显示模块
********************************************************************************/
#ifndef __UI_MENU_H
#define __UI_MENU_H

#include <stdio.h>

/*-----------------------------------常量定义-----------------------------------*/
#define UI_MENU_NAME_MAX_LEN 10


/*-----------------------------------类型定义-----------------------------------*/
/**
 * @brief 菜单项结构体
 */
typedef struct UI_Menu_Item_t
{
    char name_[UI_MENU_NAME_MAX_LEN];       // 菜单名称
    unsigned char sibling_id_;              // 同级菜单ID
    unsigned char child_num_;               // 子菜单数量
    struct UI_Menu_Item_t *parent_;         // 父菜单指针
    struct UI_Menu_Item_t *first_child_;    // 第一个子菜单指针
    struct UI_Menu_Item_t *last_child_;     // 最后一个子菜单指针
    struct UI_Menu_Item_t *prev_sibling_;   // 上一个同级菜单指针
    struct UI_Menu_Item_t *next_sibling_;   // 下一个同级菜单指针
    void (*enter)(void);
    void (*exit)(void);
}UI_Menu_Item_t;

/**
 * @brief 菜单显示实例结构体
 */
typedef struct
{
    unsigned char line_num_;
    void (*show_str)(unsigned char x, unsigned char y, char *str);

    char display_buffer_[UI_MENU_NAME_MAX_LEN];
    UI_Menu_Item_t *current_;
    UI_Menu_Item_t *selected_child_;
    UI_Menu_Item_t *display_item_start_;
    void (*display)(void *self);
    void (*set_current)(void *self, UI_Menu_Item_t *item);
    void (*switch_next)(void *self);
    void (*switch_child)(void *self);
    void (*switch_parent)(void *self);
}UI_Menu_Display_t;


/*-----------------------------------函数声明-----------------------------------*/
void UI_Menu_Item_Init(UI_Menu_Item_t *self, char *name, UI_Menu_Item_t *parent, void *enter, void *exit);
void UI_Menu_Display_Init(UI_Menu_Display_t *self, unsigned char line_num, void *Show_str);

#endif