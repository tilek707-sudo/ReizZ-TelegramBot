#!/usr/bin/env python3
"""
ReizZ - Telegram Game Bot
Main entry point
"""

import logging
import config
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from database import init_db
from handlers.commands import (
    handle_balance, handle_profile, handle_history, 
    get_bonus, handle_roulette
)
from services.economy import EconomyService

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = EconomyService.get_or_create_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    await update.message.reply_text(
        f"🎮 Добро пожаловать в ReizZ!\n\n"
        f"Это игровой бот с рулеткой и множеством других игр.\n\n"
        f"Команды (пишите без /):\n"
        f"б/баланс - ваш баланс\n"
        f"профиль - профиль\n"
        f"история - история операций\n"
        f"рулетка - начать игру\n\n"
        f"Для справки: {config.SUPPORT_CONTACT}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    if update.message.text is None:
        return
    
    text = update.message.text.lower().strip()
    
    # Register user
    EconomyService.get_or_create_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    # Balance commands
    if text in ['б', 'баланс']:
        await handle_balance(update, context)
    
    # Profile command
    elif text == 'профиль':
        await handle_profile(update, context)
    
    # History command
    elif text == 'история':
        await handle_history(update, context)
    
    # Roulette command
    elif text == 'рулетка':
        await handle_roulette(update, context)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    
    if query.data == "get_bonus":
        await get_bonus(update, context)

def main():
    """Start the bot"""
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    logger.info("ReizZ bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
