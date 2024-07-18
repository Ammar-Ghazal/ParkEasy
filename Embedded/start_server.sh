#!/bin/bash

# Function to get the IP address of the laptop
get_laptop_ip() {
    # kinda janky might not always work
    local laptop_ip=$(sudo arp-scan --localnet | awk '/IPv4:/ {print $8}')
    echo $laptop_ip
}

# Start RabbitMQ server
echo "Starting RabbitMQ server..."
sudo systemctl start rabbitmq-server

# Enable RabbitMQ management plugin
echo "Enabling RabbitMQ management plugin..."
sudo rabbitmq-plugins enable rabbitmq_management

# Enable RabbitMQ server
echo "Enabling RabbitMQ server..."
sudo systemctl enable rabbitmq-server

# Wait for RabbitMQ server to start
sleep 5

# Find the IP address of the laptop
echo "Finding IP address of the laptop..."
laptop_ip=$(get_laptop_ip)
if [ -z "$laptop_ip" ]; then
    echo "Error: Unable to find the IP address of the laptop."
    exit 1
fi
echo "Laptop IP address found: $laptop_ip"

# Start the consumer script with the laptop's IP address
echo "Starting consumer script..."
python3 threaded_consumer.py "$laptop_ip"

