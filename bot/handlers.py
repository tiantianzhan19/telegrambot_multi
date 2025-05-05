# bot/handlers.py - 消息处理功能

import time
from telegram import Update
from telegram.ext import ContextTypes
from bot.personalities import BOT_PERSONALITIES, determine_bot_to_use
from database.operations import record_user, record_interaction, update_analytics
from utils.openai_client import get_ai_response
from utils.logger import logger
from config import MAX_HISTORY_LENGTH

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理按钮回调"""
    query = update.callback_query
    user = query.from_user
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    await query.answer()
    
    if query.data.startswith('select_'):
        bot_id = query.data.replace('select_', '')
        if bot_id in BOT_PERSONALITIES:
            context.user_data['current_bot'] = bot_id
            bot_info = BOT_PERSONALITIES[bot_id]
            await query.edit_message_text(
                f"✅ 已选择 {bot_info['emoji']} {bot_info['name']} ({bot_id})\n\n"
                f"现在你可以开始对话了！"
            )
    elif query.data == 'reset_history':
        if 'history' in context.user_data:
            context.user_data['history'] = []
        await query.edit_message_text("🔄 对话历史已重置！你可以开始新的对话了。")
    elif query.data == 'help':
        help_text = (
            "📖 <b>使用指南</b>\n\n"
            "直接发送消息与当前选择的机器人对话\n\n"
            "<b>可用命令:</b>\n"
            "/start - 重新开始对话\n"
            "/menu - 显示此菜单\n"
            "/help - 显示详细帮助\n"
            "/reset - 清除对话历史\n"
            "/random - 随机选择机器人\n"
        )
        await query.edit_message_text(help_text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理文本消息"""
    start_time = time.time()
    
    user = update.message.from_user
    user_text = update.message.text
    
    # 记录/更新用户信息
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    # 初始化用户数据
    if 'history' not in context.user_data:
        context.user_data['history'] = []
    if 'current_bot' not in context.user_data:
        context.user_data['current_bot'] = "Bot1"
    
    # 确定使用哪个机器人回复
    bot_id = determine_bot_to_use(user_text, context.user_data['current_bot'])
    context.user_data['current_bot'] = bot_id  # 更新当前机器人
    bot_info = BOT_PERSONALITIES[bot_id]
    
    # 添加用户消息到历史
    context.user_data['history'].append({"role": "user", "content": user_text})
    
    # 限制历史长度以避免超出API限制
    if len(context.user_data['history']) > MAX_HISTORY_LENGTH:
        context.user_data['history'] = context.user_data['history'][-MAX_HISTORY_LENGTH:]
    
    # 通知用户机器人正在处理
    processing_message = await update.message.reply_text(
        f"{bot_info['emoji']} {bot_info['name']}正在思考..."
    )
    
    try:
        # 构建消息列表，包括系统提示和历史消息
        messages = [{"role": "system", "content": bot_info['personality']}]
        messages.extend(context.user_data['history'])
        
        # 调用OpenAI API
        bot_response = get_ai_response(messages)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 记录交互
        record_interaction(user.id, bot_id, user_text, bot_response, processing_time)
        
        # 更新分析数据
        update_analytics(user.id, bot_id, processing_time)
        
        # 添加机器人回复到历史
        context.user_data['history'].append({"role": "assistant", "content": bot_response})
        
        # 删除"正在思考"消息
        await processing_message.delete()
        
        # 回复用户，带有机器人标识
        await update.message.reply_text(
            f"{bot_info['emoji']} <b>{bot_info['name']}:</b>\n\n{bot_response}",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"与OpenAI API交互出错: {e}")
        await processing_message.delete()
        await update.message.reply_text("抱歉，处理您的请求时出错了。")
