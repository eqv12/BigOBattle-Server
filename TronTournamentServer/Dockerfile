# Step 1: Start from a stable, common base operating system.
FROM ubuntu:22.04

# Set an environment variable to prevent installers from asking for user input.
ENV DEBIAN_FRONTEND=noninteractive

# Step 2: Update the package list and install all compilers, runtimes, and libraries.
RUN apt-get update && apt-get install -y \
    # Compilers
    build-essential \
    # Python
    python3 \
    pip \
    # Java
    openjdk-17-jdk \
    # C/C++ JSON Libraries (The New Additions)
    libjansson-dev \
    libjsoncpp-dev \
    # Other tools
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Install Node.js using the official NodeSource repository.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Step 3.5: Create the target directory and copy the local Java JSON library
RUN mkdir -p /usr/share/java
COPY json-20231013.jar /usr/share/java/json.jar

# Step 4: Set a working directory inside the container.
WORKDIR /usr/src/app