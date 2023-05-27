from sqlalchemy import Column, DateTime, Integer, MetaData, Table, Text


metadata = MetaData()


question = Table(
    'question',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('question', Text, nullable=False),
    Column('answer', Text, nullable=False),
    Column('created_at', DateTime, nullable=False)
)
