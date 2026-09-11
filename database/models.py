from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    # Balances
    balance = Column(Float, default=0)
    
    # Statistics
    total_won = Column(Float, default=0)
    total_lost = Column(Float, default=0)
    max_bet = Column(Float, default=0)
    max_win = Column(Float, default=0)
    max_loss = Column(Float, default=0)
    max_transferred = Column(Float, default=0)
    max_received = Column(Float, default=0)
    total_transferred = Column(Float, default=0)
    total_received = Column(Float, default=0)
    
    # Relations
    partner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    marriage_date = Column(DateTime, nullable=True)
    
    # Bonuses
    last_bonus_date = Column(DateTime, nullable=True)
    
    # Roles
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transactions = relationship('Transaction', back_populates='user', foreign_keys='Transaction.user_id')
    roulette_bets = relationship('RouletteBet', back_populates='user')
    bandit_games = relationship('BanditGame', back_populates='user')
    roles = relationship('UserRole', back_populates='user')
    donations = relationship('Donation', back_populates='user')
    

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    telegram_group_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(255))
    added_date = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    roulette_rounds = relationship('RouletteRound', back_populates='group')
    members = relationship('GroupMember', back_populates='group')


class GroupMember(Base):
    __tablename__ = 'group_members'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    joined_date = Column(DateTime, default=datetime.utcnow)
    is_muted = Column(Boolean, default=False)
    mute_until = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    ban_until = Column(DateTime, nullable=True)
    
    group = relationship('Group', back_populates='members')
    user = relationship('User')


class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    transaction_type = Column(String(50))  # ROULETTE_WIN, ROULETTE_LOSS, TRANSFER, BONUS, BANDIT
    amount = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='transactions', foreign_keys=[user_id])


class RouletteRound(Base):
    __tablename__ = 'roulette_rounds'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    
    class Status(enum.Enum):
        WAITING = "WAITING"
        SPINNING = "SPINNING"
        FINISHED = "FINISHED"
        CANCELLED = "CANCELLED"
    
    status = Column(Enum(Status), default=Status.WAITING)
    started_at = Column(DateTime, default=datetime.utcnow)
    bet_closed_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    result = Column(Integer, nullable=True)  # 0-12
    created_at = Column(DateTime, default=datetime.utcnow)
    message_id = Column(Integer, nullable=True)
    
    # Relations
    bets = relationship('RouletteBet', back_populates='round')
    group = relationship('Group', back_populates='roulette_rounds')


class RouletteBet(Base):
    __tablename__ = 'roulette_bets'
    
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('roulette_rounds.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    
    class BetType(enum.Enum):
        RED = "RED"
        BLACK = "BLACK"
        ZERO = "ZERO"
        NUMBER = "NUMBER"
        RANGE = "RANGE"
    
    bet_type = Column(Enum(BetType), nullable=False)
    bet_value = Column(String(50))  # "5", "5-10", "RED", etc
    potential_win = Column(Float, nullable=True)
    actual_win = Column(Float, default=0)
    is_won = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    round = relationship('RouletteRound', back_populates='bets')
    user = relationship('User', back_populates='roulette_bets')


class BanditGame(Base):
    __tablename__ = 'bandit_games'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    bet_amount = Column(Float, nullable=False)
    result = Column(String(50))  # symbols combination
    win_amount = Column(Float)
    coefficient = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='bandit_games')


class Marriage(Base):
    __tablename__ = 'marriages'
    
    id = Column(Integer, primary_key=True)
    user_id_1 = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_id_2 = Column(Integer, ForeignKey('users.id'), nullable=False)
    marriage_date = Column(DateTime, default=datetime.utcnow)


class Donation(Base):
    __tablename__ = 'donations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='donations')


class UserRole(Base):
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role_name = Column(String(50))  # THIEF, POLICE
    acquired_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship('User', back_populates='roles')


class GameHistory(Base):
    __tablename__ = 'game_history'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    game_type = Column(String(50))  # ROULETTE, BANDIT
    result = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class Transfer(Base):
    __tablename__ = 'transfers'
    
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    to_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
