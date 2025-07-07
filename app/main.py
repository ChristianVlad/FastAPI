from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
from random import randrange
import psycopg2

import time
from psycopg2.extras import RealDictCursor
from . import models, schemas, utils
from .database import engine, get_db
from sqlalchemy.orm import Session



models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World!"}

@app.get("/posts", response_model=list[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return posts

@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.Post, db: Session = Depends(get_db)):
    new_post = models.Post(**post.dict(exclude_unset=True)) # Use exclude_unset to ignore id if not provided
    db.add(new_post)
    db.commit()
    db.refresh(new_post) # Refresh to get the generated ID and other default values
    return new_post

@app.get("/posts/{id}", response_model=schemas.Post)
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} was not found")
    return post

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} does not exist")

    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.Post, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} does not exist")

    post_query.update(updated_post.dict(exclude_unset=True), synchronize_session=False)
    db.commit()
    db.refresh(post) # Refresh the 'post' object to reflect updated values
    return post



@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.dict()) # Use exclude_unset to ignore id if not provided
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Refresh to get the generated ID and other default values

    return new_user


@app.get('/users/{id}',status_code=status.HTTP_404_NOT_FOUND, response_model=schemas.UserOut)