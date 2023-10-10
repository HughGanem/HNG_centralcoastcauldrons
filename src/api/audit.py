import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory;")).first().num_red_potions
        green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;")).first().num_green_potions
        blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory;")).first().num_blue_potions

        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory;")).first().num_red_ml
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory;")).first().num_green_ml
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory;")).first().num_blue_ml
        
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory;")).first().gold


    total_ml = red_ml + green_ml + blue_ml
    total_potions = red_potions + green_potions + blue_potions

    
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
