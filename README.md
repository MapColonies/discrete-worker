# **Discrete-Worker**

Discrete-Worker creates a directory with tiles (using [gda2ltiles](https://gdal.org/programs/gdal2tiles.html) utility) based on a specific zoom level from an input resource.

# Run as localhost

generate config file
* `python3 confd/generate-config.py  --environment production`

set PYTHONPATH env into current repository - python will look for custom modules in the application directory.
* `export PYTHONPATH=.`
* `python3 src/main.py`

- **Note**: if you'd like to test the app, make sure no instances are running - only one instance can consume data from *Kafka Topic* (unless it has more than one partition).
  
# Run in Docker

* Build image:

  `docker build -t discrete-worker:<tag> .`

* Run the docker:
  
  `docker run discrete-worker:latest`

## Environment Variables:

List of environment variables.