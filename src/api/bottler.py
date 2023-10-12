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
        if potions_delivered[i].potion_type == [100, 0, 0, 0]:
            red_potions = potions_delivered[i].quantity
            red_ml = 100 * red_potions
        #green
        elif potions_delivered[i].potion_type == [0, 100, 0, 0]:
            green_potions = potions_delivered[i].quantity
            green_ml = 100 * green_potions
        #blue
        elif potions_delivered[i].potion_type == [0, 0, 100, 0]:
            blue_potions = potions_delivered[i].quantity
            blue_ml = 100 * green_potions

    with db.engine.begin() as connection:
        #red
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                num_red_potions = num_red_potions + :red_potions,
                num_red_ml = num_red_ml - :red_ml,
                num_green_potions = num_green_potions + :green_potions,
                num_green_ml = num_green_ml - :green_ml,
                num_blue_potions = num_blue_potions + :blue_potions,
                num_blue_ml = num_blue_ml - :blue_ml;
                """), 
            [{"red_potions" : red_potions, "red_ml" : red_ml, "green_potions" : green_potions, "green_ml" : green_ml, "blue_potions" : blue_potions, "blue_ml" : blue_ml}]
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