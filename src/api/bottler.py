import sqlalchemy
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
    for i in range(len(potions_delivered)):
        #red potion
        if potions_delivered[i].potion_type[0] == 100 and potions_delivered[0].potion_type[1] == 0 and potions_delivered[i].potion_type[2] == 0 and potions_delivered[i].potion_type[3] == 0:
            red_potions_wanted = potions_delivered[i].quantity
            
            with db.engine.begin() as connection:
                red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory;")).first().num_red_ml

            red_potions_avaiable = red_ml // 100
            if (red_potions_avaiable - red_potions_wanted < 0):
                return "Not enough red ml"
        #green
        elif potions_delivered[i].potion_type[0] == 0 and potions_delivered[i].potion_type[1] == 100 and potions_delivered[i].potion_type[2] == 0 and potions_delivered[i].potion_type[3] == 0:
            green_potions_wanted = potions_delivered[i].quantity

            with db.engine.begin() as connection:
                green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory;")).first().num_green_ml
            
            green_potions_avaiable = green_ml // 100

            if (green_potions_avaiable - green_potions_wanted < 0):
                return "Not enough green ml"
        #blue
        elif potions_delivered[i].potion_type[0] == 0 and potions_delivered[i].potion_type[1] == 0 and potions_delivered[i].potion_type[2] == 100 and potions_delivered[i].potion_type[3] == 0:
            blue_potions_wanted = potions_delivered[i].quantity

            with db.engine.begin() as connection:
                blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory;")).first().num_blue_ml
            
            blue_potions_avaiable = blue_ml // 100

            if (blue_potions_avaiable - blue_potions_wanted < 0):
                return "Not enough blue ml"
        else:
            return "Potion does not exist"

    with db.engine.begin() as connection:
        #red
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions + {red_potions_wanted};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {red_ml};" ))
        #green
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {green_potions_wanted};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {green_ml};" ))
        #blue
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions + {blue_potions_wanted};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - {blue_ml};" ))
    
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
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory;")).first().num_red_ml
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory;")).first().num_green_ml
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory;")).first().num_blue_ml

    possible_number_of_red_poitions = red_ml // 100
    possible_number_of_green_poitions = green_ml // 100
    possible_number_of_blue_poitions = blue_ml // 100

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": possible_number_of_red_poitions,
            },
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": possible_number_of_green_poitions,
            },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": possible_number_of_blue_poitions,
            }
        ]