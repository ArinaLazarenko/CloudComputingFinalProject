# Distributed Database Cluster with Proxy and Gatekeeper Patterns

This project demonstrates the design and implementation of a distributed MySQL database cluster using cloud design patterns, specifically **Proxy** and **Gatekeeper**. The system is deployed on AWS EC2 instances, leveraging dynamic query routing, replication, and enhanced security to ensure scalability, performance, and data protection.

Key features include:
- A **Proxy** to intelligently route database queries across the cluster using three strategies: Direct Hit, Random Distribution, and Customized Distribution.
- A **Gatekeeper** to authenticate and validate requests, acting as a secure interface between external clients and internal systems.
- Automated MySQL setup with replication, user creation, and database benchmarking using **Sysbench**.
- Comprehensive benchmarking to evaluate the performance of various routing strategies.

This project highlights the integration of cloud computing principles with robust software design patterns to create a secure, scalable, and efficient distributed system.


<a id="CloudComputingFinalProject"></a>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#requirements">Requirements</a>
      <a href="#installation">Installation</a>
      <a href="#components">Components</a>
<!--       <ul>
        <li><a href="#mysql-setup">MySQL Setup</a></li>
        <li><a href="#proxy-pattern">Proxy Pattern</a></li>
        <li><a href="#gatekeeper-pattern">Gatekeeper Pattern</a></li>
        <li><a href="#benchmarking">Benchmarking</a></li>
      </ul> -->
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
  </ol>
</details>

## Requirements

- **Python 3.x**: Required to run the Proxy and Gatekeeper implementations.
- **Flask**: Used to create REST APIs for the Proxy, Gatekeeper, and Trusted Host.
- **MySQL Server**: Installed on EC2 instances for database operations.
- **Sysbench**: For benchmarking MySQL performance.
- **Requests**: To handle HTTP requests for routing and health checks.

To install the necessary Python packages, run:
```sh 
pip install flask requests
```
## Installation

1. Clone the repository to your local machine:
```sh 
git clone <repository_url>
cd <repository_directory>
```
2. Create a file named ```vpc_id.txt``` and ```subnet_id.txt``` in the AWS configuration folder ```(/home/.aws/)``` with your VPC ID and Subnet ID, respectively.
3. Ensure that your AWS credentials are configured properly, either by setting environment variables or using the AWS CLI.

## Components

### Globals
- **globals.py:** Contains global variables such as file paths, security group names, and target group names.

### Instance Setup
- **instance_setup.py:** Responsible for creating EC2 instances and security groups. It includes:
    - ```createSecurityGroup(vpc_id, group_name):``` Creates a security group and configures ingress rules.
    - ```createInstance(...):``` Creates an EC2 instance based on specified parameters.
## Usage
1. **Configure AWS Credentials:**
   - Set up your AWS credentials on your local machine using the AWS CLI or environment variables.

2. **Edit the `globals.py` File:**
   - Open the `globals.py` file and fill in the constants with the appropriate relative paths required by your project.

3. **Insert AWS Credentials in the `.aws` File:**
   - Open the `.aws` file and insert your AWS credentials in the following format:
     ```bash
     aws_access_key_id=[INSERT]
     aws_secret_access_key=[INSERT]
     aws_session_token=[INSERT]
     ```

4. **Make the `run_all.sh` Script Executable:**
   - In the terminal, run the following command to give execution permissions to the `run_all.sh` script:
   - 
     ```bash
     chmod +x run_all.sh
     ```

5. **Run the Bash Script:**
   - After making the script executable, run it using the following command:
     ```bash
     ./run_all.sh
     ```

6. **Check the Benchmarking Results:**
   - Once the script has completed running, the benchmarking results will be saved to a file named `benchmark_results.txt`. You can open or review this file for performance data.

## Troubleshooting
- If you encounter issues during instance creation:
  - Verify AWS credentials and permissions.
  - Ensure the specified VPC and subnet IDs are correct.
  - Check the security group settings.
- If health checks fail:
  - Confirm that the application is running on the instances.
  - Verify that the security group allows inbound traffic on the specified port (8000).
