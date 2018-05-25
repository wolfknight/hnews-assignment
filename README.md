**Running**

To run the server simply run `./infra/assignment.sh start`
This command will start a docker-compose cluster with 2 containers, one for the server and one for the db.

To stop the server simply run `./infra/assignment.sh stop`

**Tech-stack**

BottlePy is a quick and lightweight framework for APIs. The server can be replaced with CherryPy or Paste for a stable multi-threaded production application.
SQLlite3 is great for prototyping and testing, this will be replaced with a Dockerized SQL server like Postgres for production.
Pytest runs automated tests quickly.