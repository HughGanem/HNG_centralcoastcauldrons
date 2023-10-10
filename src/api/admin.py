import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    update_red_potions = "UPDATE global_inventory SET num_red_potions = 0;" 
    update_red_ml = "UPDATE global_inventory SET num_red_ml = 0;" 
    
    update_green_potions = "UPDATE global_inventory SET num_green_potions = 0;" 
    update_green_ml = "UPDATE global_inventory SET num_green_ml = 0;" 
    
    update_blue_potions = "UPDATE global_inventory SET num_blue_potions = 0;" 
    update_blue_ml = "UPDATE global_inventory SET num_blue_ml = 0;" 
    
    update_gold = "UPDATE global_inventory SET gold = 100;" 

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(update_red_potions))
        connection.execute(sqlalchemy.text(update_red_ml))

        connection.execute(sqlalchemy.text(update_green_potions))
        connection.execute(sqlalchemy.text(update_green_ml))

        connection.execute(sqlalchemy.text(update_blue_potions))
        connection.execute(sqlalchemy.text(update_blue_ml))

        connection.execute(sqlalchemy.text(update_gold))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """
    return {
        "shop_name": "Hugh's Hoppin' Potions",
        "shop_owner": "Hugh",
    }

