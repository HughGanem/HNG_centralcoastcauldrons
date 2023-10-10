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
    with db.engine.begin() as connection:
        gold_available = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory;")).first().gold
        gold_cost = 0

    for i in range(len(barrels_delivered)):
        if (barrels_delivered[i].potion_type[0] == 100 and barrels_delivered[i].potion_type[1] == 0 and barrels_delivered[i].potion_type[2] == 0 and barrels_delivered[i].potion_type[3] == 0):
            gold_cost = gold_cost + (barrels_delivered[i].price * barrels_delivered[i].quantity)
            red_ml = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity

            if (gold_cost > gold_available):
                return "Not enough gold"
        elif (barrels_delivered[i].potion_type[0] == 0 and barrels_delivered[i].potion_type[1] == 100 and barrels_delivered[i].potion_type[2] == 0 and barrels_delivered[i].potion_type[3] == 0):
            gold_cost = gold_cost + (barrels_delivered[i].price * barrels_delivered[i].quantity)
            green_ml = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity

            if (gold_cost > gold_available):
                return "Not enough gold"
        elif (barrels_delivered[i].potion_type[0] == 0 and barrels_delivered[i].potion_type[1] == 0 and barrels_delivered[i].potion_type[2] == 100 and barrels_delivered[i].potion_type[3] == 0):
            gold_cost = gold_cost + (barrels_delivered[i].price * barrels_delivered[i].quantity)
            blue_ml = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity

            if (gold_cost > gold_available):
                return "Not enough gold"
        else:
            return "Incorrect sku"
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_cost};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {red_ml};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {green_ml};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {blue_ml};"))
    return "Ok"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Print and return the catalog"""
    return_lst = []
    for i in range(len(wholesale_catalog)):
        current = {
                    "sku" : wholesale_catalog[i].sku,
                    "quantity": wholesale_catalog[i].quantity,
                   }
        return_lst.append(current)

    print(wholesale_catalog)

    return return_lst
