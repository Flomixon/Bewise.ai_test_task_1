import requests
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models import question


app = FastAPI(
    title='Get Questions'
)


class Item(BaseModel):
    questions_num: int = Field(gt=0)


class Question(BaseModel):
    id: int = None
    question: str = None
    answer: str = None
    created_at: datetime = None


async def exist_question_in_db(
    question_id: int,
    session: AsyncSession
):
    '''Проверка на вхождение элемента в БД'''
    res = await session.execute(
        select(question).where(question.c.id == question_id)
    )
    return res.scalar()


def get_questions(quantity: int):
    '''Получение вопросов от внешнего API'''
    url = f'https://jservice.io/api/random?count={quantity}'
    response = requests.get(url=url)
    if response.ok:
        return response
    elif response.status_code == 404:
        raise HTTPException(
            status_code=503, detail='Упс... Что-то пошло не так!'
        )
    else:
        raise HTTPException(status_code=response.status_code)


async def parse_response(
    response: requests.Response,
    quantity: int,
    session: AsyncSession
):
    '''Преобразование данных от API для добавления в БД'''
    result = []
    id_question = set()
    for row in response:
        exist_in_db = await exist_question_in_db(row['id'], session)
        if row['id'] not in id_question and not exist_in_db:
            di = {}
            id_question.add(row['id'])
            di['id'] = row['id']
            di['question'] = row['question']
            di['answer'] = row['question']
            di['created_at'] = datetime.fromisoformat(row['created_at'][:-1])
            result.append(di)
    if diff := quantity - len(result):
        result += await parse_response(
            get_questions(diff).json(),
            diff,
            session
        )
    return result


@app.router.post('/', response_model=Question)
async def questions_num(
    item: Item,
    session: AsyncSession = Depends(get_async_session)
):
    '''В переменную "questions_num" необходимо передать колличество вопросов
     для записи в БД. Эндпоит возвращает предыдущей сохранённый вопрос для
     викторины. В случае его отсутствия - пустой объект.'''
    query = select(question)
    response = await session.execute(query)
    response = response.all()
    response_question = get_questions(item.questions_num)
    result = await parse_response(
        response_question.json(),
        item.questions_num,
        session
    )
    stmt = insert(question).values(result)
    await session.execute(stmt)
    await session.commit()
    if not response:
        return {}
    response = response[-1]
    return response._asdict()
