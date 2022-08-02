# powerplant-coding-challenge
Calculate how much power each of a multitude of different powerplants need to produce (a.k.a. the production-plan) when the load is given and taking into account the cost of the underlying energy sources (gas, kerosine) and the Pmin and Pmax of each powerplant.


# To run the service

This application is written in ```Python 3.9```

Install the requirements: ```pip install -r requirements.txt```

Run the service:
``` python main.py``` | ```python3 main.py```

Send a POST request to ```localhost:8888/productionplan``` using a payload from the ```example_paylods``` folder.

error log ```production_plan.log```