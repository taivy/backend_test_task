import logging
import sys
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError

import requests

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


DayRange = namedtuple(
    'DayRange', [
        'day_string', 'day_start_string', 'day_end_string'])
# records - dict (employees names keys and spent time in hrs values)
Project = namedtuple('Project', ['name', 'records'])
# employees - list of employees names
DataForSheet = namedtuple(
    'DataForSheet', [
        'day_range', 'projects', 'employees'])


API_REQUESTS_TIMEOUT = 60
# user api object field to use as user idenifier (may change to email for
# example)
USER_IDENTIFIER = "name"


class IncorrectStatusCodeException(Exception):
    pass


def catch_api_exceptions():
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except requests.exceptions.Timeout:
                logging.error("Request to API failed: timeout")
            except requests.exceptions.ConnectionError as err:
                logging.error(
                    "Request to API failed: connection error %s", err)
            except requests.exceptions.HTTPError as err:
                logging.error("Request to API failed: error %s", err)
            except IncorrectStatusCodeException as err:
                logging.error(
                    "Request to API failed: incorrect status code %s", err)
            except JSONDecodeError as err:
                logging.error(
                    "Request to API failed: json decode error %s", err)

        return applicator
    return decorate


def get_day_range(day):
    # going to assume that the timezone where script runs is the timezone that is considered "primary" for
    # calculating dates in organization (if not/it's changed, may use pytz
    # library)

    day_string = day.strftime("%Y-%m-%d")
    day_start_string = day_string + "T00:00:00"
    day_end_string = day_string + "T23:59:59"

    return DayRange(day_string, day_start_string, day_end_string)


@catch_api_exceptions('')
def get_activities_from_api(organization_id: str, api_token: str,
                            start_datetime: str, end_datetime: str,
                            api_base_url: str = "https://api.hubstaff.com/v2",
                            ):
    response = requests.get(f"{api_base_url}/organizations/{organization_id}/activities", headers={
        "Authorization": f"Bearer {api_token}"
    }, params={
        "time_slot[start]": start_datetime,
        "time_slot[stop]": end_datetime
    }, timeout=API_REQUESTS_TIMEOUT)

    if response.status_code != 200:
        status_code = response.status_code
        raise IncorrectStatusCodeException(
            f"Incorrect status code {status_code}, expected 200")

    data = response.json()

    return data.get("activities", [])


@catch_api_exceptions('')
def get_employee_name_by_id(api_token: str,
                            employee_id: str,
                            api_base_url: str = "https://api.hubstaff.com/v2",
                            ):
    response = requests.get(f"{api_base_url}/users/{employee_id}", headers={
        "Authorization": f"Bearer {api_token}"
    }, timeout=API_REQUESTS_TIMEOUT)

    if response.status_code != 200:
        status_code = response.status_code
        raise IncorrectStatusCodeException(
            f"Incorrect status code {status_code}, expected 200")

    data = response.json()
    if not data.get("user"):
        return

    return data["user"].get(USER_IDENTIFIER)


@catch_api_exceptions('')
def get_project_name_by_id(api_token: str,
                           project_id: str,
                           api_base_url: str = "https://api.hubstaff.com/v2",
                           ):
    response = requests.get(f"{api_base_url}/projects/{project_id}", headers={
        "Authorization": f"Bearer {api_token}"
    }, timeout=API_REQUESTS_TIMEOUT)

    if response.status_code != 200:
        status_code = response.status_code
        raise IncorrectStatusCodeException(
            f"Incorrect status code {status_code}, expected 200")

    data = response.json()
    if not data.get("project"):
        return

    return data["project"].get("name")


def get_employee_id_to_name_dict(api_token: str,
                                 employees_ids,
                                 ):
    employee_id_to_name_dict = defaultdict(str)
    for employee_id in employees_ids:
        employee_id_to_name_dict[employee_id] = get_employee_name_by_id(
            api_token, employee_id)
    return employee_id_to_name_dict


def get_project_id_to_name_dict(api_token: str,
                                projects_ids,
                                ):
    project_id_to_name_dict = defaultdict(str)
    for project_id in projects_ids:
        project_id_to_name_dict[project_id] = get_project_name_by_id(
            api_token, project_id)
    return project_id_to_name_dict


def get_employees(employee_id_to_name_dict):
    employees = list(employee_id_to_name_dict.values())
    return employees


def get_projects(activities_data, project_id_to_name_dict,
                 employee_id_to_name_dict):
    projects_ids_to_records_dict = defaultdict(dict)
    for activity in activities_data:
        project_id = activity["project_id"]
        employee_name = employee_id_to_name_dict.get(activity["user_id"])
        if not projects_ids_to_records_dict[project_id].get(employee_name):
            projects_ids_to_records_dict[project_id][employee_name] = 0
        projects_ids_to_records_dict[project_id][employee_name] += activity["tracked"]
    projects = []
    for project_id, records_dict in projects_ids_to_records_dict.items():
        project_name = project_id_to_name_dict.get(project_id)
        projects.append(Project(project_name, records_dict))
    return projects


def transform_activities_data(activities):
    # filter and turn tracked time to hrs from settings
    transformed_activities = []
    for activity in activities:
        if not activity.get("tracked"):
            return
        mins = round(activity["tracked"] / 60)
        hrs = round(mins / 60, 2)
        transformed_activities.append({
            "project_id": activity["project_id"],
            "user_id": activity["user_id"],
            "tracked": hrs
        })
    return transformed_activities


def get_employees_and_projects(config, activities_data_transformed):
    employees_ids = list(set([activity["user_id"]
                         for activity in activities_data_transformed]))
    projects_ids = list(set([activity["project_id"]
                        for activity in activities_data_transformed]))

    employee_id_to_name_dict = get_employee_id_to_name_dict(api_token=config["api"]["api_token"],
                                                            employees_ids=employees_ids,
                                                            )
    project_id_to_name_dict = get_project_id_to_name_dict(api_token=config["api"]["api_token"],
                                                          projects_ids=projects_ids,
                                                          )

    employees = get_employees(employee_id_to_name_dict)
    projects = get_projects(
        activities_data_transformed,
        project_id_to_name_dict,
        employee_id_to_name_dict)
    return employees, projects


def get_data_for_sheet(config):
    day = datetime.today() - timedelta(days=1)
    if config["sheet"].get("date"):
        try:
            day = datetime.strptime(config["sheet"]["date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            logging.info(
                "Incorrect date in config: %s, using yesterday",
                config["sheet"]["date"])

    day_range = get_day_range(day)
    activities_data = get_activities_from_api(organization_id=config["api"]["organization_id"],
                                              api_token=config["api"]["api_token"],
                                              start_datetime=day_range.day_start_string,
                                              end_datetime=day_range.day_end_string,
                                              )
    if not activities_data:
        logging.error("Couldn't get activities data, exiting")
        return

    activities_data_transformed = transform_activities_data(activities_data)
    employees, projects = get_employees_and_projects(
        config, activities_data_transformed)
    if not employees or not projects:
        logging.error("Couldn't get employees or projects data, exiting")
        return

    return DataForSheet(day_range, projects, employees)
