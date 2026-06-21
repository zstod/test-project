from fastapi import FastAPI, Depends, HTTPException, status
from project.db import start_session
from project.models import UserRead, UserCreate, Users, Target, CreateTarget, Result
from project.auth import create_token, check_token, hash_password, verify_password
from sqlmodel import select

app = FastAPI()

@app.get('/api')
async def read_root():
    return {'status': 'api is running'}


@app.post('/api/register/', response_model=UserRead)
async def regist(user_model: UserCreate, session = Depends(start_session)):
    request = select(Users).where(Users.email == user_model.email)
    result = await session.execute(request)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Пользователь с таким email уже существует')
    hashed_password = hash_password(user_model.password)
    user = Users(email=user_model.email, password=hashed_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@app.post('/api/login/')
async def login(user_model: UserCreate, session = Depends(start_session)):
    request = select(Users).where(Users.email == user_model.email)
    result = await session.execute(request)
    user = result.scalars().first()
    if not user or not verify_password(user_model.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Неверный логин или пароль')
    token = create_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.get('/api/targets/')
async def get_targets(user_id: int = Depends(check_token), session = Depends(start_session)):
    request = select(Target).where(Target.user_id == user_id)
    result = await session.execute(request)
    targets = result.scalars().all()
    return targets

@app.get('/api/targets/{id}')
async def get_target(id: int, user_id: int = Depends(check_token), session = Depends(start_session)):
    request = select(Target).where(Target.id == id, Target.user_id == user_id)
    result = await session.execute(request)
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@app.post('/api/targets/')
async def add_target(target_model: CreateTarget,id: int = Depends(check_token), session = Depends(start_session)):
    target = Target(url=target_model.url,
                    name=target_model.name,
                    description=target_model.description,
                    user_id=id)
    session.add(target)
    await session.commit()
    await session.refresh(target)
    return {'status': 'success'}


@app.delete('/api/targets/{id}')
async def delete_target(id: int, user_id: int = Depends(check_token), session = Depends(start_session)):
    request = select(Target).where(Target.id == id, Target.user_id == user_id)
    result = await session.execute(request)
    delete = result.scalars().first()
    if not delete:
        return {'target': 'not found'}
    await session.delete(delete)
    await session.commit()
    return status.HTTP_204_NO_CONTENT


@app.patch('/api/targets/{id}')
async def active_target(id: int,user_id: int = Depends(check_token), session = Depends(start_session)):
    request = select(Target).where(Target.id == id, Target.user_id == user_id)
    result = await session.execute(request)
    update = result.scalars().first()
    update.is_active = not update.is_active
    session.add(update)
    await session.commit()
    await session.refresh(update)
    return status.HTTP_204_NO_CONTENT


@app.get('/api/results/{id}')
async def get_target_results(id: int,user_id: int = Depends(check_token),  session = Depends(start_session)):
    request = select(Result).where(Result.user_id == user_id, Result.target == id)
    result = await session.execute(request)
    target_result = result.scalars().all()
    return target_result
