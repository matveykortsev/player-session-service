# Player session service report

A backend service which consumes events and provides metrics about players sessions.
Service uses Cassandra database, written on Python with Flask framework, in additional uses Redis for caching.

***

## How to run

### Requirements

* Install Docker
* Add assigment_data.jsonl in docker folder, data example: https://cdn.unityads.unity3d.com/assignments/assignment_data.jsonl.bz2

### Startup

```bash
# From root directory
cd docker
docker-compose up -d --build
# Wait until images build and all containers up and running. Note that cassandara initialization takes additional time.
# Copy example dataset in session_by_player_id table via dsbulk
docker exec -it cassandra /dsbulk-1.8.0/bin/dsbulk load -k test -t session_by_player_id -c json -url assignment_data.json --schema.allowMissingFields true
```

## The Assignment

* Service should be written in Python and use a Cassandra database. Use any framework and external libraries you see fit.
* The folder should be git initialised and follow standard git practices.
* Service should have the following REST APIs with a maximum latency of 500ms (90th
percentile):
  * To receive and store event batches (10 events/batch).
  * To fetch “start” sessions for the last X (X is defined by the user) hours for each country.
  * To fetch the last 20 completed sessions for a given specified player_id.
* Data older than 1 year, either received through API or already stored in the database, should
be discarded.


***
## API framework

Used Flask for fast API design. From the ground up, Flask was built with scalability and simplicity in mind.
Being lightweight, easy to adopt, well-documented, and popular, Flask is a very good option for developing RESTful APIs.
In addition I used Marshmallow framework for serializing and deserializing JSON objects.
Also I'm used Redis, to save the responses from the API, and then use those responses instead of making the requests to the server to fetch the data.

***

## API design

API requirements:
```
1) To receive and store event batches (10 events/batch)
2) To fetch “start” sessions for the last X (X is defined by the user) hours for each country.
3) To fetch the last 20 completed sessions for a given specified player_id.
```
* For requirement #1 use endpoint ```localhost:5001/event-handler```. 
  You have to specify JSON event which you want to put in database. Example:
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"event":"end","player_id":"player_1"}' http://127.0.0.1:5001/event-handler
  curl -X POST -H "Content-Type: application/json" -d '{"country":"US","event":"start","player_id":"player_2"}' http://127.0.0.1:5001/event-handler
  ```
  * Endpoint collect two types of events ```start``` and ```end```, wait until batch fully loaded with 10 events and then flush them to database.
  Depends on event type we insert it in different tables: For start events ```session_by_country``` and ```session_by_player_id``` tables, for ```end``` events ```session_by_player_id``` table.
  More about that in database model section.

* For requirement #2 use endpoint ```localhost:5001/by-country/<country>/<hours>```
  * Fetching ```start``` sessions for specified ```country``` and ```hours``` interval.
  Using Redis cache for store request answer for 50 seconds, query string using for store request in Redis.
  Note that you have to load additional data in ```session_by_country``` table.
  More about that in database model section 
* For requirement #3 use endpoint ```localhost:5001/by-player/<player_id>``` 
  * Fetching sessions for specified ```player_id``` where ```event=='end'```.
Using Redis cache for store request answer for 50 seconds, query string using for store request in Redis.
  

***

## Database model

Tables and load strategy.

### Tables

The API requires two separate tables to effectively query the data with Cassandra database. However, the data comes in two different events at different times which adds some complexity to the model and processing.
In case we use one table for both types of events we can process sessions for #2 requirement via pythons but its effects performance.

The two tables are designed to fit the search queries. Old data expired by setting TTL for the tables to satisfy the condition.

```sql
// Last sessions started by country
CREATE TABLE test.session_by_country (
    player_id text,
    ts timestamp,
    country text,
    event text,
    session_id uuid,
    PRIMARY KEY (country, ts)
) WITH CLUSTERING ORDER BY (ts DESC) AND default_time_to_live=31557600;
                       

// Session events by player. Used to search for complete player sessions.
CREATE TABLE test.session_by_player_id (
    player_id text,
    ts timestamp,
    country text,
    event text,
    session_id uuid,
    PRIMARY KEY (player_id, ts)
) WITH CLUSTERING ORDER BY (ts DESC) AND default_time_to_live = 31557600;

```
Used dsbulk for fast restoring data from example dataset to Cassandra.
Also using prepared Cassandra queries for more efficient query. 
***

## Things to do

* Improve exception handling
* Improve rest input validation
* Add more robust data quality validation
* Timestamp handling with full event precision
* Add unit- and integration -tests to get proper test coverage
* Performance testing with real Cassandra cluster
