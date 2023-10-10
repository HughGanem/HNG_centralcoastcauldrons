import sqlalchemy
from src import database as db
from fastapi import APIRouter


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        number_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory;")).first().num_red_potions
        number_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;")).first().num_green_potions
        number_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory;")).first().num_blue_potions

    return_lst = []

    if (number_red_potions != 0):
        return_lst.append(
        {
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": number_red_potions,
            "price": 1,
            "potion_type": [100, 0, 0, 0],
        })
    
    if (number_green_potions != 0):
        return_lst.append(
        {
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": number_green_potions,
            "price": 1,
            "potion_type": [0, 100, 0, 0],
        })
    
    if (number_blue_potions != 0):
        return_lst.append(
        {
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": number_blue_potions,
            "price": 1,
            "potion_type": [0, 0, 100, 0],
        })
    return return_lst