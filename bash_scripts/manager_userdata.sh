#!/bin/bash

# Update the instance and install necessary packages
apt-get update;

# Install MySQL server
echo "Installing MySQL server..."
apt-get install mysql-server -y;

MYSQL_CONF="/etc/mysql/mysql.conf.d/mysqld.cnf"

# Backup the original configuration file before making changes
sudo cp $MYSQL_CONF $MYSQL_CONF.bak

# Update the MySQL configuration file with the necessary settings
sudo bash -c "cat <<EOF >> $MYSQL_CONF

[mysqld]
server-id = 1
bind-address = 0.0.0.0  # Allow connections from all machines
binlog_do_db = sakila  # Only replicate the sakila database
log_bin = /var/log/mysql/mysql-bin.log
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
CREATE USER 'replica_user'@'%' IDENTIFIED WITH mysql_native_password BY '$REPLICA_PASSWORD';
GRANT REPLICATION SLAVE ON *.* TO 'replica_user'@'%';

CREATE USER 'proxy'@'%' IDENTIFIED WITH mysql_native_password BY 'proxy';
GRANT SELECT, INSERT, UPDATE, DELETE ON sakila.* TO 'proxy'@'%';
FLUSH PRIVILEGES;

START MASTER;
"

sudo apt-get install sysbench -y
sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user="root" --mysql-password="$ROOT_PASSWORD" prepare 
sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user="root" --mysql-password="$ROOT_PASSWORD" run

