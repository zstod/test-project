from datetime import datetime, timedelta
from sqlmodel import select
from db import  async_session
from models import Result, Target
from time import perf_counter
import asyncio
import httpx

async def scan(target_id, url, client, asyn):
    time_start = perf_counter()
    try:
        result = await client.get(url, timeout=14, follow_redirects=True)
        status = str(result.status_code)
    except httpx.RequestError:
        status = 'Error'
    time_end = perf_counter()
    time_response = time_end - time_start
    alive = status in ['200', '201', '202', '204', '206', '301', '302', '304' '401', '403']

    async with asyn() as session:
        target = await session.get(Target,target_id)
        if target:
            target.next_check = datetime.now() + timedelta(seconds=60)
            result = Result(target=target_id,
                            user_id=target.user_id,
                            checked_at=datetime.now(),
                            response_speed=time_response,
                            status_code=status,
                            is_up=alive)
            session.add(result)
            session.add(target)
            await session.commit()

async def manager():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                async with async_session() as session:
                    request = select(Target).where(
                        Target.next_check <= datetime.now(),
                        Target.is_active == True
                    )
                    db_result = await session.execute(request)
                    targets = db_result.scalars().all()
                    tasks = [scan(target.id, target.url, client, async_session) for target in targets]
                    if tasks:
                        await asyncio.gather(*tasks)
            except Exception as e:
                print(f'Ошибка: {e}')
            await asyncio.sleep(15)
asyncio.run(manager())
