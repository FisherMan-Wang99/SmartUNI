from sqlalchemy import create_engine, Column, Integer, Text, JSON, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# 使用 SQLite，本地文件存储
DATABASE_URL = "sqlite:///./university_recommend.db"  
# ./ 表示存到当前项目目录下，文件名 university_recommend.db

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # SQLite 特殊参数
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class StudentProfile(Base):
    __tablename__ = "student_profile"
    id = Column(Integer, primary_key=True, index=True)
    profile_json = Column(JSON)   # 存用户输入的 profile
    created_at = Column(TIMESTAMP, server_default=func.now())
    recommendations = relationship("RecommendationResult", back_populates="student")


class RecommendationResult(Base):
    __tablename__ = "recommendation_result"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profile.id", ondelete="CASCADE"))
    report = Column(Text)           # 推荐报告
    universities_json = Column(JSON)  # 推荐大学列表
    created_at = Column(TIMESTAMP, server_default=func.now())
    student = relationship("StudentProfile", back_populates="recommendations")


# 创建表
Base.metadata.create_all(bind=engine)
