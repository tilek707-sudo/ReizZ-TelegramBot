from database import SessionLocal
from database.models import User, Transaction, Transfer, GroupMember
from datetime import datetime, timedelta
import config

class EconomyService:
    
    @staticmethod
    def get_or_create_user(telegram_id, username=None, first_name=None):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username or "User",
                    first_name=first_name or "User",
                    balance=0
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        finally:
            db.close()
    
    @staticmethod
    def get_user(telegram_id):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.telegram_id == telegram_id).first()
        finally:
            db.close()
    
    @staticmethod
    def get_user_by_id(user_id):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    @staticmethod
    def add_balance(telegram_id, amount, transaction_type="MANUAL", description=""):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.balance += amount
                if amount > 0:
                    user.total_won += amount
                else:
                    user.total_lost += abs(amount)
                
                transaction = Transaction(
                    user_id=user.id,
                    transaction_type=transaction_type,
                    amount=amount,
                    description=description
                )
                db.add(transaction)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def transfer_coins(from_telegram_id, to_telegram_id, amount):
        db = SessionLocal()
        try:
            from_user = db.query(User).filter(User.telegram_id == from_telegram_id).first()
            to_user = db.query(User).filter(User.telegram_id == to_telegram_id).first()
            
            if not from_user or not to_user:
                return False, "Пользователь не найден"
            
            if from_user.id == to_user.id:
                return False, "Нельзя переводить самому себе"
            
            if from_user.balance < amount:
                return False, "Недостаточно монет"
            
            from_user.balance -= amount
            to_user.balance += amount
            
            from_user.total_transferred += amount
            from_user.max_transferred = max(from_user.max_transferred, amount)
            
            to_user.total_received += amount
            to_user.max_received = max(to_user.max_received, amount)
            
            transfer = Transfer(
                from_user_id=from_user.id,
                to_user_id=to_user.id,
                amount=amount
            )
            
            tx1 = Transaction(
                user_id=from_user.id,
                transaction_type="TRANSFER_OUT",
                amount=-amount,
                description=f"Перевод пользователю {to_user.username}"
            )
            
            tx2 = Transaction(
                user_id=to_user.id,
                transaction_type="TRANSFER_IN",
                amount=amount,
                description=f"Получено от {from_user.username}"
            )
            
            db.add(transfer)
            db.add(tx1)
            db.add(tx2)
            db.commit()
            return True, "Успешно"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()
    
    @staticmethod
    def get_daily_bonus(telegram_id):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False, "Пользователь не найден"
            
            now = datetime.utcnow()
            if user.last_bonus_date:
                next_bonus = user.last_bonus_date + timedelta(hours=config.BONUS_COOLDOWN_HOURS)
                if now < next_bonus:
                    remaining = next_bonus - now
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    return False, f"⏳ Бонус будет доступен через {hours}ч {minutes}м."
            
            user.balance += config.DAILY_BONUS
            user.last_bonus_date = now
            
            transaction = Transaction(
                user_id=user.id,
                transaction_type="BONUS",
                amount=config.DAILY_BONUS,
                description="Ежедневный бонус"
            )
            db.add(transaction)
            db.commit()
            
            return True, f"🎁 Вы получили {config.DAILY_BONUS}🪙\n\nБаланс: {user.balance}🪙"
        finally:
            db.close()
    
    @staticmethod
    def get_user_history(telegram_id, limit=10):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return []
            
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user.id
            ).order_by(Transaction.created_at.desc()).limit(limit).all()
            
            return transactions
        finally:
            db.close()
