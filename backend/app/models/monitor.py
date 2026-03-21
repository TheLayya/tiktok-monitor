from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, BigInteger,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    accounts = relationship("MonitorAccount", back_populates="project", cascade="all, delete-orphan")


class MonitorProxy(Base):
    __tablename__ = "monitor_proxies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    proxy_type = Column(SAEnum("socks5", "http", "https", name="proxy_type_enum"), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_global = Column(Boolean, default=False, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    fail_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    last_test_at = Column(DateTime, nullable=True)
    last_test_result = Column(String(50), nullable=True)  # "success" / "failed"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    accounts = relationship("MonitorAccount", back_populates="proxy")


class MonitorAccount(Base):
    __tablename__ = "monitor_accounts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(255), nullable=False)
    nickname = Column(String(255), nullable=True)
    tiktok_id = Column(String(255), nullable=True)
    sec_uid = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    monitor_interval = Column(Integer, default=3600, nullable=False)  # seconds
    use_proxy = Column(Boolean, default=True, nullable=False)  # 默认开启代理
    proxy_id = Column(Integer, ForeignKey("monitor_proxies.id", ondelete="SET NULL"), nullable=True)
    enable_video_monitoring = Column(Boolean, default=True, nullable=False)  # 默认开启视频监控
    follower_count = Column(BigInteger, default=0, nullable=False)
    following_count = Column(BigInteger, default=0, nullable=False)
    like_count = Column(BigInteger, default=0, nullable=False)
    video_count = Column(BigInteger, default=0, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    bio = Column(Text, nullable=True)
    account_created_at = Column(DateTime, nullable=True)  # 账号注册时间
    region = Column(String(10), nullable=True)  # 地区/国家
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="accounts")
    proxy = relationship("MonitorProxy", back_populates="accounts")
    history = relationship("MonitorHistory", back_populates="account", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="account", cascade="all, delete-orphan")


class MonitorHistory(Base):
    __tablename__ = "monitor_history"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("monitor_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    follower_count = Column(BigInteger, default=0, nullable=False)
    following_count = Column(BigInteger, default=0, nullable=False)
    like_count = Column(BigInteger, default=0, nullable=False)
    video_count = Column(BigInteger, default=0, nullable=False)
    check_status = Column(SAEnum("success", "failed", name="check_status_enum"), nullable=False)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    account = relationship("MonitorAccount", back_populates="history")


class MonitorSettings(Base):
    __tablename__ = "monitor_settings"

    id = Column(Integer, primary_key=True, index=True)
    default_interval = Column(Integer, default=3600, nullable=False)  # seconds
    max_concurrent_checks = Column(Integer, default=5, nullable=False)
    request_timeout = Column(Integer, default=30, nullable=False)  # seconds
    default_video_count = Column(Integer, default=20, nullable=False)  # 默认监控视频数量
    site_name = Column(String(100), default="TikTok Monitor", nullable=False)  # 网站名称
    logo_image = Column(Text, nullable=True)  # Logo图片（base64编码）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
