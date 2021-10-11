# Task description

Imagine you are a member of a test organization. Implement a program that will retrieve information from the hubstaff V1 API about the time that each employee of the organization spent working on each project. Present the aggregated information in an HTML table.

In the columns, there should be the employees, in the rows, there should be the projects, and in the cells in the middle, there should be the amount of time that a given employee spent working on a given project. The program should only output the projects that were worked on, and the employees who worked on a given day. The program will be run as a daily cron job and the cron wrapper script will redirect standard output to a file.

The table should always be rendered for one day, which by default is yesterday. The configuration (such as the API key) should be read from a config file. A future extension may be for the program to send the table to a manager via email.

It should be possible for a sysadmin to deploy the program on a server without reading its code or running any API queries manually.


# Installation

Recommended Python version: 3.8

```
pip install -r requirements.txt
```


# Configuration

Configuration file is config.ini in the root of project


# Run

Run file main.py. It should redirect results (html with sheet or error message) to standard output
