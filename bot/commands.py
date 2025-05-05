# bot/commands.py - 处理机器人命令

from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import get_bot_selection_keyboard
from bot.personalities import BOT_PERSONALITIES
from database.operations import record_user
from database.analytics import get_stats_summary, export_interactions_to_csv
import random
import os
from config import ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/start命令"""
    user = update.message.from_user
    user_first_name = user.first_name
    
    # 记录用户信息
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    await update.message.reply_text(
        f'👋 你好 {user_first_name}！我是一个多人格聊天机器人。\n\n'
        f'你可以直接与我对话，或者使用 /menu 选择特定的机器人人格。\n\n'
        f'输入 /help 获取更多帮助信息。'
    )
    
    # 初始化用户数据
    if 'history' not in context.user_data:
        context.user_data['history'] = []
    if 'current_bot' not in context.user_data:
        context.user_data['current_bot'] = "Bot1"  # 默认使用Bot1

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/help命令"""
    user = update.message.from_user
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    help_text = (
        "📖 <b>使用指南</b>\n\n"
        "直接发送消息与当前选择的机器人对话\n\n"
        "<b>可用命令:</b>\n"
        "/start - 重新开始对话\n"
        "/menu - 显示机器人选择菜单\n"
        "/help - 显示此帮助信息\n"
        "/reset - 清除当前对话历史\n"
        "/random - 随机选择一个机器人人格\n\n"
        "<b>当前可用的机器人人格:</b>\n"
    )
    
    for bot_id, bot_info in BOT_PERSONALITIES.items():
        help_text += f"{bot_info['emoji']} {bot_info['name']} - {bot_id}\n"
    
    current_bot = context.user_data.get('current_bot', "Bot1")
    current_bot_info = BOT_PERSONALITIES[current_bot]
    help_text += f"\n<b>当前正在与 {current_bot_info['emoji']} {current_bot_info['name']} 对话</b>"
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/menu命令 - 显示机器人选择菜单"""
    user = update.message.from_user
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    reply_markup = get_bot_selection_keyboard()
    await update.message.reply_text('请选择想要对话的机器人:', reply_markup=reply_markup)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/reset命令 - 重置对话历史"""
    user = update.message.from_user
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    if 'history' in context.user_data:
        context.user_data['history'] = []
    
    current_bot = context.user_data.get('current_bot', "Bot1")
    current_bot_info = BOT_PERSONALITIES[current_bot]
    
    await update.message.reply_text(
        f"🔄 对话历史已重置！\n\n"
        f"你现在正在与 {current_bot_info['emoji']} {current_bot_info['name']} 对话。"
    )

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/random命令 - 随机选择机器人"""
    user = update.message.from_user
    record_user(user.id, user.username, user.first_name, user.last_name)
    
    bot_ids = list(BOT_PERSONALITIES.keys())
    selected_bot = random.choice(bot_ids)
    context.user_data['current_bot'] = selected_bot
    bot_info = BOT_PERSONALITIES[selected_bot]
    
    await update.message.reply_text(
        f"🎲 随机选择结果: {bot_info['emoji']} {bot_info['name']} ({selected_bot})\n\n"
        f"现在你可以开始与 {bot_info['name']} 对话了！"
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """管理员命令 - 生成并发送数据统计"""
    user_id = update.message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ 对不起，您没有访问此命令的权限。")
        return
    
    # 获取统计数据
    stats = get_stats_summary()
    
    # 生成报告
    report = f"📊 <b>机器人数据统计</b>\n\n"
    report += f"总用户数: {stats['total_users']}\n"
    report += f"今日活跃用户: {stats['active_users_today']}\n"
    report += f"总交互次数: {stats['total_interactions']}\n"
    report += f"平均响应时间: {stats['avg_response_time']:.2f}秒\n\n"
    
    report += "<b>机器人使用情况:</b>\n"
    for bot_id, count in stats['bot_usage']:
        bot_info = BOT_PERSONALITIES.get(bot_id, {"name": bot_id, "emoji": "🤖"})
        usage_percent = count/stats['total_interactions']*100 if stats['total_interactions'] > 0 else 0
        report += f"{bot_info['emoji']} {bot_info['name']}: {count}次 ({usage_percent:.1f}%)\n"
    
    await update.message.reply_text(report, parse_mode='HTML')
    
    # 导出CSV数据
    csv_file = export_interactions_to_csv()
    if csv_file:
        await update.message.reply_document(
            document=open(csv_file, 'rb'),
            filename=csv_file,
            caption="📊 这是所有用户交互的导出数据。"
        )
        os.remove(csv_file)  # 发送后删除文件
