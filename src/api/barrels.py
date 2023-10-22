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
    for barrel in barrels_delivered:
        current_red_ml = 0
        current_green_ml = 0
        current_blue_ml = 0
        current_dark_ml = 0

        if (barrel.potion_type == [1, 0, 0, 0]):
            current_red_ml = barrel.ml_per_barrel * barrel.quantity
        elif (barrel.potion_type == [0, 1, 0, 0]):
            current_green_ml = barrel.ml_per_barrel * barrel.quantity
        elif (barrel.potion_type == [0, 0, 1, 0]):
            current_blue_ml = barrel.ml_per_barrel * barrel.quantity
        elif (barrel.potion_type == [0, 0, 0, 1]):
            current_dark_ml = barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception("potion type does not exist")

        with db.engine.begin() as connection:
            transaction_id = connection.execute(sqlalchemy.text(
                """
                INSERT INTO transaction (description) 
                VALUES ('Brought :quantity :potion_type for :price.')
                RETURNING transaction_id;
                """),
                [{"quantity": barrel.quantity, "potion_type": barrel.potion_type, "price": barrel.price}]
                ).scalar_one()
            
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO ml_ledger (transaction_id, gold, red_ml, green_ml, blue_ml, dark_ml) 
                VALUES (:transaction_id, :gold, :red_ml, :green_ml, :blue_ml, :dark_ml);
                """
            ),
            [{"transaction_id": transaction_id, "gold": -barrel.price * barrel.quantity, "red_ml": current_red_ml, "green_ml": current_green_ml, "blue_ml": current_blue_ml, "dark_ml": current_dark_ml}]
            )
    return "Ok"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Print and return the catalog"""
    #print(wholesale_catalog)
    with db.engine.begin() as connection:
        result_potion = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(gold) AS num_gold
            FROM potion_ledger;
            """
        )).first()
    
    potion_gold = result_potion.num_gold
    if (potion_gold is None):
        potion_gold = 0

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
        """SELECT 
        SUM(gold) AS num_gold,
        SUM(red_ml) AS num_red_ml,
        SUM(green_ml) AS num_green_ml,
        SUM(blue_ml) AS num_blue_ml,
        SUM(dark_ml) AS num_dark_ml
        FROM ml_ledger;"""
        )).first()

    gold = result.num_gold + potion_gold
    red_ml = result.num_red_ml
    green_ml = result.num_green_ml
    blue_ml = result.num_blue_ml
    dark_ml = result.num_dark_ml

    return_lst = []
    for barrel in wholesale_catalog:
        quantity = 0
        ml_amount = 0
        while (0 <= gold and barrel.price <= gold and quantity < barrel.quantity and ml_amount <= 500):
            if ((barrel.potion_type == [1, 0, 0, 0] and red_ml > 500) or (barrel.potion_type == [0, 1, 0, 0] and green_ml > 500) or (barrel.potion_type == [0, 0, 1, 0] and blue_ml > 500) or (barrel.potion_type == [0, 0, 0, 1] and dark_ml > 500)):
                break
            
            if (barrel.potion_type == [1, 0, 0, 0]):
                red_ml += barrel.ml_per_barrel
            elif (barrel.potion_type == [0, 1, 0, 0]):
                green_ml += barrel.ml_per_barrel
            elif (barrel.potion_type == [0, 0, 1, 0]):
                blue_ml += barrel.ml_per_barrel
            elif (barrel.potion_type == [0, 0, 0, 1]):
                dark_ml += barrel.ml_per_barrel


            ml_amount += barrel.ml_per_barrel
            quantity += 1
            gold -= barrel.price
        
        if (quantity > 0):
            return_lst.append(
                {
                    "sku": barrel.sku,
                    "quantity": quantity
                }
            )

    if (len(return_lst) == 0):
        print("no barrels")
        return ()
    return return_lst
