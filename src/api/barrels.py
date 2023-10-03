import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """Check and make the API call"""
    SQL_gold = "SELECT gold FROM global_inventory;" 
    SQL_red_potions = "SELECT num_red_potions FROM global_inventory;" 

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(SQL_gold))
        gold_available = result.first().gold

        result = connection.execute(sqlalchemy.text(SQL_red_potions))
        num_red_potions = result.first().num_red_potions

    gold_cost = barrels_delivered[0].price * barrels_delivered[0].quantity
    red_ml = barrels_delivered[0].ml_per_barrel * barrels_delivered[0].quantity

    if (num_red_potions > 10):
        return "Already have 10+ red potions"
    if (gold_available - gold_cost >= 0):
        update_red_potions = "UPDATE global_inventory SET gold = gold - " + str(gold_cost) + ";"
        update_red_ml = "UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(red_ml) + ";" 

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(update_red_potions))
            connection.execute(sqlalchemy.text(update_red_ml))
        print(barrels_delivered)

        return "OK"
    else:
        return "Not enough gold"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Print and return the catalog"""

    print(wholesale_catalog)

    return [
        {
            "sku": wholesale_catalog[0].sku,
            "quantity": wholesale_catalog[0].quantity,
        }
    ]
