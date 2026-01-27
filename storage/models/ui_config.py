"""
[REQ-2.7] Phase 7 用户界面配置表

存储用户的界面配置，包括表格列宽、列顺序等
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from storage.models import Base


class UIConfig(Base):
    """用户界面配置表"""
    __tablename__ = 'ui_configs'

    config_id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    config_key = Column(String(100), unique=True, nullable=False, comment='配置键名')
    config_value = Column(Text, nullable=False, comment='配置值（JSON格式）')
    config_type = Column(String(50), nullable=False, comment='配置类型（table_column, filter, etc）')
    description = Column(String(500), comment='配置描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<UIConfig(config_id={self.config_id}, config_key='{self.config_key}', config_type='{self.config_type}')>"
