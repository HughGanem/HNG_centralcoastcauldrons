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
        potion_result = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(quantity) AS potion_quantity
            FROM potion_ledger;
            """
        )).first()

        ml_result = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(red_ml + green_ml + blue_ml + dark_ml) AS total_ml
            FROM ml_ledger;
            """
        )).first()

        gold_result = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(gold) AS gold_cost
            FROM gold_ledger;
            """
        )).first()

    potion_amount = potion_result.potion_quantity
    ml_amount = ml_result.total_ml
    gold_amount = gold_result.gold_cost

    
    if (potion_amount is None):
        potion_amount = 0
    
    if (ml_amount is None):
        ml_amount = 0

    if (gold_amount is None):
        gold_amount = 0
    

    return {"number_of_potions": potion_amount, "ml_in_barrels": ml_amount, "gold": gold_amount}

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