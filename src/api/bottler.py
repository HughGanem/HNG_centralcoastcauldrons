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
    SQL_Red_ML = "SELECT num_red_ml FROM global_inventory;" 

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(SQL_Red_ML))
        red_ml = result.first().num_red_ml

    red_potions_wanted = potions_delivered[0].quantity
    red_potions_avaiable = red_ml // 100

    if (red_potions_avaiable - red_potions_wanted >= 0):
        update_red_potions = "UPDATE global_inventory SET num_red_potions = num_red_potions + " + str(red_potions_wanted) + ";"
        update_red_ml = "UPDATE global_inventory SET num_red_ml = num_red_ml - " + str(red_ml) + ";" 

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(update_red_potions))
            connection.execute(sqlalchemy.text(update_red_ml))

        print(potions_delivered)

        return "OK"
    else:
        return "Not enough ml to make that many potions"

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
    SQL_Red_ML = "SELECT num_red_ml FROM global_inventory;" 

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(SQL_Red_ML))
        red_ml = result.first().num_red_ml

    possible_number_of_red_poitions = red_ml // 100
    if (possible_number_of_red_poitions == 0):
        return "Not enough ml to bottle into potions"
    else:
        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": possible_number_of_red_poitions,
                }
            ]