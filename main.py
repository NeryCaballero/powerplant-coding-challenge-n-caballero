import logging
from flask import Flask, request, jsonify

logging.basicConfig(filename='production_plan.log', level=logging.ERROR)


app = Flask(__name__)

''' The payload provides a list of power plants that needs to be ordered by "order of merit" which is
the lowest cost of production first.
The following function takes the payload, extracts the lists of powerplants
if the power plant type is 'windturbine' and the wind percentage is not 0, it assigns order of merit 1 
if the power plant type is 'windturbine' and the wind percentage IS 0, it assigns order of merit 9999999 (to be at last) 
if the power plant type is 'gasfired' it calculates the cost of production
if the power plant type is 'turbojet' it calculates the cost of production
then a sort is called upon the value of order of merit (less expensive to more expensive)
'''


def get_merit_order(payload):
    power_plants_order_of_merit = []
    for power_plant in payload["powerplants"]:
        if power_plant["type"] == "windturbine":
            if payload["fuels"]["wind(%)"] == 0:
                power_plant["order_of_merit"] = 999999
            else:
                power_plant["order_of_merit"] = 1
        elif power_plant["type"] == "gasfired":
            gas_price = payload["fuels"]["gas(euro/MWh)"] / power_plant["efficiency"]
            power_plant["order_of_merit"] = round(gas_price, 2)
        elif power_plant["type"] == "turbojet":
            kerosine_price = payload["fuels"]["kerosine(euro/MWh)"] / power_plant["efficiency"]
            power_plant["order_of_merit"] = round(kerosine_price, 2)
        else:
            print(f"The following power plant was not recognised : {power_plant['name']}, please check the 'type'.")
        power_plants_order_of_merit.append(power_plant)
    power_plants_order_of_merit.sort(key=lambda x: (x["order_of_merit"]))
    print(power_plants_order_of_merit)
    return power_plants_order_of_merit


''' In this function the variable 'load' stores the amount of power demanded to supply
the variable power_produced keeps track of the power that's generated by each plant in the order of merit
the variable remaining_power_to_reach_load keeps track of the power the needs to still be generated for the next power plant
returns a list of name_of_the_plant and power_to_be_demanded_to_the_plant
'''


def calculate_power_per_power_plant(payload):
    load = payload["load"]
    power_produced = 0
    response = []

    power_plants_order_of_merit = get_merit_order(payload)

    for i in range(len(power_plants_order_of_merit)):
        print(f'--------------------{power_plants_order_of_merit[i]["name"]}---------------------')

        remaining_power_to_reach_load = round(load - power_produced, 2)
        print(f'The remaining power needed is: {remaining_power_to_reach_load} , the next plant to turn on is [{i}] {power_plants_order_of_merit[i]["name"]}')

        if remaining_power_to_reach_load == 0:
            response.append({"name": power_plants_order_of_merit[i]["name"], "p": 0})
            print(f'The remaining power needed is: {remaining_power_to_reach_load} , it is not necessary to turn this power plant: [{i}] {power_plants_order_of_merit[i]["name"]}')

        elif power_plants_order_of_merit[i]["type"] == "windturbine":
            max_power_generated = round((power_plants_order_of_merit[i]["pmax"] / 100) * payload["fuels"]["wind(%)"], 2)
            print(f'max_power_generated by {power_plants_order_of_merit[i]["name"]}: {max_power_generated}')

            if max_power_generated < remaining_power_to_reach_load:
                power_produced += max_power_generated
                response.append({"name": power_plants_order_of_merit[i]["name"], "p": max_power_generated})

            else:
                power_produced += remaining_power_to_reach_load
                response.append({"name": power_plants_order_of_merit[i]["name"], "p": remaining_power_to_reach_load})

            print(f'{max_power_generated} power was produced from {power_plants_order_of_merit[i]["name"]}", total power produced is {power_produced}')

        else:
            max_power_generated = power_plants_order_of_merit[i]["pmax"]

            if max_power_generated < remaining_power_to_reach_load:

                if (remaining_power_to_reach_load - max_power_generated) < power_plants_order_of_merit[i]["pmin"]:

                    max_power_generated = max_power_generated - (power_plants_order_of_merit[i + 1]["pmin"] - (remaining_power_to_reach_load - max_power_generated))
                    power_produced += max_power_generated
                    power_plants_order_of_merit[i]["p"] = max_power_generated
                    response.append({"name": power_plants_order_of_merit[i]["name"], "p": max_power_generated})

                else:
                    power_produced += max_power_generated
                    power_plants_order_of_merit[i]["p"] = max_power_generated
                    response.append({"name": power_plants_order_of_merit[i]["name"], "p": max_power_generated})

            elif remaining_power_to_reach_load >= power_plants_order_of_merit[i]["pmin"]:
                power_produced += remaining_power_to_reach_load
                response.append({"name": power_plants_order_of_merit[i]["name"], "p": remaining_power_to_reach_load})
                print(f'{remaining_power_to_reach_load} power was produced from {power_plants_order_of_merit[i]["name"]}", total power produced is {power_produced}')

            else:
                response.append({"name": power_plants_order_of_merit[i]["name"], "p": 0})

    return response


@app.route('/productionplan', methods=['POST'])
def get_production_plan():
    try:
        payload = request.json
    except Exception as e:
        logging.exception((str(e)))
        return 'Error occurred : ' + str(e)

    response = calculate_power_per_power_plant(payload)
    return jsonify(response)


if __name__ == '__main__':
    app.run(port=8888, debug=True)
