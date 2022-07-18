from sqlalchemy import Column, Integer, Text

from app.models.db import Base


class FileInfo(Base):
    __tablename__ = "files_info"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    file_id = Column(Text)
    file_path = Column(Text)
    guid_ = Column(Text)
    original_filename = Column(Text)
    extension = Column(Text)
    content_type = Column(Text)
