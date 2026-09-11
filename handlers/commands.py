from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.economy import EconomyService
from services.roulette import RouletteService
from database.models import User, Transaction
from database import SessionLocal
import config

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle баланс/б command"""
    user = EconomyService.get_or_create_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    keyboard = [[InlineKeyboardButton("🎁 Бонус 5000🪙", callback_data="get_bonus")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"👤 {user.first_name}\n\nМонеты: {int(user.balance)}🪙"
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle профиль command"""
    
    # Check if replying to someone
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
    else:
        target_user_id = update.effective_user.id
    
    user = EconomyService.get_or_create_user(
        target_user_id,
        update.message.reply_to_message.from_user.username if update.message.reply_to_message else update.effective_user.username,
        update.message.reply_to_message.from_user.first_name if update.message.reply_to_message else update.effective_user.first_name
    )
    
    partner_info = ""
    if user.partner_id:
        db = SessionLocal()
        try:
            partner = db.query(User).filter(User.id == user.partner_id).first()
            if partner:
                partner_info = f"💍 Брак: {partner.first_name}\n"
        finally:
            db.close()
    
    profile_text = f"""👤 {user.first_name}

🆔 ID: {user.id}

{partner_info}

💰 Баланс: {int(user.balance)}🪙
🏆 Выиграно: {int(user.total_won)}🪙
💸 Проиграно: {int(user.total_lost)}🪙

📈 Макс. ставка: {int(user.max_bet)}🪙
🏆 Макс. выигрыш: {int(user.max_win)}🪙

💸 Макс. перевод: {int(user.max_transferred)}🪙
💰 Макс. получено: {int(user.max_received)}🪙"""
    
    await update.message.reply_text(profile_text)

async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle история command"""
    user = EconomyService.get_or_create_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    transactions = EconomyService.get_user_history(update.effective_user.id, limit=20)
    
    if not transactions:
        await update.message.reply_text("📜 История пуста")
        return
    
    history_text = "📜 История операций\n\n"
    for tx in transactions:
        time_str = tx.created_at.strftime("%H:%M:%S")
        
        if tx.transaction_type == "ROULETTE_WIN":
            history_text += f"[{time_str}] выигрыш в рулетку: +{int(tx.amount)}🪙\n"
        elif tx.transaction_type == "ROULETTE_LOSS":
            history_text += f"[{time_str}] проигрыш в рулетку: -{int(abs(tx.amount))}🪙\n"
        elif tx.transaction_type == "TRANSFER_OUT":
            history_text += f"[{time_str}] перевод: {int(abs(tx.amount))}🪙\n"
        elif tx.transaction_type == "TRANSFER_IN":
            history_text += f"[{time_str}] получено: +{int(tx.amount)}🪙\n"
        elif tx.transaction_type == "BONUS":
            history_text += f"[{time_str}] бонус: +{int(tx.amount)}🪙\n"
    
    await update.message.reply_text(history_text)

async def get_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bonus button"""
    success, message = EconomyService.get_daily_bonus(update.effective_user.id)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(message)

async def handle_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show roulette menu"""
    group_id = update.effective_chat.id
    round = RouletteService.create_or_get_round(group_id)
    
    keyboard = [
        [InlineKeyboardButton("1-3", callback_data="bet_range_1_3")],
        [InlineKeyboardButton("4-6", callback_data="bet_range_4_6")],
        [InlineKeyboardButton("7-9", callback_data="bet_range_7_9")],
        [InlineKeyboardButton("10-12", callback_data="bet_range_10_12")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    roulette_text = """🎰 Минирулетка

Угадайте число из:

0💚

1🔴 2⚫️ 3🔴 4⚫️ 5🔴 6⚫️
7🔴 8⚫️ 9🔴 10⚫️ 11🔴 12⚫️

Ставки можно текстом:

1000 на красное
5000 на 12
10000 5-10"""
    
    await update.message.reply_text(roulette_text, reply_markup=reply_markup)
