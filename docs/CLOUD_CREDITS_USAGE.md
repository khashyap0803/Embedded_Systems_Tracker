# 💰 Cloud Credits Usage Guide - Embedded Systems Focus

**Total Credits:** ~$1,500 equivalent  
**Duration:** 1 year  
**Goal:** 100% utilization on embedded systems skill development

---

## Executive Summary

| Platform | Total | Allocated | Waste |
|----------|-------|-----------|-------|
| **GCP** | ₹1,00,000 | ₹1,00,000 | ₹0 ✅ |
| **Azure** | $200 | $200 | $0 ✅ |
| **DigitalOcean** | $100 | $100 | $0 ✅ |

---

# 🟢 GCP ₹1,00,000 - Detailed Breakdown

## 1. ARM Cross-Compilation Server (₹40,000/year)

### Resource Configuration

| Property | Value |
|----------|-------|
| **Service** | Compute Engine |
| **Instance Type** | e2-standard-4 |
| **vCPUs** | 4 |
| **RAM** | 16 GB |
| **Disk** | 200 GB SSD |
| **OS** | Ubuntu 22.04 LTS |
| **Monthly Cost** | ~₹3,500 |
| **Annual Cost** | ₹42,000 (capped at ₹40,000) |

### Setup Commands

```bash
# Create the instance
gcloud compute instances create arm-build-server \
    --zone=asia-south1-a \
    --machine-type=e2-standard-4 \
    --boot-disk-size=200GB \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

# SSH into the server
gcloud compute ssh arm-build-server --zone=asia-south1-a
```

### Required Packages Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install ARM cross-compiler
sudo apt install -y gcc-arm-none-eabi gdb-multiarch

# Install Yocto dependencies
sudo apt install -y gawk wget git diffstat unzip texinfo gcc build-essential \
    chrpath socat cpio python3 python3-pip python3-pexpect xz-utils \
    debianutils iputils-ping python3-git python3-jinja2 libegl1-mesa \
    libsdl1.2-dev pylint3 xterm python3-subunit mesa-common-dev zstd liblz4-tool

# Install Docker for containerized builds
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### Curriculum Week Mapping

| Week | Task | How Server Helps |
|------|------|------------------|
| 1-5 | GPIO, Timers | Compile STM32 HAL projects |
| 6-10 | DMA, ADC | Build complex firmware |
| 50-55 | Embedded Linux | Build Yocto images (~4 hours vs 8+ hours on laptop) |
| 56-60 | Buildroot | Compile custom Linux distributions |
| 65-71 | Zephyr RTOS | Build and test Zephyr samples |

### Permanent Outputs to Download

| Artifact | Size | Command to Download |
|----------|------|---------------------|
| ARM GCC Toolchain | ~500MB | `gcloud compute scp arm-build-server:/opt/gcc-arm ~/backup/` |
| Yocto SSTATE_CACHE | ~50GB | `gsutil cp -r gs://bucket/sstate-cache ~/backup/` |
| Yocto DL_DIR | ~20GB | `gsutil cp -r gs://bucket/downloads ~/backup/` |
| Custom Linux Image | ~2GB | `scp server:~/yocto/build/images/*.wic ~/backup/` |

### Cost Optimization Tips

```
1. STOP the instance when not using:
   gcloud compute instances stop arm-build-server --zone=asia-south1-a
   
2. Use preemptible VMs for long builds (70% cheaper):
   --preemptible flag during creation
   
3. Use spot VMs for non-critical builds:
   --provisioning-model=SPOT
```

---

## 2. IoT Protocol Simulation (₹25,000/year)

### 2.1 Cloud Pub/Sub - MQTT Simulation

| Property | Value |
|----------|-------|
| **Service** | Cloud Pub/Sub |
| **Monthly Cost** | ~₹1,500 |
| **Annual Cost** | ₹18,000 |
| **Message Volume** | ~10 million/month (enough for learning) |

### Create Pub/Sub Resources

```bash
# Create a topic (represents an MQTT topic)
gcloud pubsub topics create sensor-data

# Create a subscription (represents an MQTT subscriber)
gcloud pubsub subscriptions create sensor-sub --topic=sensor-data

# Test publish
gcloud pubsub topics publish sensor-data --message='{"temp": 25.5, "humidity": 60}'

# Test subscribe
gcloud pubsub subscriptions pull sensor-sub --auto-ack
```

### Simulating MQTT with Python

```python
# mqtt_simulator.py - Run on your STM32 or local machine
from google.cloud import pubsub_v1
import json
import time

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('your-project', 'sensor-data')

def publish_sensor_data(temperature, humidity):
    data = json.dumps({
        "device_id": "stm32-001",
        "temperature": temperature,
        "humidity": humidity,
        "timestamp": time.time()
    }).encode('utf-8')
    
    future = publisher.publish(topic_path, data)
    print(f"Published message ID: {future.result()}")

# Simulate sensor readings
for i in range(100):
    publish_sensor_data(20 + i * 0.1, 50 + i * 0.2)
    time.sleep(1)
```

### 2.2 Cloud Functions - Edge Processing Simulation

| Property | Value |
|----------|-------|
| **Service** | Cloud Functions (2nd gen) |
| **Monthly Cost** | ~₹500 |
| **Annual Cost** | ₹6,000 |
| **Invocations** | ~1 million/month free tier |

### Create Edge Processing Function

```python
# main.py - Deploy as Cloud Function
import functions_framework
import json

@functions_framework.http
def process_sensor_data(request):
    """Simulates edge processing of sensor data."""
    data = request.get_json()
    
    # Simulated edge AI inference
    temperature = data.get('temperature', 0)
    
    # Simple anomaly detection (like TinyML would do)
    if temperature > 35:
        alert = "HIGH_TEMP_ALERT"
    elif temperature < 10:
        alert = "LOW_TEMP_ALERT"
    else:
        alert = "NORMAL"
    
    return json.dumps({
        "original": data,
        "processed": True,
        "alert": alert,
        "edge_latency_ms": 5  # Simulated
    })
```

### Deploy the Function

```bash
gcloud functions deploy process-sensor-data \
    --gen2 \
    --runtime=python311 \
    --trigger-http \
    --allow-unauthenticated \
    --region=asia-south1
```

### Curriculum Week Mapping

| Week | Topic | How Pub/Sub/Functions Help |
|------|-------|---------------------------|
| 17-19 | UART/SPI basics | Send data from STM32 → Cloud |
| 20-22 | WiFi/Ethernet | Connect ESP32 to Pub/Sub |
| 23-24 | MQTT protocol | Deep dive into pub/sub patterns |
| 25-27 | CoAP, LwM2M | Simulate lightweight protocols |
| 28-30 | Cloud integration | Full device-to-cloud pipeline |

---

## 3. Edge AI / TinyML Development (₹20,000/year)

### 3.1 Vertex AI Workbench

| Property | Value |
|----------|-------|
| **Service** | Vertex AI Workbench (User-Managed) |
| **Instance Type** | e2-standard-2 (CPU only, no GPU) |
| **Monthly Cost** | ~₹1,500 |
| **Annual Cost** | ₹18,000 |

### Create Vertex AI Notebook

```bash
# Create a user-managed notebook
gcloud notebooks instances create tinyml-workbench \
    --location=asia-south1-a \
    --machine-type=e2-standard-2 \
    --vm-image-project=deeplearning-platform-release \
    --vm-image-family=tf2-latest-cpu
```

### TinyML Training Workflow

```python
# tinyml_gesture.py - Train a gesture recognition model
import tensorflow as tf
import numpy as np

# 1. Load accelerometer dataset (from your STM32 recordings)
X_train = np.load('gestures_train.npy')  # Shape: (samples, timesteps, 3)
y_train = np.load('labels_train.npy')   # Labels: 0=idle, 1=wave, 2=punch

# 2. Build a small CNN model (fits in STM32 RAM)
model = tf.keras.Sequential([
    tf.keras.layers.Conv1D(8, 3, activation='relu', input_shape=(50, 3)),
    tf.keras.layers.MaxPooling1D(2),
    tf.keras.layers.Conv1D(16, 3, activation='relu'),
    tf.keras.layers.GlobalAveragePooling1D(),
    tf.keras.layers.Dense(3, activation='softmax')
])

# 3. Compile and train
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=50, validation_split=0.2)

# 4. Convert to TensorFlow Lite (for STM32)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]  # Quantize for MCU
tflite_model = converter.convert()

# 5. Save the model (PERMANENT OUTPUT!)
with open('gesture_model.tflite', 'wb') as f:
    f.write(tflite_model)

print(f"Model size: {len(tflite_model) / 1024:.1f} KB")  # Should be < 50KB
```

### Deploy TinyML to STM32

```c
// main.c - Use the trained model on STM32
#include "gesture_model.h"  // Generated from .tflite
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"

// Model buffer (from gesture_model.tflite converted to C array)
extern const unsigned char gesture_model_tflite[];
extern const unsigned int gesture_model_tflite_len;

void run_inference(float* accelerometer_data) {
    static tflite::MicroInterpreter* interpreter;
    // ... TFLite Micro setup code ...
    
    // Copy input data
    memcpy(interpreter->input(0)->data.f, accelerometer_data, 50 * 3 * sizeof(float));
    
    // Run inference
    interpreter->Invoke();
    
    // Get result
    float* output = interpreter->output(0)->data.f;
    int gesture = (output[0] > output[1] && output[0] > output[2]) ? 0 :
                  (output[1] > output[2]) ? 1 : 2;
    
    printf("Detected gesture: %d\n", gesture);
}
```

### Curriculum Week Mapping

| Week | Topic | How Vertex AI Helps |
|------|-------|---------------------|
| 38-39 | TinyML intro | Train first model |
| 40-41 | Model optimization | Quantization, pruning |
| 42-43 | Edge Impulse | Compare with cloud training |
| 44-45 | Deployment | Convert and deploy to STM32 |

### Permanent Outputs

| Artifact | Size | Download |
|----------|------|----------|
| Trained .tflite models | 10-100KB each | Google Drive |
| Training datasets | 1-10MB | Google Drive |
| Jupyter notebooks | 1-5MB | GitHub |

---

## 4. CI/CD for Firmware (₹15,000/year)

### 4.1 Cloud Build Configuration

| Property | Value |
|----------|-------|
| **Service** | Cloud Build |
| **Monthly Cost** | ~₹1,000 |
| **Build Minutes** | ~1000 min/month |

### cloudbuild.yaml for STM32 Firmware

```yaml
# cloudbuild.yaml - Automated STM32 firmware build
steps:
  # Step 1: Use ARM GCC Docker image
  - name: 'gcr.io/$PROJECT_ID/arm-gcc:12.2'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Building STM32 firmware..."
        cd firmware/
        make clean
        make all
        
  # Step 2: Run static analysis (MISRA)
  - name: 'gcr.io/$PROJECT_ID/cppcheck:latest'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        cppcheck --enable=all --error-exitcode=1 src/
        
  # Step 3: Run unit tests (on host)
  - name: 'gcr.io/$PROJECT_ID/arm-gcc:12.2'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        cd tests/
        make test
        ./run_tests
        
  # Step 4: Upload firmware binary
  - name: 'gcr.io/cloud-builders/gsutil'
    args: ['cp', 'firmware/build/*.bin', 'gs://$PROJECT_ID-firmware/builds/$BUILD_ID/']

# Store build artifacts
artifacts:
  objects:
    location: 'gs://$PROJECT_ID-firmware/builds/$BUILD_ID/'
    paths: ['firmware/build/*.bin', 'firmware/build/*.elf', 'firmware/build/*.map']
```

### Create ARM GCC Docker Image

```dockerfile
# Dockerfile.arm-gcc
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    gcc-arm-none-eabi \
    gdb-multiarch \
    make \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
```

### Build and Push Docker Image

```bash
# Build the Docker image
docker build -t gcr.io/$PROJECT_ID/arm-gcc:12.2 -f Dockerfile.arm-gcc .

# Push to Artifact Registry
docker push gcr.io/$PROJECT_ID/arm-gcc:12.2
```

### 4.2 Artifact Registry

| Property | Value |
|----------|-------|
| **Service** | Artifact Registry |
| **Monthly Cost** | ~₹250 |
| **Storage** | 10GB free, then ₹2/GB |

### Create Registry

```bash
# Create Docker repository
gcloud artifacts repositories create embedded-builds \
    --repository-format=docker \
    --location=asia-south1 \
    --description="Embedded firmware Docker images"
```

### Curriculum Week Mapping

| Week | Topic | How CI/CD Helps |
|------|-------|-----------------|
| 12-16 | Complete projects | Automated testing |
| 45-49 | Safety-critical | MISRA compliance checks |
| 65-71 | Production | Full CI/CD pipeline |

### Permanent Outputs

| Artifact | Location | Action Before Expiry |
|----------|----------|---------------------|
| cloudbuild.yaml | GitHub | Already version controlled |
| Dockerfile.arm-gcc | GitHub | Already version controlled |
| Docker images | Artifact Registry | `docker save` to local tar |
| Firmware binaries | Cloud Storage | `gsutil cp` to local |

---

# 🔵 Azure $200 - Detailed Breakdown

## 1. Azure IoT Hub ($120/year)

### Resource Configuration

| Property | Value |
|----------|-------|
| **Service** | Azure IoT Hub |
| **Tier** | S1 (Standard) |
| **Units** | 1 |
| **Messages/day** | 400,000 |
| **Monthly Cost** | $10 |
| **Annual Cost** | $120 |

### Create IoT Hub

```bash
# Login to Azure
az login

# Create resource group
az group create --name embedded-learning --location eastus

# Create IoT Hub
az iot hub create \
    --name my-embedded-iot-hub \
    --resource-group embedded-learning \
    --sku S1 \
    --unit 1
```

### Register a Device

```bash
# Create device identity
az iot hub device-identity create \
    --hub-name my-embedded-iot-hub \
    --device-id stm32-device-001

# Get connection string (save this!)
az iot hub device-identity connection-string show \
    --hub-name my-embedded-iot-hub \
    --device-id stm32-device-001
```

### ESP32/STM32 Connection Code

```c
// azure_iot.c - Connect STM32 to Azure IoT Hub
#include "azure_iot_hub_client.h"

#define CONNECTION_STRING "HostName=my-embedded-iot-hub.azure-devices.net;DeviceId=stm32-device-001;SharedAccessKey=..."

void send_telemetry(float temperature, float humidity) {
    char payload[256];
    snprintf(payload, sizeof(payload),
        "{\"temperature\": %.2f, \"humidity\": %.2f, \"timestamp\": %lu}",
        temperature, humidity, HAL_GetTick());
    
    // Send to Azure IoT Hub
    IoTHubClient_SendEventAsync(iotHubClientHandle, payload);
    printf("Sent: %s\n", payload);
}

void receive_commands(void) {
    // Receive commands from cloud (OTA updates, config changes)
    IoTHubClient_SetMessageCallback(iotHubClientHandle, message_callback, NULL);
}
```

### Device Twin for Configuration

```json
// Device Twin - Stored in Azure, synced to device
{
    "properties": {
        "desired": {
            "reporting_interval_ms": 5000,
            "threshold_temp": 30.0,
            "firmware_version": "1.2.0"
        },
        "reported": {
            "current_temp": 25.5,
            "battery_level": 85,
            "wifi_rssi": -65
        }
    }
}
```

### Curriculum Week Mapping

| Week | Topic | How IoT Hub Helps |
|------|-------|-------------------|
| 23-25 | Cloud connectivity | Real Azure integration |
| 28-30 | Device management | Device twins, direct methods |
| 55-60 | OTA updates | Firmware deployment |
| 65-71 | Production IoT | Industry-grade platform |

---

## 2. Azure RTOS Learning ($50/year)

### What You Get

| Component | Description |
|-----------|-------------|
| **ThreadX** | Industry RTOS kernel |
| **NetX Duo** | TCP/IP stack |
| **FileX** | FAT file system |
| **GUIX** | GUI framework |
| **USBX** | USB stack |

### ThreadX Simulation on PC

```c
// main.c - ThreadX thread example (runs on PC simulator)
#include "tx_api.h"

#define THREAD_STACK_SIZE 1024
static TX_THREAD sensor_thread;
static TX_THREAD display_thread;
static UCHAR sensor_stack[THREAD_STACK_SIZE];
static UCHAR display_stack[THREAD_STACK_SIZE];

void sensor_thread_entry(ULONG param) {
    while (1) {
        // Read sensor
        float temp = read_temperature();
        
        // Send to queue
        tx_queue_send(&data_queue, &temp, TX_WAIT_FOREVER);
        
        // Sleep 1 second
        tx_thread_sleep(100);  // 100 ticks = 1 second
    }
}

void display_thread_entry(ULONG param) {
    float temp;
    while (1) {
        // Wait for data
        tx_queue_receive(&data_queue, &temp, TX_WAIT_FOREVER);
        
        // Update display
        printf("Temperature: %.2f°C\n", temp);
    }
}

int main(void) {
    tx_kernel_enter();
    return 0;
}

void tx_application_define(void *first_unused_memory) {
    // Create threads
    tx_thread_create(&sensor_thread, "Sensor", sensor_thread_entry, 0,
                     sensor_stack, THREAD_STACK_SIZE, 1, 1, TX_NO_TIME_SLICE, TX_AUTO_START);
    tx_thread_create(&display_thread, "Display", display_thread_entry, 0,
                     display_stack, THREAD_STACK_SIZE, 2, 2, TX_NO_TIME_SLICE, TX_AUTO_START);
}
```

### Curriculum Week Mapping

| Week | Topic | How Azure RTOS Helps |
|------|-------|---------------------|
| 13-16 | RTOS basics | Compare with FreeRTOS |
| 45-49 | Safety-critical | Pre-certified RTOS |

---

## 3. Azure DevOps Pipelines ($30/year)

### Pipeline for Embedded Firmware

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Build
    jobs:
      - job: BuildFirmware
        steps:
          - script: |
              sudo apt-get update
              sudo apt-get install -y gcc-arm-none-eabi
            displayName: 'Install ARM GCC'
          
          - script: |
              cd firmware
              make clean
              make all
            displayName: 'Build Firmware'
          
          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: 'firmware/build'
              artifactName: 'firmware-binary'

  - stage: Test
    jobs:
      - job: UnitTests
        steps:
          - script: |
              cd tests
              make test
              ./run_tests --gtest_output=xml:test-results.xml
            displayName: 'Run Unit Tests'
          
          - task: PublishTestResults@2
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: '**/test-results.xml'

  - stage: StaticAnalysis
    jobs:
      - job: MISRA
        steps:
          - script: |
              cppcheck --enable=all --error-exitcode=1 src/
            displayName: 'MISRA Compliance Check'
```

---

# 🟣 DigitalOcean $100 - Detailed Breakdown

## 1. Dedicated Build Droplet ($72/year)

### Resource Configuration

| Property | Value |
|----------|-------|
| **Droplet Type** | Basic |
| **Size** | s-2vcpu-4gb |
| **vCPUs** | 2 |
| **RAM** | 4 GB |
| **Storage** | 80 GB SSD |
| **Monthly Cost** | $6 |
| **Annual Cost** | $72 |

### Create Droplet

```bash
# Using doctl CLI
doctl compute droplet create embedded-build \
    --image ubuntu-22-04-x64 \
    --size s-2vcpu-4gb \
    --region nyc1 \
    --ssh-keys $(doctl compute ssh-key list --format ID --no-header)
```

### Setup as Build Server

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Install ARM toolchain
apt update && apt upgrade -y
apt install -y gcc-arm-none-eabi gdb-multiarch

# Install QEMU for ARM emulation
apt install -y qemu-system-arm qemu-user-static

# Install Zephyr SDK
wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.1/zephyr-sdk-0.16.1_linux-x86_64.tar.xz
tar xvf zephyr-sdk-0.16.1_linux-x86_64.tar.xz
cd zephyr-sdk-0.16.1
./setup.sh
```

### QEMU ARM Emulation

```bash
# Run ARM Linux image in QEMU
qemu-system-arm \
    -M vexpress-a9 \
    -kernel zImage \
    -dtb vexpress-v2p-ca9.dtb \
    -drive if=sd,file=rootfs.ext4,format=raw \
    -append "root=/dev/mmcblk0 console=ttyAMA0" \
    -nographic
```

### Self-Hosted MQTT Broker (Mosquitto)

```bash
# Install Mosquitto
apt install -y mosquitto mosquitto-clients

# Configure for external access
cat > /etc/mosquitto/conf.d/remote.conf << EOF
listener 1883 0.0.0.0
allow_anonymous true
EOF

# Restart
systemctl restart mosquitto

# Test from your laptop
mosquitto_pub -h your-droplet-ip -t "sensor/temp" -m "25.5"
mosquitto_sub -h your-droplet-ip -t "sensor/#"
```

### Self-Hosted OTA Server (Hawkbit)

```bash
# Docker compose for Hawkbit
cat > docker-compose.yml << EOF
version: '3'
services:
  hawkbit:
    image: hawkbit/hawkbit-update-server
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=mysql
EOF

docker-compose up -d
```

### Curriculum Week Mapping

| Week | Use Case |
|------|----------|
| Any | ARM emulation with QEMU |
| 23-24 | Self-hosted MQTT broker |
| 55-60 | OTA update server (Hawkbit) |
| 65-71 | Complete embedded Linux testing |

---

## 2. Object Storage - Spaces ($28/year)

### Configuration

| Property | Value |
|----------|-------|
| **Service** | Spaces |
| **Size** | 50 GB |
| **Monthly Cost** | $2.50 |
| **Annual Cost** | $30 (capped at $28) |

### Setup Spaces

```bash
# Create a Space (via web console or s3cmd)
s3cmd --configure
# Enter DigitalOcean Spaces credentials

# Upload firmware binaries
s3cmd put firmware.bin s3://my-firmware-bucket/v1.2.0/

# Generate download URL for OTA
s3cmd signurl s3://my-firmware-bucket/v1.2.0/firmware.bin +3600
```

### OTA Update Flow

```
1. Build firmware on GCP Cloud Build
2. Upload to DigitalOcean Spaces
3. Device polls Hawkbit for updates
4. Hawkbit returns Spaces URL
5. Device downloads and flashes firmware
6. Device reports success to Azure IoT Hub
```

---

# 📅 Complete Monthly Schedule

## Month 1-2: Setup & Foundation

| Week | Platform | Action | Cost |
|------|----------|--------|------|
| 1 | GCP | Create build server | ₹7,000 |
| 1 | Azure | Create IoT Hub | $10 |
| 1 | DO | Create droplet | $6 |
| 2-4 | GCP | Install toolchains | ₹7,000 |
| 5-8 | All | Learning GPIO, Timers | ₹14,000 + $10 + $6 |

**Month 1-2 Total:** ₹28,000 + $26

## Month 3-4: Connectivity

| Week | Platform | Action | Cost |
|------|----------|--------|------|
| 9-12 | GCP | Pub/Sub setup | ₹12,000 |
| 9-12 | Azure | IoT Hub + RTOS | $35 |
| 9-12 | DO | MQTT broker | $12 |

**Month 3-4 Total:** ₹12,000 + $47

## Month 5-6: IoT Mastery

| Week | Platform | Action | Cost |
|------|----------|--------|------|
| 13-16 | GCP | Cloud Functions | ₹8,000 |
| 13-16 | Azure | Device twins, OTA | $25 |
| 13-16 | DO | Hawkbit setup | $12 |

**Month 5-6 Total:** ₹8,000 + $37

## Month 7-8: TinyML

| Week | Platform | Action | Cost |
|------|----------|--------|------|
| 17-20 | GCP | Vertex AI Workbench | ₹12,000 |
| 17-20 | Azure | Minimal | $15 |
| 17-20 | DO | Model testing | $12 |

**Month 7-8 Total:** ₹12,000 + $27

## Month 9-10: CI/CD & Linux

| Week | Platform | Action | Cost |
|------|----------|--------|------|
| 21-24 | GCP | Cloud Build heavy | ₹15,000 |
| 21-24 | Azure | DevOps pipelines | $25 |
| 21-24 | DO | Yocto builds | $12 |

**Month 9-10 Total:** ₹15,000 + $37

## Month 11-12: Finalize & Export

| Week | Platform | Action | Cost |
|------|----------|--------|------|
| 25-28 | GCP | Final builds, download | ₹25,000 |
| 25-28 | Azure | Final testing | $26 |
| 25-28 | DO | Archive everything | $10 |

**Month 11-12 Total:** ₹25,000 + $36

---

# 📦 Complete Download Checklist (Before Expiry)

## GCP Downloads

```bash
# 1. ARM toolchain
gcloud compute scp arm-build-server:/opt/arm-gcc-12.2 ~/backup/toolchains/

# 2. Yocto state cache (MOST IMPORTANT - saves weeks of rebuild time)
gsutil -m cp -r gs://your-bucket/sstate-cache ~/backup/yocto/

# 3. Yocto downloads
gsutil -m cp -r gs://your-bucket/downloads ~/backup/yocto/

# 4. All Docker images
docker pull gcr.io/your-project/arm-gcc:12.2
docker save gcr.io/your-project/arm-gcc:12.2 > ~/backup/docker/arm-gcc.tar

# 5. TinyML models
gsutil cp gs://your-bucket/models/*.tflite ~/backup/tinyml/

# 6. CI/CD configs (should already be in GitHub)
git clone https://github.com/your-username/embedded-firmware ~/backup/code/
```

## Azure Downloads

```bash
# 1. IoT Hub configurations
az iot hub show --name my-embedded-iot-hub > ~/backup/azure/iothub-config.json

# 2. Device identities
az iot hub device-identity list --hub-name my-embedded-iot-hub > ~/backup/azure/devices.json

# 3. DevOps pipeline YAMLs (should be in GitHub)
# Already version controlled
```

## DigitalOcean Downloads

```bash
# 1. Create droplet snapshot
doctl compute droplet-action snapshot embedded-build --snapshot-name final-backup

# 2. Download snapshot (if possible) or recreate from scripts
# Note: Snapshots stay in DO, but setup scripts should be in GitHub

# 3. Firmware from Spaces
s3cmd sync s3://my-firmware-bucket/ ~/backup/firmware/
```

---

# ✅ Final Credit Summary

| Platform | Total | Used | Remaining | Status |
|----------|-------|------|-----------|--------|
| **GCP** | ₹1,00,000 | ₹1,00,000 | ₹0 | ✅ 100% |
| **Azure** | $200 | $200 | $0 | ✅ 100% |
| **DO** | $100 | $100 | $0 | ✅ 100% |

**Zero waste. 100% embedded-focused. All permanent assets backed up.** 🎉
