from sqlalchemy import func
from database import get_db, get_current_user
from models import Query as QueryModel, User
from fastapi import FastAPI, Query, Request, Response, Depends, Cookie, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from weather import get_weather, get_place_suggestions

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CITIES = ["Moscow", "Saint Petersburg", "Novosibirsk"]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, response: Response, db: Session = Depends(get_db), user_data: tuple = Depends(get_current_user)):
    user, session_id = user_data
    response.set_cookie(key="session_id", value=session_id)
    city_weather = {}
    for city in CITIES:
        weather_data = await get_weather(city)
        city_weather[city] = weather_data['current']
    return templates.TemplateResponse("index.html", {"request": request, "city_weather": city_weather})


@app.get("/weather", response_class=JSONResponse)
async def get_weather_report(
        city: str = Query(...),
        session_id: str = Header(None, alias="Session_id"),
        db: Session = Depends(get_db)
):
    if session_id is None:
        return JSONResponse(content={"error": "Session ID not provided"}, status_code=400)

    user = db.query(User).filter(User.session_id == session_id).first()
    if user is None:
        print(f"Creating new user with session_id: {session_id}")
        user = User(session_id=session_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    weather_data = await get_weather(city)
    query = db.query(QueryModel).filter(QueryModel.user_id == user.id, QueryModel.city == city).first()
    if query:
        query.count += 1
    else:
        query = QueryModel(user_id=user.id, city=city)
        db.add(query)
    db.commit()
    return JSONResponse(content=weather_data)

@app.get("/autocomplete", response_class=JSONResponse)
async def autocomplete(query: str = Query(...), session_id: str = Header(None)):
    suggestions = await get_place_suggestions(query)
    return JSONResponse(content=suggestions)

@app.get("/stats", response_class=JSONResponse)
async def get_stats(db: Session = Depends(get_db)):
    stats = db.query(QueryModel.city, func.sum(QueryModel.count).label('total')).group_by(QueryModel.city).all()
    return JSONResponse(content={"stats": [{"city": city, "count": count} for city, count in stats]})


@app.get("/history", response_class=JSONResponse)
async def get_user_history(session_id: str = Header(None, alias="Session_id"), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        return JSONResponse(content={"history": []})

    queries = db.query(QueryModel.city).filter(QueryModel.user_id == user.id).all()
    history = [query.city for query in queries]

    return JSONResponse(content={"history": history})
