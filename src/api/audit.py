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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory;")).first()
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text(
            """
            SELECT SUM(quantity) AS total_sum
            FROM potions;
            """
        )).first().total_sum
    
    total_ml = result.num_red_ml + result.num_green_ml + result.num_blue_ml + result.num_dark_ml
    gold = result.gold

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
