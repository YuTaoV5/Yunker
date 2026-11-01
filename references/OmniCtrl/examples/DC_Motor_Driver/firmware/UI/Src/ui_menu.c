/********************************************************************************
* @author: Ternura_xiang
* @email: ternura_xiang@foxmail.com
* @date: 2025-10-27 14:10
* @version: v1.0.0
* @description: 菜单显示模块
********************************************************************************/
#include "ui_menu.h"
#include <string.h>

/**
 * @brief 设置当前显示的菜单项
 * @param self 菜单显示实例指针
 * @param item 要设置为当前显示的菜单项指针
 */
static void UI_Menu_Display_Set_Current(void *self, UI_Menu_Item_t *item)
{
    UI_Menu_Display_t *menu = (UI_Menu_Display_t *)self;
    if (item != NULL)
    {
        menu->current_ = item;
        menu->selected_child_ = item->first_child_;
        menu->display_item_start_ = menu->selected_child_;
    }
}

/**
 * @brief 切换到当前菜单项的父项（返回上一级菜单）
 * @param self 菜单显示实例指针
 */
static void UI_Menu_Switch_Parent(void *self)
{
    UI_Menu_Display_t *menu = (UI_Menu_Display_t *)self;
    if (menu->current_->parent_ != NULL)
    {
        // 执行特定的退出函数
        if(menu->current_->exit != NULL)
            menu->current_->exit();
        // 记录当前项的兄弟项ID
        unsigned char curr_sibling_id = menu->current_->sibling_id_;
        // 切换到当前项的父项
        menu->current_ = menu->current_->parent_;
        // 找到刚才设置的子项
        menu->selected_child_ = menu->current_->first_child_;
        while(menu->selected_child_->sibling_id_ != curr_sibling_id)
        {
            menu->selected_child_ = menu->selected_child_->next_sibling_;
        }
        // 执行特定的进入函数
        if(menu->current_->enter != NULL)
            menu->current_->enter();

    }
}

/**
 * @brief 切换到当前菜单项的子项（进入子菜单）
 * @param self 菜单显示实例指针
 */
static void UI_Menu_Switch_Child(void *self)
{
    UI_Menu_Display_t *menu = (UI_Menu_Display_t *)self;
    if (menu->current_->first_child_ != NULL)
    {
        if(menu->current_->exit != NULL)
            menu->current_->exit();
        menu->current_ = menu->selected_child_;
        menu->selected_child_ = menu->current_->first_child_;
        if(menu->current_->enter != NULL)
            menu->current_->enter();
    }
}

/**
 * @brief 切换到当前菜单项的下一项
 * @param self 菜单显示实例指针
 */
static void UI_Menu_Switch_Next(void *self)
{
    UI_Menu_Display_t *menu = (UI_Menu_Display_t *)self;
    if (menu->selected_child_->next_sibling_ != NULL)
    {
        menu->selected_child_ = menu->selected_child_->next_sibling_;
    }
}

/**
 * @brief 显示函数
 * @param self 菜单显示实例指针
 */
static void UI_Menu_Display(void *self)
{
    UI_Menu_Display_t *menu = (UI_Menu_Display_t *)self;
    if (menu->current_ == NULL) return;
    
    // 计算第一行显示的设置项索引
    if(menu->selected_child_->sibling_id_ < menu->line_num_)
        menu->display_item_start_ = menu->current_->first_child_;
    else
    {
        menu->display_item_start_ = menu->selected_child_->prev_sibling_;
        for(char i=2; i<menu->line_num_; i++)
        {
            menu->display_item_start_ = menu->display_item_start_->prev_sibling_;
        }
    }
            
    // 显示当前设置项
    UI_Menu_Item_t *display_item = menu->display_item_start_;
    for(char i = 0; i < menu->line_num_; i++)
    {
        if(i!=0 && display_item->sibling_id_==0) break; // 此时选项不足一页

        sprintf((char *)menu->display_buffer_, "%.10s", display_item->name_);
        menu->show_str(1, i, menu->display_buffer_);
        display_item = display_item->next_sibling_;
    }

    // 显示当前设置项的标识
    // 两种情况：
    // 1. 当前设置项在第一页显示范围内
    // 3. 此时当前设置项在屏幕末尾
    if(menu->display_item_start_->sibling_id_ == 0)
        menu->show_str(0, menu->selected_child_->sibling_id_, "*");
    else
        menu->show_str(0, menu->line_num_ - 1, "*");
}

/**
 * @brief 初始化菜单项
 * @param self 菜单项实例指针
 * @param name 菜单项名称
 * @param parent 菜单项父项指针
 */
void UI_Menu_Item_Init(UI_Menu_Item_t *self, char *name, UI_Menu_Item_t *parent, void *enter, void *exit)
{
    strcpy(self->name_, name);
    self->parent_ = parent;
    self->child_num_ = 0;
    self->first_child_ = NULL;
    self->last_child_ = NULL;
    self->enter = enter;
    self->exit = exit;

    if (self->parent_ != NULL && self->parent_->child_num_ != 0) // 父菜单有子菜单/无父菜单
    {
        // 1. 建立当前菜单(A)与原父菜单的最后一个子菜单(B)的联系
        // (1) 更新A作为B的下一个同级菜单
        self->prev_sibling_ = self->parent_->last_child_;
        // (2) 传递原B的下一个同级菜单给A
        self->next_sibling_ = self->parent_->last_child_->next_sibling_;
        // (3) 更新原B的下一个同级菜单为A
        self->parent_->last_child_->next_sibling_ = self;

        // 2. 建立当前菜单(A)与原父菜单(C)的联系
        // (1) 更新A作为C的最后一个子菜单
        self->parent_->last_child_ = self;
        // (2) 更新C的子菜单数量, 并作为A的同级菜单ID
        self->sibling_id_ = self->parent_->child_num_++;
    }
    else        // 父菜单无子菜单
    {
        // 设置当前菜单(A)的同级菜单
        self->prev_sibling_ = self;
        self->next_sibling_ = self;
        self->sibling_id_ = 0;

        // 若有父菜单，则将当前菜单(A)作为父菜单(C)的第一个子菜单
        if(self->parent_ != NULL)
        {
            self->parent_->first_child_ = self;
            self->parent_->last_child_ = self;
            self->parent_->child_num_ = 1;
        }
    }
}

/**
 * @brief 初始化菜单显示实例
 * @param self 菜单显示实例指针
 * @param line_num 菜单显示行数
 * @param Show_str 显示字符串函数指针
 */
void UI_Menu_Display_Init(UI_Menu_Display_t *self, unsigned char line_num, void *Show_str)
{
    self->line_num_ = line_num;
    self->show_str = Show_str;

    memset(self->display_buffer_, 0, UI_MENU_NAME_MAX_LEN);
    self->current_ = NULL;
    self->selected_child_ = NULL;
    self->display_item_start_ = NULL;
    self->display = UI_Menu_Display;
    self->set_current = UI_Menu_Display_Set_Current;
    self->switch_next = UI_Menu_Switch_Next;
    self->switch_child = UI_Menu_Switch_Child;
    self->switch_parent = UI_Menu_Switch_Parent;
}
