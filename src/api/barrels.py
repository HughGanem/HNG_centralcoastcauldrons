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
    gold_cost = 0

    for i in range(len(barrels_delivered)):
        if barrels_delivered[i].potion_type == [100,0,0,0]:
            gold_cost = gold_cost + (barrels_delivered[i].price * barrels_delivered[i].quantity)
            red_ml = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity

        elif barrels_delivered[i].potion_type == [0,100,0,0]:
            gold_cost = gold_cost + (barrels_delivered[i].price * barrels_delivered[i].quantity)
            green_ml = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity

        elif barrels_delivered[i].potion_type == [0,0,100,0]:
            gold_cost = gold_cost + (barrels_delivered[i].price * barrels_delivered[i].quantity)
            blue_ml = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity
        else:
            return "Incorrect sku"
    
    with db.engine.begin() as connection:
        if (gold_cost != 0):
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_cost};"))
        if (red_ml != 0):
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {red_ml};"))
        if (green_ml != 0):
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {green_ml};"))
        if (blue_ml != 0):
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {blue_ml};"))
    return "Ok"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Print and return the catalog"""
    return_lst = []

    # SELECT INTO DATABASE FOR HOW MUCH GOLD I AHVE
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory;")).first().gold

    for i in range(len(wholesale_catalog)):
        if wholesale_catalog[i].price < gold:    
            if wholesale_catalog[i].potion_type == [100,0,0,0]:
                gold -= wholesale_catalog[i].price
                current = {
                    "sku" : wholesale_catalog[i].sku,
                    "quantity": 1
                }
                return_lst.append(current)
            elif wholesale_catalog[i].potion_type == [0,100,0,0]:
                gold -= wholesale_catalog[i].price
                current = {
                    "sku" : wholesale_catalog[i].sku,
                    "quantity": 1
                }
                return_lst.append(current)
            elif wholesale_catalog[i].potion_type == [0,0,100,0]:
                gold -= wholesale_catalog[i].price
                current = {
                    "sku" : wholesale_catalog[i].sku,
                    "quantity": 1
                }
                return_lst.append(current)
    return return_lst
