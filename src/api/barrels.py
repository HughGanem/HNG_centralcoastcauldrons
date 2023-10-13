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
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0

    for barrel in barrels_delivered:
        if (barrel.potion_type == [1, 0, 0, 0]):
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif (barrel.potion_type == [0, 1, 0, 0]):
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif (barrel.potion_type == [0, 0, 1, 0]):
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif (barrel.potion_type == [0, 0, 0, 1]):
            dark_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception("potion type does not exist")
        gold_cost += barrel.price * barrel.quantity

    print(f"gold_cost: {gold_cost}, red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}")
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
            UPDATE global_inventory SET 
            gold = gold - :gold_cost,
            num_red_ml = num_red_ml + :red_ml,
            num_green_ml = num_green_ml + :green_ml,
            num_blue_ml = num_blue_ml + :blue_ml,
            num_dark_ml = num_dark_ml + :dark_ml;
            """),
            [{"gold_cost": gold_cost, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}])
    return "Ok"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Print and return the catalog"""
    return_lst = []

    # SELECT INTO DATABASE FOR HOW MUCH GOLD I AHVE
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory;")).first().gold

    for barrel in wholesale_catalog:
        if (barrel.price) < gold:
            if barrel.potion_type == [1, 0, 0, 0]:
                gold -= (barrel.price)
                current = {
                    "sku" : barrel.sku,
                    "quantity": barrel.quantity
                }
                return_lst.append(current)
            elif barrel.potion_type == [0, 1, 0, 0]:
                gold -= (barrel.price)
                current = {
                    "sku" : barrel.sku,
                    "quantity": barrel.quantity
                }
                return_lst.append(current)
            elif barrel.potion_type == [0, 0, 1, 0]:
                gold -= (barrel.price * 1)
                current = {
                    "sku" : barrel.sku,
                    "quantity": barrel.quantity
                }
                return_lst.append(current)
            elif barrel.potion_type == [0, 0, 0, 1]:
                gold -= (barrel.price)
                current = {
                    "sku" : barrel.sku,
                    "quantity": barrel.quantity
                }
                return_lst.append(current)
            else:
                raise Exception("Barrel doesn't exist")
        else:
            
            raise Exception("Not enough gold")
    
    return return_lst
