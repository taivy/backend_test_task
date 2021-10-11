import logging
import pathlib
import sys

import jinja2


logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def get_jinja_template(templates_dir: str = "templates",
                       template_name: str = "sheet.jinja"):
    directory_of_this_file = pathlib.Path(__file__).parent.resolve()
    templates_directory = directory_of_this_file / templates_dir
    if not templates_directory.is_dir():
        logging.error(
            "Template directory does not exist at path %s",
            templates_directory.resolve())
        return
    template_path = templates_directory / template_name
    if not template_path.is_file():
        logging.error(
            "Template does not exist at path %s",
            template_path.resolve())
        return

    loader = jinja2.FileSystemLoader(templates_directory)
    env = jinja2.Environment(loader=loader)
    template = env.get_template(template_name)
    return template


def get_sheet_html_string(data) -> str:
    template = get_jinja_template()
    html_string = "<b>Couldn't get rendering template. See logs for more info</b>"
    if template:
        try:
            html_string = template.render(date_string=data.day_range.day_string,
                                          projects=data.projects,
                                          employees=data.employees)
        except jinja2.TemplateError as err:
            logging.error("Error while rendering Jinja template: %s", err)
            html_string = "<b>Error occured while rendering template. See logs for more info</b>"
    return html_string


def output_sheet(sheet_html_string):
    # may change the implementation in the future: e.g. output to email message or a file
    # now just output to stdout
    print(sheet_html_string)
