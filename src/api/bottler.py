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
    print(potions_delivered)
    red_ml = sum(potion.quantity * potion.potion_type[0] for potion in potions_delivered)
    green_ml = sum(potion.quantity * potion.potion_type[1] for potion in potions_delivered)
    blue_ml = sum(potion.quantity * potion.potion_type[2] for potion in potions_delivered)
    dark_ml = sum(potion.quantity * potion.potion_type[3] for potion in potions_delivered)

    for potion_delivered in potions_delivered:
        with db.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE potions
                    SET quantity = quantity + :additional_potions
                    WHERE red_ml = :red_ml and green_ml = :green_ml and blue_ml = :blue_ml and dark_ml = :dark_ml
                    """),
                    [{"additional_potions" : potion_delivered.quantity, 
                      "red_ml" : potion_delivered.potion_type[0], 
                      "green_ml" : potion_delivered.potion_type[1],
                      "blue_ml" : potion_delivered.potion_type[2],
                      "dark_ml" : potion_delivered.potion_type[3]}])
    
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
            [{"red_ml" : red_ml, "green_ml" : green_ml, "blue_ml" : blue_ml, "dark_ml" : dark_ml}]
        )
    print(potions_delivered)
    print({"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml})
    
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
        columns = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory;")).first()
    red_ml = columns.num_red_ml
    green_ml = columns.num_green_ml
    blue_ml = columns.num_blue_ml
    dark_ml = columns.num_dark_ml

    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("""SELECT * FROM potions ORDER BY potion_id DESC;""")).all()

    return_lst = []
    for potion in potions:
        quantity = potion.quantity
        added_potion = False

        while (red_ml >= potion.red_ml and green_ml >= potion.green_ml and blue_ml >= potion.blue_ml and dark_ml >= potion.dark_ml and quantity <= 4):
            red_ml -= potion.red_ml
            green_ml -= potion.green_ml
            blue_ml -= potion.blue_ml
            dark_ml -= potion.dark_ml
            quantity += 1
            added_potion = True
        
        if (added_potion):
            return_lst.append(
                {
                    "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                    "quantity": quantity
                }
            )
    
    print(return_lst)
    if (len(return_lst) == 0):
        return ()
    return return_lst