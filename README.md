**Overview**

The current version only contains a PoC of step 1 including creating a post and listing posts.
In addition there are 2 sanity system tests, and the whole thing is running in Docker. 

**Running**

To run the tests simply run the script `./infra/run-tests.sh`

**Tech-stack**

BottlePy is a quick and lightweight framework for APIs. The server can be replaced with CherryPy or Paste for a stable multi-threaded production application.
SQLlite3 is great for prototyping and testing, this will be replaced with a Dockerized SQL server like Postgres for production.
Pytest runs automated tests quickly.