from database import SessionLocal
from database.models import RouletteRound, RouletteBet, User, GameHistory, Group
from datetime import datetime
import random
import config

class RouletteService:
    
    @staticmethod
    def create_or_get_round(group_id):
        db = SessionLocal()
        try:
            # Check if group exists
            group = db.query(Group).filter(Group.telegram_group_id == group_id).first()
            if not group:
                group = Group(telegram_group_id=group_id, name=f"Group {group_id}")
                db.add(group)
                db.commit()
                db.refresh(group)
            
            # Get active round
            round = db.query(RouletteRound).filter(
                RouletteRound.group_id == group.id,
                RouletteRound.status == RouletteRound.Status.WAITING
            ).first()
            
            if not round:
                round = RouletteRound(
                    group_id=group.id,
                    status=RouletteRound.Status.WAITING
                )
                db.add(round)
                db.commit()
                db.refresh(round)
            
            return round
        finally:
            db.close()
    
    @staticmethod
    def place_bet(round_id, user_id, amount, bet_type, bet_value):
        db = SessionLocal()
        try:
            round = db.query(RouletteRound).filter(RouletteRound.id == round_id).first()
            user = db.query(User).filter(User.id == user_id).first()
            
            if not round or not user:
                return False, "Ошибка"
            
            if amount < config.MIN_BET:
                return False, f"Минимальная ставка {config.MIN_BET}🪙"
            
            if user.balance < amount:
                return False, "Недостаточно монет"
            
            # Reserve balance
            user.balance -= amount
            
            # Create bet
            bet = RouletteBet(
                round_id=round.id,
                user_id=user.id,
                amount=amount,
                bet_type=bet_type,
                bet_value=bet_value
            )
            
            db.add(bet)
            db.commit()
            
            return True, "Ставка принята"
        finally:
            db.close()
    
    @staticmethod
    def get_round_bets(round_id):
        db = SessionLocal()
        try:
            bets = db.query(RouletteBet).filter(RouletteBet.round_id == round_id).all()
            return bets
        finally:
            db.close()
    
    @staticmethod
    def spin_roulette(round_id):
        db = SessionLocal()
        try:
            round = db.query(RouletteRound).filter(RouletteRound.id == round_id).first()
            if not round:
                return None
            
            result = random.randint(0, 12)
            round.result = result
            round.status = RouletteRound.Status.FINISHED
            round.finished_at = datetime.utcnow()
            
            db.commit()
            
            return result
        finally:
            db.close()
    
    @staticmethod
    def process_bets(round_id):
        db = SessionLocal()
        try:
            round = db.query(RouletteRound).filter(RouletteRound.id == round_id).first()
            bets = db.query(RouletteBet).filter(RouletteBet.round_id == round_id).all()
            
            winners = []
            
            for bet in bets:
                user = db.query(User).filter(User.id == bet.user_id).first()
                if not user:
                    continue
                
                is_won = RouletteService.check_bet_win(bet, round.result)
                
                if is_won:
                    coefficient = RouletteService.get_coefficient(bet.bet_type, bet.bet_value)
                    win_amount = bet.amount * coefficient
                    bet.actual_win = win_amount
                    bet.is_won = True
                    user.balance += win_amount
                    user.total_won += win_amount
                    user.max_win = max(user.max_win, win_amount)
                    winners.append((user.username, win_amount))
                else:
                    user.total_lost += bet.amount
                    user.max_loss = max(user.max_loss, bet.amount)
                
                user.max_bet = max(user.max_bet, bet.amount)
            
            db.commit()
            
            return winners
        finally:
            db.close()
    
    @staticmethod
    def check_bet_win(bet, result):
        if bet.bet_type == RouletteBet.BetType.RED:
            return result in [1, 3, 5, 7, 9, 11]
        elif bet.bet_type == RouletteBet.BetType.BLACK:
            return result in [2, 4, 6, 8, 10, 12]
        elif bet.bet_type == RouletteBet.BetType.ZERO:
            return result == 0
        elif bet.bet_type == RouletteBet.BetType.NUMBER:
            return result == int(bet.bet_value)
        elif bet.bet_type == RouletteBet.BetType.RANGE:
            parts = bet.bet_value.split('-')
            start = int(parts[0])
            end = int(parts[1])
            return start <= result <= end
        
        return False
    
    @staticmethod
    def get_coefficient(bet_type, bet_value):
        if bet_type == RouletteBet.BetType.RED or bet_type == RouletteBet.BetType.BLACK:
            return config.ROULETTE_PAYOUTS.get('RED', 2.0)
        elif bet_type == RouletteBet.BetType.ZERO:
            return config.ROULETTE_PAYOUTS.get('ZERO', 14.0)
        elif bet_type == RouletteBet.BetType.NUMBER:
            return config.ROULETTE_PAYOUTS.get('NUMBER_1', 12.0)
        elif bet_type == RouletteBet.BetType.RANGE:
            parts = bet_value.split('-')
            count = int(parts[1]) - int(parts[0]) + 1
            key = f'RANGE_{count}'
            return config.ROULETTE_PAYOUTS.get(key, 2.0)
        
        return 1.0
    
    @staticmethod
    def cancel_user_bets(round_id, user_id):
        db = SessionLocal()
        try:
            bets = db.query(RouletteBet).filter(
                RouletteBet.round_id == round_id,
                RouletteBet.user_id == user_id
            ).all()
            
            user = db.query(User).filter(User.id == user_id).first()
            
            total_returned = 0
            for bet in bets:
                total_returned += bet.amount
                db.delete(bet)
            
            if user:
                user.balance += total_returned
            
            db.commit()
            return True
        finally:
            db.close()
    
    @staticmethod
    def get_last_results(group_id, limit=20):
        db = SessionLocal()
        try:
            group = db.query(Group).filter(Group.telegram_group_id == group_id).first()
            if not group:
                return []
            
            rounds = db.query(RouletteRound).filter(
                RouletteRound.group_id == group.id,
                RouletteRound.result.isnot(None)
            ).order_by(RouletteRound.finished_at.desc()).limit(limit).all()
            
            return [r.result for r in rounds]
        finally:
            db.close()
