#!/bin/bash

# Update the instance and install necessary packages
apt-get update;

TOKEN=$(curl -X PUT -s http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance ID = $INSTANCE_ID"

SERVER_ID='<SERVERID>'
echo "Server ID = $SERVER_ID"

MANAGER_IP='<MANAGERIP>'
echo "Manager IP address = $MANAGER_IP"

MANAGER_LOG_FILE='<MANAGERLOGFILE>'
MANAGER_LOG_POSITION='<MANAGERLOGPOSITION>'

# Install MySQL server
echo "Installing MySQL server..."
apt-get install mysql-server -y;

MYSQL_CONF="/etc/mysql/mysql.conf.d/mysqld.cnf"

# Backup the original configuration file before making changes
sudo cp $MYSQL_CONF $MYSQL_CONF.bak

# Update the MySQL configuration file with the necessary settings
sudo bash -c "cat <<EOF >> $MYSQL_CONF

[mysqld]
server-id = $SERVER_ID
bind-address = 0.0.0.0  # Allow connections from all machines
relay-log = /var/log/mysql/mysql-relay-bin.log
log_bin = /var/log/mysql/mysql-bin.log
read-only = 1
EOF"

# Start MySQL service
echo "Starting MySQL service..."
systemctl start mysql;
systemctl enable mysql;

# Secure MySQL installation (automate the process)
ROOT_PASSWORD="Qq_123234345"
REPLICA_PASSWORD="Qq_1223235"

sudo mysql -sfu root -e "
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$ROOT_PASSWORD';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;"

# Download the Sakila database schema and data
echo "Downloading Sakila database..."
cd /tmp
wget https://downloads.mysql.com/docs/sakila-db.tar.gz

# Extract the downloaded tar file
echo "Extracting Sakila database..."
tar -xzvf sakila-db.tar.gz

# Import the Sakila database into MySQL
echo "Creating and importing the Sakila database..."
mysql -u root -p$ROOT_PASSWORD -e "CREATE DATABASE sakila;"
mysql -u root -p$ROOT_PASSWORD sakila < /tmp/sakila-db/sakila-schema.sql
mysql -u root -p$ROOT_PASSWORD sakila < /tmp/sakila-db/sakila-data.sql

echo "Sakila database installed successfully!"

systemctl restart mysql;

mysql -u root -p$ROOT_PASSWORD -e "
CREATE USER 'proxy'@'%' IDENTIFIED WITH mysql_native_password BY 'proxy';
GRANT SELECT ON sakila.* TO 'proxy'@'%';
FLUSH PRIVILEGES;

CHANGE MASTER TO
    MASTER_HOST = '$MANAGER_IP',
    MASTER_USER = 'replica_user',
    MASTER_PASSWORD = '$REPLICA_PASSWORD',
    MASTER_LOG_FILE = '$MANAGER_LOG_FILE',
    MASTER_LOG_POS = $MANAGER_LOG_POSITION;

START SLAVE;
"

sudo apt-get install sysbench -y
sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user="root" --mysql-password="$ROOT_PASSWORD" prepare 
sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user="root" --mysql-password="$ROOT_PASSWORD" run 

