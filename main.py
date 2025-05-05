# main.py - 主文件，启动机器人

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.commands import start, help_command, menu_command, reset_command, random_command, admin_stats
from bot.handlers import button_callback, handle_message
from database.models import init_database
from config import TELEGRAM_TOKEN, DB_PATH

def main() -> None:
    """主函数"""
    # 初始化数据库
    init_database(DB_PATH)
    
    # 创建应用
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # 添加处理程序
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("random", random_command))
    application.add_handler(CommandHandler("admin_stats", admin_stats))  # 管理员统计命令
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 运行机器人
    print("机器人已启动，数据库记录功能已激活...")
    application.run_polling()

if __name__ == "__main__":
    main()
