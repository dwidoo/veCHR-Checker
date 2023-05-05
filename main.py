# main.py

from fastapi import FastAPI
import yaml
import requests
from web3 import Web3
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta, TH
import time
import pandas as pd
import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

app = FastAPI()

# Params
params_path = "params.yaml"


def read_params(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config


config = read_params(params_path)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/{item_id}")
async def read_item(item_id: int):
    tokenid = int(item_id)
    # CHR Price in USDC
    params = {
        "from": "0x15b2fb8f08E4Ac1Ce019EADAe02eE92AeDF06851",
        "to": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "amount": "1000000000000000000",
    }

    try:
        response = requests.get("https://router.firebird.finance/arbitrum/route", params=params)
        CHR_price = response.json()["maxReturn"]["tokens"]["0x15b2fb8f08e4ac1ce019eadae02ee92aedf06851"]["price"]
    except Exception as e:
        print(e)

    try:
        provider_url = config["data"]["provider_url"]
        w3 = Web3(Web3.HTTPProvider(provider_url))

        abi1 = config["data"]["abi1"]
        contract_address1 = config["data"]["contract_address1"]
        contract_instance1 = w3.eth.contract(address=contract_address1, abi=abi1)

        abi2 = config["data"]["abi2"]
        contract_address2 = config["data"]["contract_address2"]
        contract_instance2 = w3.eth.contract(address=contract_address2, abi=abi2)

        abi3 = config["data"]["abi3"]
        contract_address3 = config["data"]["contract_address3"]
        contract_instance3 = w3.eth.contract(address=contract_address3, abi=abi3)

        # Total Supply
        totalSupply = contract_instance3.functions.balanceOf(contract_address1).call() / 1000000000000000000
        todayDate = datetime.utcnow()
        lastThursday = todayDate + relativedelta(weekday=TH(-1))
        my_time = datetime.min.time()
        my_datetime = datetime.combine(lastThursday, my_time)
        currentepoch = int(my_datetime.replace(tzinfo=timezone.utc).timestamp())
    except Exception as e:
        print(e)

    # Read Data
    try:
        # Balance veCHR
        bal = round(
            contract_instance1.functions.balanceOfNFT(tokenid).call() / 1000000000000000000,
            4,
        )

        # Locked veCHR
        locked = round(
            contract_instance1.functions.locked(tokenid).call()[0] / 1000000000000000000,
            4,
        )

        # Lock End Date
        lockend = time.strftime(
            "%Y-%m-%d",
            time.gmtime(int(contract_instance1.functions.locked(tokenid).call()[1])),
        )

        # Voted Last Epoch
        voted = contract_instance1.functions.voted(tokenid).call()

        # Voted Current Epoch
        votedcurrentepoch = contract_instance2.functions.lastVoted(tokenid).call() > currentepoch
    except Exception as e:
        print(e)
    #return json.dumps({"item_id": item_id,
    #        "Locked CHR": locked,
    #        "veCHR Balance": bal,
    #        "Estimated Value in $": round(CHR_price * locked, 4),
    #        "Lock End Date": lockend,
    #        "Vote Share": round(bal / totalSupply, 4),
    #        "Vote Reset": ["No" if voted == True else "Yes"][0],
    #        "Voted Current Epoch": ["No" if votedcurrentepoch == False else "Yes"][0]
    #        })
    item = {"item_id": item_id,
            "Locked CHR": locked,
            "veCHR Balance": bal,
            "Estimated Value in $": round(CHR_price * locked, 4),
            "Lock End Date": lockend,
            "Vote Share": round(bal / totalSupply, 4),
            "Vote Reset": ["No" if voted == True else "Yes"][0],
            "Voted Current Epoch": ["No" if votedcurrentepoch == False else "Yes"][0]
            }
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

    #return {'item_id': item_id}