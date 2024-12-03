import time
import os
import globals as g
import boto3
import stat
import paramiko
import json

import instance_setup as ic

'''
Description: Connects to a remote EC2 instance via SSH, runs a MySQL command to fetch the master status (file and position), and returns the result.
Inputs: 
    instance_ip (str) - The IP address of the EC2 instance to connect to via SSH.
    pem_file_path (str) - The path to the PEM file used for SSH authentication.
    root_password (str) - The root password for the MySQL server to execute the command.
Outputs: 
    list - A list containing two elements: the master log file and the position, as returned by the `SHOW MASTER STATUS` MySQL command.
'''
def fetch_manager_status(instance_ip: str, pem_file_path: str, root_password: str):
    try:
        print(f"Connecting to {instance_ip} using SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(instance_ip, username='ubuntu', key_filename=pem_file_path)
                
        command = f"output=$(mysql -u root -p{root_password} -e 'SHOW MASTER STATUS;' | awk 'NR>1 {{print $1, $2}}'); file=$(echo $output | awk '{{print $1}}'); position=$(echo $output | awk '{{print $2}}'); echo \"$file $position\""

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        print("Command output:", output)

        result = output.strip().split()
        
        ssh.close()
        print("SSH connection closed.")

        return result

    except Exception as e:
        print(f"An error occurred during SSH: {str(e)}")


'''
Description: Cleans up resources by terminating EC2 instances (worker, manager, proxy, gatekeeper, and trusted host), deleting associated security groups, and removing the EC2 key pair.
'''
def cleanup(self):
    try:
        instance_ids = [
            instance.id
            for instance in self.worker_instances + [self.manager_instance]
        ]
        if instance_ids:
            self.ec2_client.terminate_instances(InstanceIds=instance_ids)
            print(f"Termination of instances {instance_ids} initiated.")

            waiter = self.ec2_client.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=instance_ids)
            print("Instances terminated.")

        if self.proxy_instance:
            self.ec2_client.terminate_instances(InstanceIds=[self.proxy_instance.id])
            print(f"Termination of proxy instance {self.proxy_instance.id} initiated.")

            waiter = self.ec2_client.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=[self.proxy_instance.id])
            print("Proxy instance terminated.")

        if self.gatekeeper_instance:
            self.ec2_client.terminate_instances(InstanceIds=[self.gatekeeper_instance.id])
            print(f"Termination of instance {self.gatekeeper_instance.id} initiated.")

            waiter = self.ec2_client.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=[self.gatekeeper_instance.id])
            print("Gatekeeper instance terminated.")

        if self.trusted_host_instance:
            self.ec2_client.terminate_instances(InstanceIds=[self.trusted_host_instance.id])
            print(f"Termination of instance {self.trusted_host_instance.id} initiated.")

            waiter = self.ec2_client.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=[self.trusted_host_instance.id])
            print("Trusted host instance terminated.")

        self.ec2_client.delete_security_group(GroupId=self.security_mysql_id)
        print(f"Security group {self.security_mysql_id} deleted.")

        self.ec2_client.delete_security_group(GroupId=self.security_proxy_id)
        print(f"Security group {self.security_proxy_id} deleted.")

        self.ec2_client.delete_security_group(GroupId=self.security_trusted_host_id)
        print(f"Security group {self.security_trusted_host_id} deleted.")

        self.ec2_client.delete_security_group(GroupId=self.security_gatekeeper_id)
        print(f"Security group {self.security_gatekeeper_id} deleted.")



        self.ec2_client.delete_key_pair(KeyName=self.key_name)
    except Exception as e:
        print(f"An error occurred during cleaning up: {str(e)}")


if __name__ == "__main__":
    print("RUNNING MAIN AUTOMATED SCRIPT")  

    # cleanup()  

    pem_file_path = g.pem_file_path

    # Create EC2 Client
    session = boto3.Session()
    ec2 = session.resource('ec2')

    # Read VPC and Subnet IDs from files
    with open(f'{g.aws_folder_path}/vpc_id.txt', 'r') as file:
        vpc_id = file.read().strip()

    with open(f'{g.aws_folder_path}/subnet_id.txt', 'r') as file:
        subnet_id = file.read().strip()


    # Delete keypair with same name, USED IN TESTING
    # ec2.KeyPair("key_name").delete()

    # Create a new key pair and save the .pem file
    key_pair = ec2.create_key_pair(KeyName='key_name')

    # Change security to be able to read
    os.chmod(pem_file_path, stat.S_IWUSR)

    # Save the private key to a .pem file
    with open(pem_file_path, 'w') as pem_file:
        pem_file.write(key_pair.key_material)

    # Change file permissions to 400 to protect the private key
    os.chmod(pem_file_path, stat.S_IRUSR)

    # Create security groups
    security_mysql_id = ic.createSecurityGroup(vpc_id, "mysql security group")
    security_proxy_id = ic.createSecurityGroup(vpc_id, "proxy security group")
    security_trusted_host_id = ic.createSecurityGroup(vpc_id, "trusted host security group")
    security_gatekeeper_id = ic.createSecurityGroup(vpc_id, "gatekeeper public security group")

    # Manager and workers
    with open(f'{g.path}/bash_scripts/worker_userdata.sh', 'r') as file:
        worker_user_data = file.read()

    with open(f'{g.path}/bash_scripts/manager_userdata.sh', 'r') as file:
        manager_user_data = file.read()

    print("Creating instances...")

    print("Creating manager...")
    manager_instances = ic.createInstance('t2.micro', 1, 1, key_pair, security_mysql_id, subnet_id, manager_user_data, "manager")
    manager_public_ip = manager_instances[0].public_ip_address
    manager_private_ip = manager_instances[0].private_ip_address

    print("Waiting for manager to be up and running...")
    waiter = boto3.client('ec2').get_waiter('instance_status_ok')
    waiter.wait(
        InstanceIds=[manager_instances[0].instance_id],
        WaiterConfig={
            'Delay': 15, 
            'MaxAttempts': 20 
        }
    )

    root_password = f'{g.root_pass}'
    manager_log_file, manager_log_position = fetch_manager_status(manager_public_ip, pem_file_path, root_password)

    print("Creating workers...")
    server_ids = [2, 3]
    worker_instance_ids = []
    worker_private_ips = []
    for server_id in server_ids:
        user_data = worker_user_data.replace('<SERVERID>', str(server_id)).replace('<MANAGERIP>', manager_private_ip).replace('<MANAGERLOGFILE>', manager_log_file).replace('<MANAGERLOGPOSITION>', manager_log_position)
        worker_instances = ic.createInstance('t2.micro', 1, 1, key_pair, security_mysql_id, subnet_id, user_data, "worker")
        worker_instance_ids.append(worker_instances[0].instance_id)
        worker_private_ips.append(worker_instances[0].private_ip_address)

    print("Waiting for workers to be up and running...")
    waiter.wait(
        InstanceIds=worker_instance_ids,
        WaiterConfig={
            'Delay': 15,  
            'MaxAttempts': 20 
        }
    )

    # Proxy
    with (
        open(f'{g.path}/bash_scripts/proxy_userdata.sh', 'r') as userdata, 
        open(f'{g.path}/proxy.py', 'r') as pythonProgram
    ):
        proxy_program = pythonProgram.read()
        comma_separated_worker_ips = ','.join(worker_private_ips)
        proxy_user_data = userdata.read().replace('<PROXYCODE>', proxy_program).replace('<MANAGERIP>', manager_private_ip).replace('<WORKERIPSCSL>', comma_separated_worker_ips)

    print("Creating proxy...")
    proxy_instances = ic.createInstance('t2.large', 1, 1, key_pair, security_proxy_id, subnet_id, proxy_user_data, "proxy")

    print("Waiting for proxy to be up and running...")
    waiter.wait(
        InstanceIds=[proxy_instances[0].instance_id],
        WaiterConfig={
            'Delay': 15,  
            'MaxAttempts': 20  
        }
    )

    # Trusted Host
    with (
            open(f'{g.path}/bash_scripts/trusted_host.sh', 'r') as userdata, 
            open(f'{g.path}/trusted_host.py', 'r') as pythonProgram
        ):
            trusted_host_program = pythonProgram.read()
            trusted_host_user_data = userdata.read().replace('<TRUSTEDHOSTCODE>', trusted_host_program).replace('<MANAGERIP>', manager_private_ip).replace('<WORKERIPSCSL>', comma_separated_worker_ips)
 

    print("Creating trusted host...")
    trusted_host_instance = ic.createInstance('t2.large', 1, 1, key_pair, security_trusted_host_id, subnet_id, trusted_host_user_data, "trusted host")
    
    print("Waiting for trusted host to be up and running...")
    waiter = boto3.client('ec2').get_waiter('instance_status_ok')
    waiter.wait(
        InstanceIds=[trusted_host_instance[0].instance_id],
        WaiterConfig={
            'Delay': 15,  
            'MaxAttempts': 20  
        }
    )

    # Gatekeeper
    with (
            open(f'{g.path}/bash_scripts/gatekeeper.sh', 'r') as userdata, 
            open(f'{g.path}/gatekeeper.py', 'r') as pythonProgram
        ):
            gatekeeper_program = pythonProgram.read()
            gatekeeper_user_data = userdata.read().replace('<GATEKEEPERCODE>', gatekeeper_program).replace('<MANAGERIP>', manager_private_ip).replace('<WORKERIPSCSL>', comma_separated_worker_ips)

    print("Creating gatekeeper...")
    gatekeeper_instance = ic.createInstance('t2.large', 1, 1, key_pair, security_gatekeeper_id, subnet_id, gatekeeper_user_data, "gatekeeper")

    print("Waiting for gatekeeper to be up and running...")
    waiter = boto3.client('ec2').get_waiter('instance_status_ok')
    waiter.wait(
        InstanceIds=[gatekeeper_instance[0].instance_id],
        WaiterConfig={
            'Delay': 15, 
            'MaxAttempts': 20 
        }
    )

    print("Exporting IPs...")
    def export_instances_public_ips(self):
        instances_ips = {
            "worker_ips": [instance.public_ip_address for instance in self.worker_instances],
            "manager_ip": self.manager_instances.public_ip_address,
            "proxy_ip": self.proxy_instances.public_ip_address,
            "gatekeeper_ip": self.gatekeeper_instance.public_ip_address,
            "trusted_host_ip": self.trusted_host_instance.public_ip_address
        }

        with open("instances_ips.json", "w") as file:
            json.dump(instances_ips, file)

    export_instances_public_ips

    print("AUTOMATED SCRIPT COMPLETED!")

