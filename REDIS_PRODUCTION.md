# Redis Memory Configuration for Production

When deploying Redis in production environments, you should enable the memory overcommit setting to prevent potential issues with background saving and replication.

## The Warning

Redis may show this warning in logs:
```
WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition.
```

## Linux Production Deployment

For production deployments on Linux, you can:

### Option 1: Use the production Docker Compose override file
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Option 2: Configure the host system
Run these commands on the host system:
```bash
echo 'vm.overcommit_memory=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl vm.overcommit_memory=1
```

## Development Environments

For local development on macOS or Windows:
- The warning can be safely ignored
- Do not enable the `sysctls` configuration as it's not supported on these platforms
- The application will function normally despite the warning
