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
    #SQL I what to execute
    sql_to_execute = "SELECT num_red_potions FROM global_inventory;"  

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        number_red_potions = result.first().num_red_potions
        

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": number_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]