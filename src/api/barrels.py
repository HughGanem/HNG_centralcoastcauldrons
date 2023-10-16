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
    print(wholesale_catalog)

    # SELECT INTO DATABASE FOR HOW MUCH GOLD I AHVE
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory;")).first()
    gold = result.gold
    red_ml = result.num_red_ml
    green_ml = result.num_green_ml
    blue_ml = result.num_blue_ml
    dark_ml = result.num_dark_ml


    barrels_SKU = ["", "", "", ""]
    barrels_quantity = [0, 0, 0, 0]
    for barrel in wholesale_catalog:
        if (0 <= gold and gold >= barrel.price):
            if (barrel.potion_type == [1, 0, 0, 0] and red_ml <= 500):
                barrels_SKU[0] = barrel.sku
                barrels_quantity[0] = (barrels_quantity[0] + 1)
                gold -= barrel.price
            elif (barrel.potion_type == [0, 1, 0, 0] and green_ml <= 500):
                barrels_SKU[1] = barrel.sku
                barrels_quantity[1] = (barrels_quantity[1] + 1)
                gold -= barrel.price
            elif (barrel.potion_type == [0, 0, 1, 0] and blue_ml <= 500):
                barrels_SKU[2] = barrel.sku
                barrels_quantity[2] = (barrels_quantity[2] + 1)
                gold -= barrel.price
            elif (barrel.potion_type == [0, 0, 0, 1] and dark_ml <= 500):
                barrels_SKU[3] = barrel.sku
                barrels_quantity[3] = (barrels_quantity[3] + 1)
                gold -= barrel.price
    
    return_lst = []
    for index in range(len(barrels_SKU)):
        if (barrels_quantity[index] != 0 and barrels_SKU[index] != ""):
            return_lst.append(
                {
                "sku": barrels_SKU[index],
                "quantity": barrels_quantity[index]
                }
            )
    if (len(return_lst) == 0):
        print("no barrels")
        return ()
    print(return_lst)
    return return_lst
