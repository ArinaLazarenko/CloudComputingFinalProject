import logging
import time
import random
import requests
from rich.console import Console

requests_number = 1000

logger = logging.getLogger(__name__)
console = Console()

'''
Description: Generates a SQL query to count the number of records in the 'actor' table.
Outputs: str - The SQL `SELECT` query as a string, designed to return the count of records in the 'actor' table.
'''
def generate_read_query(self):
    return "SELECT count(*) FROM actor;"

'''
Description: Generates a SQL query to insert a new record into the 'actor' table with randomly generated first and last names.
Outputs: str - The SQL `INSERT` query as a string, with randomly generated first and last names for the 'actor' table.
'''
def generate_write_query(self):
    first_name = f"Name{random.randint(1, 1000)}"
    last_name = f"Surname{random.randint(1, 1000)}"
    return f"INSERT INTO actor (first_name, last_name) VALUES ('{first_name}', '{last_name}');"

'''
Description: Sends a POST request with a query and implementation to a specified URL and returns the server's response.
Inputs: 
    query (str) - The query to be sent in the request.
    implementation (str) - The implementation detail or additional information to be sent with the query.
    url (str) - The URL where the query and implementation will be sent.
Outputs: 
    dict - A dictionary containing the response data in JSON format, or an error message if the request fails.
'''
def send_query(self, query: str, implementation: str, url: str):
    try:
        response = requests.post(url, json={"query": query, "implementation": implementation})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

'''
Description: Runs a benchmark to measure the performance of different implementations (direct, random, and ping) 
by sending read and write queries, tracking success rates, and recording execution times and dispersion of reads.
'''
def load_test(self):
    gatekeeper_ip = self.get_public_ip(self.inst_wrapper.instances[5]["InstanceId"])
    url = f"http://{gatekeeper_ip}:5000/query"
    execution_times = {}
    dispersion_of_reads_dict = {}
    
    for implementation in range(1, 4): # 1: direct, 2: random, 3: ping
        dispersion_of_reads = {}
        read_success = 0
        write_success = 0
        print(f"Running benchmark for implementation {implementation}...")
        initial_time = time.time()
        for _ in range(requests_number):
            query = self.generate_read_query()
            result = self.send_query(query, implementation, url)
            if "error" not in result:
                receiver = result["receiver"]
                if receiver in dispersion_of_reads:
                    dispersion_of_reads[receiver] += 1
                else:
                    dispersion_of_reads[receiver] = 1
                read_success += 1
            else:
                print(f"Read error: {result['error']}")
                break

        for _ in range(requests_number):
            query = self.generate_write_query()
            result = self.send_query(query, implementation, url)
            if "error" not in result:
                write_success += 1
            else:
                print(f"Write error: {result['error']}")
                break
            
        execution_times[implementation] = time.time() - initial_time
        dispersion_of_reads_dict[implementation] = dispersion_of_reads
        print(f"Read success: {read_success}/{requests_number}")
        print(f"Write success: {write_success}/{requests_number}")
    
    # output the data to ./output/benchmark_results.txt
    with open("./output/benchmark_results.txt", "w") as f:
        f.write(f"Execution times: {execution_times}\n")
        f.write(f"Dispersion of reads: {dispersion_of_reads_dict}\n")