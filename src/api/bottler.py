import sqlalchemy
import random
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    total_potions = 0

    for potion in potions_delivered:
        red_ml += (potion.quantity * potion.potion_type[0])
        green_ml += (potion.quantity * potion.potion_type[1])
        blue_ml += (potion.quantity * potion.potion_type[2])
        dark_ml += (potion.quantity * potion.potion_type[3])
        total_potions += potion.quantity
        
        with db.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE potions
                    SET quantity = quantity + :quantity
                    WHERE potion_type = :potion_type
                    """),
                    [{"quantity" : potion.quantity, "potion_type" : "[" + ", ".join(map(str, potion.potion_type)) + "]"}])

    
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                num_red_ml = num_red_ml - :red_ml,
                num_green_ml = num_green_ml - :green_ml,
                num_blue_ml = num_blue_ml - :blue_ml,
                num_dark_ml = num_dark_ml - :dark_ml;
                """), 
            [{"total_potions" : total_potions, "red_ml" : red_ml, "green_ml" : green_ml, "blue_ml" : blue_ml, "dark_ml" : dark_ml}]
        )

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        columns = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory;")).first()
    red_ml = columns.num_red_ml
    green_ml = columns.num_green_ml
    blue_ml = columns.num_blue_ml

    potion_types = [[50, 50, 0, 0], [50, 0, 50, 0], [0, 50, 50, 0], [100, 0, 0, 0], [0, 100, 0, 0], [0, 0, 100, 0]]
    quantity = [0, 0, 0, 0, 0, 0]

    while (((red_ml // 50) + (green_ml // 50) + (blue_ml // 50)) > 1):
        if (red_ml >= 50 and green_ml >= 50):
            quantity[0] = quantity[0] + 1
            red_ml -= 50
            green_ml -= 50

        if (red_ml >= 50 and blue_ml >= 50):
            quantity[1] = quantity[1] + 1
            red_ml -= 50
            blue_ml -= 50

        if (green_ml >= 50 and blue_ml >= 50):
            quantity[2] = quantity[2] + 1
            red_ml -= 50
            blue_ml -= 50

        if (red_ml >= 100):
            quantity[3] = quantity[3] + 1
            red_ml -= 100
        
        if (green_ml >= 100):
            quantity[4] = quantity[3] + 1
            green_ml -= 100
        
        if (blue_ml >= 100):
            quantity[5] = quantity[3] + 1
            blue_ml -= 100

    return_lst = []
    for i in range(len(potion_types)):
        if quantity[i] != 0:
            return_lst.append(
                {
                    "potion_type": potion_types[i],
                    "quantity": quantity[i]
                }
            )
    return return_lst